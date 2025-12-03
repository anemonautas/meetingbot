import os
import time
import threading
import subprocess
import signal
import shutil

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from libot.logger import logger
from libot.config import OUTPUT_DIR, DISPLAY_NUM, EXIT_ON_FINISH
from libot.js_scripts import CHECK_TEXT_PRESENCE_JS, FIND_AND_CLICK_JS
from libot.audio import get_monitor_source, force_audio_routing
from libot.avatar import ensure_avatar_y4m
from libot.browser import take_screenshot, safe_click
from libot.meeting import join_meeting
from libot.gcs import upload_recordings_to_gcs
from libot.gemini import gemini_transcription
from libot.compress import compress_audio

def _wait_dom_ready(driver, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            state = driver.execute_script("return document.readyState")
            if state == "complete":
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def record_task(meeting_url, max_duration, task_id, record_audio=True, record_video=True):
    logger.info(f"[{task_id}] Iniciando proceso de grabación...")
    task_dir = os.path.join(OUTPUT_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)
    logger.debug(f"[{task_id}] Directorio de grabación: {task_dir}")

    output_video = os.path.join(task_dir, "recording.mp4")
    logger.debug(f"[{task_id}] Archivo de video: {output_video}")

    output_audio = os.path.join(task_dir, "audio.wav")       # siempre que record_audio sea True
    compressed_audio = os.path.join(task_dir, "audio.mp3")
    logger.debug(f"[{task_id}] Archivo de audio: {output_audio}")

    ffmpeg_video_log = os.path.join(task_dir, "ffmpeg_video.log")
    logger.debug(f"[{task_id}] Archivo de log de video: {ffmpeg_video_log}")

    ffmpeg_audio_log = os.path.join(task_dir, "ffmpeg_audio.log")
    logger.debug(f"[{task_id}] Archivo de log de audio: {ffmpeg_audio_log}")

    audio_source = get_monitor_source()
    logger.debug(f"[{task_id}] Fuente de audio: {audio_source}")

    avatar_y4m = ensure_avatar_y4m()

    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/google-chrome"  # explicit, given your Dockerfile

    chrome_options.add_argument("--headless=new")              # important

    chrome_options.add_argument(f"--user-data-dir=/tmp/profile_{task_id}")
    chrome_options.add_argument("--disable-features=AudioServiceOutOfProcess")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    chrome_options.add_argument("--use-fake-device-for-media-stream")
    chrome_options.add_argument("--use-fake-ui-for-media-stream")

    if avatar_y4m:
        chrome_options.add_argument(f"--use-file-for-fake-video-capture={avatar_y4m}")

    logger.debug(f"[{task_id}] Opciones de Chrome: {chrome_options}")

    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    ffmpeg_video_process = None
    ffmpeg_audio_process = None

    stop_audio_enforcer = threading.Event()

    try:
        logger.info(f"[{task_id}] Lanzando Chrome...")

        logger.info(f"[{task_id}] Driver de Chrome: {driver}")

        logger.info(f"[{task_id}] Abriendo URL de reunión: {meeting_url}")
        driver.get(meeting_url)
        _wait_dom_ready(driver, timeout=30)

        # 1) Intentar unirse a la reunión
        if not join_meeting(driver, task_id):
            logger.error(f"[{task_id}] Abortando: no se pudo unir a la reunión.")
            driver.quit()
            stop_audio_enforcer.set()
            if ffmpeg_audio_process:
                ffmpeg_audio_process.terminate()
            if ffmpeg_video_process:
                ffmpeg_video_process.terminate()
            return

        # 2) Limpiar tooltips genéricos dentro de la reunión
        time.sleep(2)
        for _ in range(3):
            logger.debug(f"[{task_id}] Intentando limpiar tooltips...")
            if not safe_click(driver, "button", ["Dismiss", "Got it", "Close", "Cerrar"], task_id):
                break
            time.sleep(1)

        # 3) Hilo para forzar routing de audio
        logger.debug(f"[{task_id}] Iniciando hilo para forzar routing de audio...")
        t_ae = threading.Thread(target=force_audio_routing, args=(task_id, stop_audio_enforcer))
        t_ae.daemon = True
        t_ae.start()
        logger.debug(f"[{task_id}] Hilo para forzar routing de audio iniciado: {t_ae}")
        
        # 4) Lanzar ffmpeg
        logger.info(f"[{task_id}] 🎥 Iniciando grabación (audio source: {audio_source})")
        ffmpeg_env = os.environ.copy()
        if record_audio:
            cmd_audio = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "pulse", "-ac", "2", "-thread_queue_size", "1024", "-i", audio_source,
                "-acodec", "pcm_s16le", "-ar", "48000",  # WAV 48kHz PCM
                output_audio,
            ]
            logger.debug(f"[{task_id}] Comando de ffmpeg para audio: {cmd_audio}")
            logger.info(f"[{task_id}] 🎙️ Iniciando grabación de audio en WAV desde: {audio_source}")
            with open(ffmpeg_audio_log, "w") as f_log_a:
                ffmpeg_audio_process = subprocess.Popen(
                    cmd_audio,
                    stdout=f_log_a,
                    stderr=subprocess.STDOUT,
                    env=ffmpeg_env,
                )
            logger.debug(f"[{task_id}] Proceso de ffmpeg para audio iniciado: {ffmpeg_audio_process}")
            time.sleep(1)
            if ffmpeg_audio_process.poll() is not None:
                logger.error(f"[{task_id}] ❌ ffmpeg AUDIO no arrancó. Ver {ffmpeg_audio_log}")
                raise RuntimeError("ffmpeg audio failed startup")

        # 6) Lanzar ffmpeg de VÍDEO (sólo vídeo, sin audio)
        if record_video:
            cmd_video = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "x11grab", "-video_size", "1920x1080", "-framerate", "30",
                "-thread_queue_size", "1024", "-i", DISPLAY_NUM,
                "-an",  # sin audio
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                output_video,
            ]
            logger.info(f"[{task_id}] 🎥 Iniciando grabación de vídeo (opcional).")
            with open(ffmpeg_video_log, "w") as f_log_v:
                ffmpeg_video_process = subprocess.Popen(
                    cmd_video,
                    stdout=f_log_v,
                    stderr=subprocess.STDOUT,
                    env=ffmpeg_env,
                )
            time.sleep(1)
            if ffmpeg_video_process.poll() is not None:
                logger.error(f"[{task_id}] ❌ ffmpeg VÍDEO no arrancó. Ver {ffmpeg_video_log}")
                # si el vídeo es opcional, puedes no hacer raise aquí:
                if record_video:
                    raise RuntimeError("ffmpeg video failed startup")

        # 5) Bucle de monitorización de la reunión
        start_time = time.time()
        controls_missing_count = 0
        exit_phrases = [
            "you were removed", "se le ha eliminado",
            "meeting ended", "finalizó la reunión",
            "thank you for attending",
        ]

        while (time.time() - start_time) < max_duration:
            # ffmpeg sigue vivo
            primary_proc = ffmpeg_audio_process if record_audio else ffmpeg_video_process

            if primary_proc is not None and primary_proc.poll() is not None:
                logger.error(f"[{task_id}] ❌ Proceso ffmpeg principal terminó inesperadamente.")
                break

            # (Opcional) log si el secundario muere
            if record_video and ffmpeg_video_process is not None and ffmpeg_video_process.poll() is not None:
                logger.warning(f"[{task_id}] ⚠️ Proceso de vídeo ha terminado, pero sigo grabando audio.")

            # Texto de fin de reunión
            try:
                found_phrase = driver.execute_script(CHECK_TEXT_PRESENCE_JS, exit_phrases)
            except Exception:
                found_phrase = None

            if found_phrase:
                logger.info(f"[{task_id}] 🛑 Detectado texto de salida: '{found_phrase}'")
                break

            # Heurística de controles visibles
            controls_visible = False
            check_terms = ["Raise", "Levantar", "Chat", "Leave", "Salir"]

            for text in check_terms:
                try:
                    if driver.execute_script(FIND_AND_CLICK_JS, [text], "button", False) == "found":
                        controls_visible = True
                        break
                except Exception:
                    pass

            if not controls_visible:
                try:
                    if driver.find_elements(By.ID, "hangup-button"):
                        controls_visible = True
                except Exception:
                    pass

            if controls_visible:
                controls_missing_count = 0
            else:
                controls_missing_count += 1

            if controls_missing_count >= 10:
                logger.warning(f"[{task_id}] 🛑 Controles ausentes ~20s. Terminando.")
                take_screenshot(driver, task_id, "controls_lost")
                break

            time.sleep(2)

        logger.info(f"[{task_id}] 🏁 Bucle de grabación terminado.")


    except Exception as e:
        logger.error(f"[{task_id}] Error crítico: {e}", exc_info=True)
        if driver:
            take_screenshot(driver, task_id, "critical_error")

    finally:
        logger.info(f"[{task_id}] 🏁 Finalizando grabación...")
        stop_audio_enforcer.set()
        logger.info(f"[{task_id}] 🏁 Audio enforcer detenido.")

        logger.info(f"[{task_id}] 🏁 Deteniendo procesos ffmpeg...")
        for proc_name, proc in [("AUDIO", ffmpeg_audio_process), ("VÍDEO", ffmpeg_video_process)]:
            if proc is not None and proc.poll() is None:
                logger.info(f"[{task_id}] Deteniendo ffmpeg {proc_name}...")
                try:
                    os.kill(proc.pid, signal.SIGTERM)
                except Exception:
                    pass
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        logger.info(f"[{task_id}] 🏁 Procesos ffmpeg detenidos.")

        if driver:
            try:
                driver.quit()
            except Exception:
                pass
            logger.info(f"[{task_id}] 🏁 Driver detenido.")

        profile_path = f"/tmp/profile_{task_id}"
        if os.path.exists(profile_path):
            try:
                shutil.rmtree(profile_path)
                logger.info(f"[{task_id}] 🏁 Profile eliminado.")
            except Exception:
                time.sleep(1)
                shutil.rmtree(profile_path, ignore_errors=True)
                logger.warning(f"[{task_id}] 🏁 No se pudo eliminar el profile limpiamente.")

        logger.info(f"[{task_id}] 🏁 Cleanup completado.")

        # 7) Upload sólo si existe el fichero
        if record_audio and os.path.exists(output_audio):

            logger.info(f"[{task_id}] 🎙️ Comprimiendo audio..." )
            compress_audio(output_audio, compressed_audio)
            logger.info(f"[{task_id}] 🎙️ Audio comprimido en {compressed_audio}")

            logger.info(f"[{task_id}] 🎙️ Subiendo audio a GCS...")
            upload_recordings_to_gcs(task_id, compressed_audio, "audio.mp3")
            logger.info(f"[{task_id}] 🎙️ Audio subido a GCS.")

            logger.info(f"[{task_id}] 🎙️ Transcribiendo audio con Gemini...")
            transcript = gemini_transcription(compressed_audio)
            logger.info(f"[{task_id}] 🎙️ Transcripción terminada.")

            logger.warning(f"[{task_id}] 🎙️ Transcripción: {transcript}")

        else:
            logger.warning(f"[{task_id}] No se encontró {output_audio}, no se sube nada.")
        
        if record_video and os.path.exists(output_video):
            upload_recordings_to_gcs(task_id, output_video, "video.mp4")
            logger.info(f"[{task_id}] 🎬 Video subido a GCS.")
        else:
            logger.warning(f"[{task_id}] No se encontró {output_video}, no se sube nada.")

        if EXIT_ON_FINISH:
            logger.info(f"[{task_id}] EXIT_ON_FINISH activo. Terminando proceso.")
            os._exit(0)
