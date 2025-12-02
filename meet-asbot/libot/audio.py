import subprocess
import time
from .logger import logger

# --- AUDIO SETUP ---

def get_monitor_source():
    """
    Identifies the correct PulseAudio monitor source for recording.
    Prioritizes 'VirtualSpeaker.monitor'.
    """
    logger.info("🔧 Detecting Audio Source...")
    
    # 1. Try to find the specific monitor for the VirtualSpeaker sink
    for _ in range(5):
        try:
            # pactl list sources short returns: ID Name Module ...
            result = subprocess.run(["pactl", "list", "sources", "short"], capture_output=True, text=True)
            if "VirtualSpeaker.monitor" in result.stdout:
                logger.info("✅ Audio Source Found: VirtualSpeaker.monitor")
                return "VirtualSpeaker.monitor"
        except Exception:
            pass
        time.sleep(1)

    # 2. Fallback: Find *any* monitor source
    try:
        result = subprocess.run(["pactl", "list", "sources", "short"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) > 1 and "monitor" in parts[1]:
                fallback = parts[1]
                logger.warning(f"⚠️ VirtualSpeaker not found. Fallback to: {fallback}")
                return fallback
    except Exception:
        pass

    # 3. Last Resort
    logger.error("❌ No audio source found. Using default '0'. Recording might be silent.")
    return "0"

def force_audio_routing(task_id, stop_event):
    """
    Background thread that constantly moves new audio streams (Chrome) 
    to the VirtualSpeaker sink to ensure they are recorded.
    """
    logger.info(f"[{task_id}] 👮 Audio Enforcer started.")
    while not stop_event.is_set():
        try:
            # Get list of inputs (applications playing audio)
            result = subprocess.run(["pactl", "list", "sink-inputs", "short"], capture_output=True, text=True)
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) > 0:
                        stream_id = parts[0]
                        # Move to VirtualSpeaker
                        subprocess.run(["pactl", "move-sink-input", stream_id, "VirtualSpeaker"], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        # Unmute and max volume just in case
                        subprocess.run(["pactl", "set-sink-input-mute", stream_id, "0"], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        subprocess.run(["pactl", "set-sink-input-volume", stream_id, "100%"], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass # Be silent to not flood logs
        time.sleep(2)
