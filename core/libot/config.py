import os


AVATAR_IMAGE = os.environ.get("AVATAR_IMAGE", "/app/assets/avatar.png")
AVATAR_Y4M = os.environ.get("AVATAR_Y4M", "/app/assets/avatar.mjpeg")
EXIT_ON_FINISH = os.environ.get("EXIT_ON_FINISH", "1") == "1"

GCS_BUCKET = os.environ.get("GCS_BUCKET")
GCS_PREFIX = os.environ.get("GCS_PREFIX", "").rstrip("/")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/output")
SEGMENT_SECONDS = os.environ.get("SEGMENT_SECONDS", "300")

# Virtual Display ID
DISPLAY_NUM = ":99"

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
