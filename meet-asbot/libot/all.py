import os
import time
import subprocess
import threading
import uuid
import logging
import shutil
import signal
import sys
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from google.cloud import storage

# --- CONFIGURATION ---
AVATAR_IMAGE = os.environ.get("AVATAR_IMAGE", "/app/assets/avatar.png")
AVATAR_Y4M = os.environ.get("AVATAR_Y4M", "/app/assets/avatar.mp4")
AVATAR_RESOLUTION = os.environ.get("AVATAR_RESOLUTION", "1280x720")
AVATAR_DURATION = int(os.environ.get("AVATAR_DURATION", "600"))
EXIT_ON_FINISH = os.environ.get("EXIT_ON_FINISH", "0") == "1"

GCS_BUCKET = os.environ.get("GCS_BUCKET")
GCS_PREFIX = os.environ.get("GCS_PREFIX", "").rstrip("/")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/output")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- LOGGING ---
log_file_path = os.path.join(OUTPUT_DIR, "service.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file_path)
    ]
)
logger = logging.getLogger("RECORDER")

app = Flask(__name__)

# Virtual Display ID
DISPLAY_NUM = ":99"
os.environ["DISPLAY"] = DISPLAY_NUM

# --- GCS UPLOAD ---
def upload_recordings_to_gcs(task_id, video_path, audio_path):
    if not GCS_BUCKET: return
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        base = f"{GCS_PREFIX}/{task_id}" if GCS_PREFIX else task_id
        
        if video_path and os.path.exists(video_path):
            blob = bucket.blob(f"{base}/recording.mp4")
            blob.upload_from_filename(video_path)
            logger.info(f"Uploaded video: gs://{GCS_BUCKET}/{base}/recording.mp4")
            
        if audio_path and os.path.exists(audio_path):
            blob = bucket.blob(f"{base}/audio.wav")
            blob.upload_from_filename(audio_path)
            logger.info(f"Uploaded audio: gs://{GCS_BUCKET}/{base}/audio.wav")
    except Exception as e:
        logger.error(f"GCS Upload failed: {e}")

# --- TEXTS & JS ---
JOIN_BUTTON_TEXTS = ["Join now", "Unirse ahora", "Rejoindre maintenant", "Jetzt teilnehmen"]
NO_AUDIO_TEXTS = ["Continue without audio or video", "Continue without audio", "No usar audio", "Continuar sin audio"]
COMPUTER_AUDIO_TEXTS = ["Computer audio", "Audio del equipo", "Audio de l'ordinateur", "Computeraudio", "System audio"]
NAME_PLACEHOLDERS = ["name", "nombre", "nom", "Name", "type your name", "escriba su nombre"] 
EXIT_PHRASES = ["you were removed", "se le ha eliminado", "meeting ended", "finalizó la reunión", "thank you for attending"]

FIND_AND_CLICK_JS = """
    var searchTextOptions = arguments[0];
    var tag = arguments[1];
    var doClick = arguments[2];
    function searchInDocument(doc) {
        var elements = doc.querySelectorAll(tag);
        for (var i = 0; i < elements.length; i++) {
            var el = elements[i];
            var text = (el.innerText || el.textContent || "").toLowerCase().trim();
            var aria = (el.getAttribute('aria-label') || "").toLowerCase();
            for (var j = 0; j < searchTextOptions.length; j++) {
                var opt = searchTextOptions[j].toLowerCase();
                if (text === opt || text.includes(opt) || aria === opt || aria.includes(opt)) {
                    if (el.offsetParent !== null) return el;
                }
            }
        }
        var iframes = doc.querySelectorAll('iframe');
        for (var i = 0; i < iframes.length; i++) {
            try {
                var innerDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                if (innerDoc) {
                    var result = searchInDocument(innerDoc);
                    if (result) return result;
                }
            } catch(e) {}
        }
        return null;
    }
    var found = searchInDocument(document);
    if (found) {
        if (doClick) { found.click(); return "clicked"; }
        return "found";
    }
    return null;
"""

