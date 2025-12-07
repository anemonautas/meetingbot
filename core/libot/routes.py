import base64
import binascii
import json
import os
import threading
import uuid
from datetime import datetime
import imghdr

from flask import Blueprint, request, jsonify, send_file

from libot.config import OUTPUT_DIR
from libot.logger import logger
from libot.recorder import record_task

api = Blueprint('api', __name__)

SUPPORTED_MIME_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
}
IMGHDR_TO_MIME = {
    "png": "image/png",
    "jpeg": "image/jpeg",
}
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB safety cap

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
                data.get("record_video", False)
            )
        )
    t.daemon = True
    t.start()

    return jsonify({"status": "started", "task_id": task_id}), 202


@api.route("/tango", methods=["POST"])
def upload_tango():
    data = request.get_json() or {}
    image_b64 = data.get("image")
    mime_type = data.get("mime_type")
    user_id = data.get("user_id")
    conversation_id = data.get("conversation_id")

    if not image_b64:
        logger.warning("Tango upload rejected: missing image payload")
        return jsonify({"error": "Missing 'image'"}), 400

    if not mime_type:
        logger.warning("Tango upload rejected: missing mime_type")
        return jsonify({"error": "Missing 'mime_type'"}), 400

    if mime_type not in SUPPORTED_MIME_TYPES:
        logger.warning("Tango upload rejected: unsupported mime type %s", mime_type)
        return jsonify({"error": "Unsupported 'mime_type'"}), 415

    try:
        image_bytes = base64.b64decode(image_b64, validate=True)
    except (binascii.Error, TypeError):
        logger.warning("Tango upload rejected: invalid base64 image")
        return jsonify({"error": "Invalid image encoding"}), 400

    if not image_bytes:
        logger.warning("Tango upload rejected: empty image payload")
        return jsonify({"error": "Invalid image encoding"}), 400

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        logger.warning("Tango upload rejected: image too large (%s bytes)", len(image_bytes))
        return jsonify({"error": "Image too large"}), 400

    detected_format = imghdr.what(None, h=image_bytes)
    detected_mime = IMGHDR_TO_MIME.get(detected_format)
    if detected_mime != mime_type:
        logger.warning(
            "Tango upload rejected: mime type mismatch (declared=%s, detected=%s)",
            mime_type,
            detected_mime,
        )
        return jsonify({"error": "Unsupported or mismatched 'mime_type'"}), 415

    date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    task_id = date_now + "_" + str(uuid.uuid4())[:8]

    upload_dir = os.path.join(OUTPUT_DIR, task_id, "upload")
    os.makedirs(upload_dir, exist_ok=True)

    extension = SUPPORTED_MIME_TYPES[mime_type]
    image_path = os.path.join(upload_dir, f"image.{extension}")
    with open(image_path, "wb") as image_handle:
        image_handle.write(image_bytes)

    metadata = {
        "mime_type": mime_type,
        "user_id": user_id,
        "conversation_id": conversation_id,
    }
    metadata_path = os.path.join(upload_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as metadata_handle:
        json.dump(metadata, metadata_handle)

    logger.info(
        "Stored tango upload for task %s (user=%s, conversation=%s)",
        task_id,
        user_id,
        conversation_id,
    )

    return jsonify({"task_id": task_id}), 202

