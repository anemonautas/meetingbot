import os
import time
import threading
import subprocess
import signal
import shutil
import glob

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from libot.logger import logger
from libot.config import OUTPUT_DIR, DISPLAY_NUM, EXIT_ON_FINISH
from libot.js_scripts import CHECK_TEXT_PRESENCE_JS, FIND_AND_CLICK_JS
from libot.audio import get_monitor_source, force_audio_routing
from libot.avatar import ensure_avatar_y4m
from libot.browser import take_screenshot, safe_click, build_driver, _wait_dom_ready
from libot.meeting import join_meeting
from libot.gcs import upload_recordings_to_gcs
from libot.gemini import gemini_transcription
from libot.compress import compress_audio
from libot.briefing import handle_briefing

EXIT_PHRASES = [
    "you were removed",
    "se le ha eliminado",
    "meeting ended",
    "finalizó la reunión",
    "thank you for attending",
]


def process_audio_segment(task_id, wav_path, task_dir, segment_index):
    """
    Helper function to Compress -> Upload -> Transcribe a single completed segment.
    Designed to run in a thread.
    """
    try:
        base_name = os.path.splitext(os.path.basename(wav_path))[0]  # e.g., audio_000
        mp3_path = os.path.join(task_dir, base_name + ".mp3")
        remote_name = f"{base_name}.mp3"

        logger.info(f"  [{task_id}] 🎙️ [Seg {segment_index}] Compressing {wav_path}...")
        compress_audio(wav_path, mp3_path)

        if os.path.exists(mp3_path):
            logger.info(
                f"  [{task_id}] 🎙️ [Seg {segment_index}] Uploading {remote_name}..."
            )
            upload_recordings_to_gcs(task_id, mp3_path, remote_name)

            logger.info(
                f"  [{task_id}] 🎙️ [Seg {segment_index}] Transcribing with Gemini..."
            )
            transcript = gemini_transcription(mp3_path, task_id, segment_index)
            logger.warning(
                f"   [{task_id}] 🎙️ [Seg {segment_index}] Transcript result: {len(transcript)}"
            )

        else:
            logger.error(f" [{task_id}] ❌ Failed to compress segment {segment_index}")

    except Exception as e:
        logger.error(f" [{task_id}] ❌ Error processing segment {segment_index}: {e}")


def ffmpg_audio_process(audio_source, audio_pattern, ffmpeg_audio_log, segment_seconds):
    ffmpeg_env = os.environ.copy()

    cmd_audio = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "pulse",
        "-ac",
        "2",
        "-thread_queue_size",
        "1024",
        "-i",
        audio_source,
        "-acodec",
        "pcm_s16le",
        "-ar",
        "48000",
        "-f",
        "segment",
        "-segment_time",
        str(segment_seconds),
        "-reset_timestamps",
        "1",
        audio_pattern,
    ]
    with open(ffmpeg_audio_log, "w") as f_log_a:
        ffmpeg_audio_process = subprocess.Popen(
            cmd_audio, stdout=f_log_a, stderr=subprocess.STDOUT, env=ffmpeg_env
        )

    time.sleep(1)
    if ffmpeg_audio_process.poll() is not None:
        raise RuntimeError("ffmpeg audio failed startup")