FILL_INPUT_JS = """
    var value = arguments[0];
    var searchTerms = arguments[1];
    function searchInput(doc) {
        var inputs = doc.querySelectorAll("input");
        for (var i = 0; i < inputs.length; i++) {
            var el = inputs[i];
            var placeholder = (el.placeholder || "").toLowerCase();
            var aria = (el.getAttribute('aria-label') || "").toLowerCase();
            var match = searchTerms.some(term => placeholder.includes(term) || aria.includes(term));
            if (match) {
                el.focus();
                el.value = value;
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                nativeInputValueSetter.call(el, value);
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
                return true;
            }
        }
        var iframes = doc.querySelectorAll('iframe');
        for (var i = 0; i < iframes.length; i++) {
            try {
                var innerDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                if (innerDoc && searchInput(innerDoc)) return true;
            } catch(e) {}
        }
        return false;
    }
    return searchInput(document);
"""

CHECK_TEXT_PRESENCE_JS = """
    var searchPhrases = arguments[0];
    function searchInDocument(doc) {
        var bodyText = (doc.body.innerText || "").toLowerCase();
        for (var i = 0; i < searchPhrases.length; i++) {
            if (bodyText.includes(searchPhrases[i].toLowerCase())) {
                return searchPhrases[i];
            }
        }
        var iframes = doc.querySelectorAll('iframe');
        for (var i = 0; i < iframes.length; i++) {
            try {
                var innerDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                if (innerDoc) {
                    var found = searchInDocument(innerDoc);
                    if (found) return found;
                }
            } catch(e) {}
        }
        return null;
    }
    return searchInDocument(document);
"""

def run_cmd(command):
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# --- AUDIO SETUP ROBUSTO ---

def get_active_audio_source():
    """
    Busca el nombre exacto de la fuente de monitorización.
    Intenta encontrar 'VirtualSpeaker.monitor', si no, devuelve el primero que encuentre.
    """
    try:
        # Esperamos hasta 5 segundos a que aparezca VirtualSpeaker
        for _ in range(5):
            out = subprocess.run(["pactl", "list", "sources", "short"], capture_output=True, text=True).stdout
            if "VirtualSpeaker.monitor" in out:
                return "VirtualSpeaker.monitor"
            time.sleep(1)
        
        # Si no lo encontramos explícitamente, buscamos cualquier .monitor
        out = subprocess.run(["pactl", "list", "sources", "short"], capture_output=True, text=True).stdout
        for line in out.split('\n'):
            parts = line.split()
            if len(parts) > 1 and "monitor" in parts[1]:
                logger.warning(f"⚠️ VirtualSpeaker.monitor no encontrado. Usando fallback: {parts[1]}")
                return parts[1]
                
        # Último recurso
        return "0" 
    except:
        return "VirtualSpeaker.monitor"

def setup_audio_system_robust():
    """
    Solo verifica que el entrypoint hizo su trabajo.
    """
    logger.info("🔧 Verificando audio...")
    
    # Intentar encontrar VirtualSpeaker.monitor
    for _ in range(5):
        try:
            out = subprocess.run(["pactl", "list", "sources", "short"], capture_output=True, text=True).stdout
            if "VirtualSpeaker.monitor" in out:
                logger.info("✅ Audio OK: VirtualSpeaker.monitor encontrado.")
                return "VirtualSpeaker.monitor"
        except: pass
        time.sleep(1)

    # Si llegamos aquí, algo falló, pero devolvemos '0' (default) para intentar grabar igual
    logger.warning("⚠️ VirtualSpeaker.monitor no encontrado. Usando default '0'.")
    return "0"

def ensure_avatar_y4m():
    if AVATAR_Y4M and os.path.exists(AVATAR_Y4M): return AVATAR_Y4M
    if AVATAR_IMAGE and os.path.exists(AVATAR_IMAGE):
        try:
            logger.info(f"🎨 Generating avatar video from {AVATAR_IMAGE}")
            width, height = AVATAR_RESOLUTION.split("x")
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", AVATAR_IMAGE, "-t", str(AVATAR_DURATION),
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-pix_fmt", "yuv420p", AVATAR_Y4M
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return AVATAR_Y4M
        except: pass
    return None

