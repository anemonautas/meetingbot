import os
from logging import getLogger
import time
import uuid

logger = getLogger("libot.config")


def env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "y")


MEETING_URL = os.environ.get("MEETING_URL")
if not MEETING_URL:
    raise SystemExit("MEETING_URL is required")


TASK_ID = os.environ.get("TASK_ID")
if not TASK_ID:
    logger.debug("TASK_ID is not set, generating a random one")
    TASK_ID = f"{int(time.time())}_{str(uuid.uuid4())[:8]}"


AVATAR_IMAGE = os.environ.get("AVATAR_IMAGE", "/app/assets/scribe.png")
AVATAR_Y4M = os.environ.get("AVATAR_Y4M", "/app/assets/scribe.mjpeg")
EXIT_ON_FINISH = env_bool("EXIT_ON_FINISH", True)

GCS_BUCKET = os.environ.get("GCS_BUCKET")
GCS_PREFIX = os.environ.get("GCS_PREFIX", "").rstrip("/")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/output")
SEGMENT_SECONDS = os.environ.get("SEGMENT_SECONDS", "300")

# Virtual Display ID
DISPLAY_NUM = ":99"

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


DURATION = int(os.environ.get("DURATION", "7200"))
RECORD_AUDIO = env_bool("RECORD_AUDIO", True)
RECORD_VIDEO = env_bool("RECORD_VIDEO", False)