def record_task(
    meeting_url,
    max_duration,
    task_id,
    record_audio=True,
    record_video=True,
    segment_seconds: int = 300,
):
    logger.info(f"[{task_id}] Starting recording process for \n{meeting_url}")
    task_dir = os.path.join(OUTPUT_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    output_video = os.path.join(task_dir, "recording.mp4")
    audio_pattern = os.path.join(task_dir, "audio_%03d.wav")

    ffmpeg_video_log = os.path.join(task_dir, "ffmpeg_video.log")
    ffmpeg_audio_log = os.path.join(task_dir, "ffmpeg_audio.log")

    audio_source = get_monitor_source()
    avatar_y4m = ensure_avatar_y4m()

    ffmpeg_video_process = None
    ffmpeg_audio_process = None
    stop_audio_enforcer = threading.Event()
    driver = None

    next_audio_index_to_process = 0
    processing_threads = []

    try:
        logger.info(f"[{task_id}] Lanzando Chrome...")
        driver = build_driver(task_id, avatar_y4m, task_dir)

        logger.info(f"[{task_id}] Abriendo URL de reunión: {meeting_url}")
        driver.get(meeting_url)
        take_screenshot(driver, task_id, "OPENING")
        _wait_dom_ready(driver, timeout=30)

        if not join_meeting(driver, task_id):
            logger.error(f"[{task_id}] Abortando: no se pudo unir a la reunión.")
            driver.quit()
            return

        time.sleep(2)
        for _ in range(3):
            if not safe_click(
                driver, "button", ["Dismiss", "Got it", "Close", "Cerrar"], task_id
            ):
                break
            time.sleep(1)

        t_ae = threading.Thread(
            target=force_audio_routing, args=(task_id, stop_audio_enforcer)
        )
        t_ae.daemon = True
        t_ae.start()

        ffmpeg_env = os.environ.copy()
        if record_audio:
            ffmpg_audio_process(
                audio_source, audio_pattern, ffmpeg_audio_log, segment_seconds
            )

        if record_video:
            cmd_video = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "x11grab",
                "-video_size",
                "1920x1080",
                "-framerate",
                "30",
                "-thread_queue_size",
                "1024",
                "-i",
                DISPLAY_NUM,
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                output_video,
            ]
            with open(ffmpeg_video_log, "w") as f_log_v:
                ffmpeg_video_process = subprocess.Popen(
                    cmd_video, stdout=f_log_v, stderr=subprocess.STDOUT, env=ffmpeg_env
                )

        start_time = time.time()
        controls_missing_count = 0

        while (time.time() - start_time) < max_duration:
            if record_audio:
                next_file_path = os.path.join(
                    task_dir, f"audio_{next_audio_index_to_process + 1:03d}.wav"
                )

                if os.path.exists(next_file_path):
                    ready_file_path = os.path.join(
                        task_dir, f"audio_{next_audio_index_to_process:03d}.wav"
                    )

                    logger.info(
                        f"[{task_id}] ⚡ Segmento completado detectado: {ready_file_path}"
                    )

                    t = threading.Thread(
                        target=process_audio_segment,
                        args=(
                            task_id,
                            ready_file_path,
                            task_dir,
                            next_audio_index_to_process,
                        ),
                    )
                    t.start()
                    processing_threads.append(t)
                    next_audio_index_to_process += 1

            primary_proc = (
                ffmpeg_audio_process if record_audio else ffmpeg_video_process
            )

            if primary_proc and primary_proc.poll() is not None:
                logger.error(
                    f"[{task_id}] ❌ Proceso ffmpeg principal terminó inesperadamente."
                )
                break

            try:
                found_phrase = driver.execute_script(
                    CHECK_TEXT_PRESENCE_JS, EXIT_PHRASES
                )
            except Exception:
                found_phrase = None

            if found_phrase:
                logger.info(
                    f"[{task_id}] 🛑 Detectado texto de salida: '{found_phrase}'"
                )
                break

            controls_visible = False
            check_terms = ["Raise", "Levantar", "Chat", "Leave", "Salir"]
            for text in check_terms:
                try:
                    if (
                        driver.execute_script(
                            FIND_AND_CLICK_JS, [text], "button", False
                        )
                        == "found"
                    ):
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
        logger.info(f"[{task_id}] 🏁 Finalizando grabación y limpiando...")
        stop_audio_enforcer.set()

        for proc in [ffmpeg_audio_process, ffmpeg_video_process]:
            if proc and proc.poll() is None:
                try:
                    os.kill(proc.pid, signal.SIGTERM)
                    proc.wait(timeout=5)
                except Exception:
                    proc.kill()

        if driver:
            try:
                driver.quit()
            except Exception:
                pass

        shutil.rmtree(f"/tmp/profile_{task_id}", ignore_errors=True)

        if record_audio:
            for t in processing_threads:
                if t.is_alive():
                    t.join(timeout=30)

            all_wavs = sorted(glob.glob(os.path.join(task_dir, "audio_*.wav")))

            for wav_path in all_wavs:
                try:
                    idx_str = os.path.splitext(os.path.basename(wav_path))[0].split(
                        "_"
                    )[1]
                    idx = int(idx_str)

                    if idx >= next_audio_index_to_process:
                        logger.info(
                            f"[{task_id}] 🏁 Procesando segmento final/restante: {wav_path}"
                        )
                        process_audio_segment(task_id, wav_path, task_dir, idx)

                    
                except Exception as e:
                    logger.warning(
                        f"[{task_id}] Error parsing filename {wav_path}: {e}"
                    )
                    
            handle_briefing(task_id)


        if record_video and os.path.exists(output_video):
            upload_recordings_to_gcs(task_id, output_video, "video.mp4")

        if EXIT_ON_FINISH:
            os._exit(0)