def force_audio_routing(task_id, stop_event):
    logger.info(f"[{task_id}] 👮 Audio Enforcer started.")
    while not stop_event.is_set():
        try:
            result = subprocess.run(["pactl", "list", "sink-inputs", "short"], capture_output=True, text=True)
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) > 0:
                        stream_id = parts[0]
                        subprocess.run(["pactl", "move-sink-input", stream_id, "VirtualSpeaker"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        subprocess.run(["pactl", "set-sink-input-mute", stream_id, "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        subprocess.run(["pactl", "set-sink-input-volume", stream_id, "100%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass
        time.sleep(3)

def take_screenshot(driver, task_id, name):
    try: driver.save_screenshot(os.path.join(OUTPUT_DIR, task_id, f"{name}.png"))
    except: pass
    try: 
        with open(os.path.join(OUTPUT_DIR, task_id, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    except: pass

def safe_click(driver, tag, text_options, task_id):
    if isinstance(text_options, str): text_options = [text_options]
    try:
        res = driver.execute_script(FIND_AND_CLICK_JS, text_options, tag, True)
        if res == "clicked":
            logger.info(f"[{task_id}] 🖱️  CLICK: <{tag}> matching {text_options}")
            return True
        return False
    except: return False

def native_type_fallback(driver, task_id, bot_name):
    try:
        inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
        for inp in inputs:
            if inp.is_displayed():
                inp.click(); inp.clear(); inp.send_keys(bot_name)
                return True
    except: pass
    return False

# --- LOGIC ---

def join_meeting(driver, task_id):
    max_attempts = 20
    bot_name = "elmy Recorder"
    logger.info(f"[{task_id}] 🚀 Attempting to join meeting...")
    
    for i in range(max_attempts):
        if "login.microsoft" in driver.current_url:
            logger.error(f"[{task_id}] ⛔ Login Wall detected.")
            take_screenshot(driver, task_id, "wall_error")
            return False

        if safe_click(driver, "button", ["Continue on this browser", "Continuar en este explorador", "Continuer sur ce navigateur"], task_id):
            time.sleep(3); continue

        driver.execute_script(FILL_INPUT_JS, bot_name, NAME_PLACEHOLDERS)
        if i % 4 == 0: native_type_fallback(driver, task_id, bot_name)

        if safe_click(driver, "div", COMPUTER_AUDIO_TEXTS, task_id) or \
           safe_click(driver, "button", COMPUTER_AUDIO_TEXTS, task_id) or \
           safe_click(driver, "label", COMPUTER_AUDIO_TEXTS, task_id):
            time.sleep(1)

        if safe_click(driver, "button", JOIN_BUTTON_TEXTS, task_id):
            logger.info(f"[{task_id}] 🤞 Clicked Join...")
            take_screenshot(driver, task_id, "joining_attempt")
            time.sleep(5)

        in_meeting_texts = ["Raise", "Levantar", "Chat", "React", "Reaccionar", "Leave", "Salir"]
        is_in = False
        for text in in_meeting_texts:
            if driver.execute_script(FIND_AND_CLICK_JS, [text], "button", False) == "found":
                is_in = True; break
        
        if not is_in:
            try:
                if len(driver.find_elements(By.ID, "hangup-button")) > 0: is_in = True
            except: pass

        if is_in:
            logger.info(f"[{task_id}] ✅ Successfully joined!")
            take_screenshot(driver, task_id, "success_joined")
            return True

        time.sleep(2)

    logger.error(f"[{task_id}] ❌ Failed to join.")
    take_screenshot(driver, task_id, "fail_join")
    return False

def record_task(meeting_url, max_duration, task_id):
    task_dir = os.path.join(OUTPUT_DIR, task_id)
    if not os.path.exists(task_dir): os.makedirs(task_dir)
    
    output_video = os.path.join(task_dir, "recording.mp4")
    output_audio = os.path.join(task_dir, "audio.wav")
    ffmpeg_log = os.path.join(task_dir, "ffmpeg.log")
    
    # 1. Setup y obtención del nombre REAL de la fuente
    audio_source_name = setup_audio_system_robust()
    if not audio_source_name:
        logger.error(f"[{task_id}] Audio system failed. Aborting.")
        return

    avatar_y4m = ensure_avatar_y4m()

    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir=/tmp/profile_{task_id}")
    chrome_options.add_argument("--disable-features=AudioServiceOutOfProcess")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
    chrome_options.add_argument("--lang=en-US")
    
    if avatar_y4m: chrome_options.add_argument(f"--use-file-for-fake-video-capture={avatar_y4m}")
    else: chrome_options.add_argument("--use-fake-device-for-media-stream")
    chrome_options.add_argument("--use-fake-ui-for-media-stream")

    service = Service()
    driver = None
    ffmpeg_process = None
    stop_audio_enforcer = threading.Event()

    try:
        logger.info(f"[{task_id}] Launching Chrome...")
        env = os.environ.copy()
        env["PULSE_SERVER"] = "unix:/var/run/pulse/native" 
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(meeting_url)
        time.sleep(5)
        
        if join_meeting(driver, task_id):
            time.sleep(2)
            safe_click(driver, "button", ["Dismiss", "Got it", "Cerrar"], task_id)

            t_ae = threading.Thread(target=force_audio_routing, args=(task_id, stop_audio_enforcer))
            t_ae.daemon = True
            t_ae.start()

            logger.info(f"[{task_id}] 🎥 Starting FFmpeg using audio source: {audio_source_name}")
            
            ffmpeg_env = os.environ.copy()
            ffmpeg_env["DISPLAY"] = DISPLAY_NUM
            ffmpeg_env["PULSE_SERVER"] = "unix:/var/run/pulse/native"

            # FIX: Usamos el nombre detectado dinámicamente
            cmd_video = [
                "ffmpeg", "-y", 
                "-f", "x11grab", "-video_size", "1920x1080", "-framerate", "30", "-thread_queue_size", "1024", "-i", DISPLAY_NUM,
                "-f", "pulse", "-ac", "2", "-thread_queue_size", "1024", "-i", audio_source_name,
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", 
                "-c:a", "aac", "-b:a", "128k", 
                output_video
            ]
            
            with open(ffmpeg_log, "w") as f_log:
                ffmpeg_process = subprocess.Popen(cmd_video, stdout=f_log, stderr=subprocess.STDOUT, env=ffmpeg_env)
            
            time.sleep(3) # Un poco más de margen
            
            start_time = time.time()
            controls_missing_count = 0
            
            while (time.time() - start_time) < max_duration:
                if ffmpeg_process.poll() is not None:
                    logger.error(f"[{task_id}] ❌ FFmpeg CRASHED immediately!")
                    try:
                        with open(ffmpeg_log, "r") as f:
                            last_lines = f.readlines()[-10:]
                            logger.error("LOG: " + "".join(last_lines))
                    except: pass
                    break

                found_phrase = driver.execute_script(CHECK_TEXT_PRESENCE_JS, EXIT_PHRASES)
                if found_phrase:
                    logger.info(f"[{task_id}] 🛑 Meeting ended ('{found_phrase}')")
                    break

                controls_visible = False
                in_meeting_texts = ["Raise", "Levantar", "Chat", "Leave", "Salir"]
                for text in in_meeting_texts:
                    if driver.execute_script(FIND_AND_CLICK_JS, [text], "button", False) == "found":
                        controls_visible = True; break
                if not controls_visible:
                    try:
                        if len(driver.find_elements(By.ID, "hangup-button")) > 0: controls_visible = True
                    except: pass
                
                if controls_visible: controls_missing_count = 0
                else: controls_missing_count += 1
                
                if controls_missing_count >= 20: 
                    logger.info(f"[{task_id}] 🛑 Controls lost")
                    take_screenshot(driver, task_id, "controls_lost")
                    break
                
                time.sleep(1.5)

            logger.info(f"[{task_id}] 🏁 Recording finished.")

        else:
            logger.error(f"[{task_id}] Failed to join meeting.")
            take_screenshot(driver, task_id, "failed_to_join")

    except Exception as e:
        logger.error(f"[{task_id}] Critical: {e}", exc_info=True)
        if driver: take_screenshot(driver, task_id, "critical_error")
    finally:
        stop_audio_enforcer.set()
        if ffmpeg_process and ffmpeg_process.poll() is None:
            os.kill(ffmpeg_process.pid, signal.SIGTERM)
            try: ffmpeg_process.wait(timeout=5)
            except: ffmpeg_process.kill()
        
        if driver: driver.quit()
        path = f"/tmp/profile_{task_id}"
        if os.path.exists(path): shutil.rmtree(path, ignore_errors=True)

        upload_recordings_to_gcs(task_id, output_video, output_audio)

        if EXIT_ON_FINISH: os._exit(0)

@app.route("/", methods=["POST"])
def trigger_bot():
    data = request.get_json()
    task_id = str(uuid.uuid4())[:8]
    t = threading.Thread(target=record_task, args=(data.get("url"), int(data.get("duration", 3600)), task_id))
    t.daemon = True
    t.start()
    return jsonify({"status": "started", "task_id": task_id}), 202

if __name__ == "__main__":
    if os.path.exists(f"/tmp/.X{DISPLAY_NUM.replace(':','')}-lock"):
        os.remove(f"/tmp/.X{DISPLAY_NUM.replace(':','')}-lock")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    