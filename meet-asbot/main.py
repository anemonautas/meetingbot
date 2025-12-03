import os
import threading
import uuid
from datetime import datetime
from flask import Flask, request, jsonify

# Import from libot package
from libot.config import DISPLAY_NUM
from libot.logger import logger
from libot.recorder import record_task

# --- FLASK APP ---
app = Flask(__name__)

# Ensure environment variables are set for PulseAudio and Display
os.environ["DISPLAY"] = DISPLAY_NUM
os.environ["PULSE_SERVER"] = "unix:/var/run/pulse/native"

@app.route("/", methods=["POST"])
def trigger_bot():
    date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Missing 'url'"}), 400

    task_id = date_now + "_" + str(uuid.uuid4())[:8]
    duration = int(data.get("duration", 3600))
    
    t = threading.Thread(target=record_task, args=(data["url"], duration, task_id, data.get("record_audio", True), data.get("record_video", False)))
    t.daemon = True
    t.start()
    
    return jsonify({"status": "started", "task_id": task_id}), 202


if __name__ == "__main__":
    
    lock_file = f"/tmp/.X{DISPLAY_NUM.replace(':','')}-lock"
    if os.path.exists(lock_file):
        os.remove(lock_file)
        
    port = int(os.environ.get("PORT", 8080))
    logger.info("-" * 80)
    logger.info(f"🚀 Service starting on port {port}")
    logger.info("-" * 80)
    app.run(host="0.0.0.0", port=port)


    