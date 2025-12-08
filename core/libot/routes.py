import threading
import uuid
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from libot.recorder import record_task

api = Blueprint("api", __name__)


@api.route("/", methods=["POST"])
def trigger_bot():
    date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Missing 'url'"}), 400

    task_id = date_now + "_" + str(uuid.uuid4())[:8]
    duration = int(data.get("duration", 3600))

    t = threading.Thread(
        target=record_task,
        args=(
            data["url"],
            duration,
            task_id,
            data.get("record_audio", True),
            data.get("record_video", False),
        ),
    )
    t.daemon = True
    t.start()

    return jsonify({"status": "started", "task_id": task_id}), 202
