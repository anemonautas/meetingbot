# job_main.py

import os
import time
import uuid
from libot.logger import logger
from libot.recorder import record_task

def env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "y")

if __name__ == "__main__":
    meeting_url = os.environ.get("MEETING_URL")
    if not meeting_url:
        raise SystemExit("MEETING_URL is required")

    duration = int(os.environ.get("DURATION", "3600"))
    record_audio = env_bool("RECORD_AUDIO", True)
    record_video = env_bool("RECORD_VIDEO", False)

    task_id = os.environ.get("TASK_ID")
    if not task_id:
        task_id = f"{int(time.time())}_{str(uuid.uuid4())[:8]}"

    logger.info("-" * 80)
    logger.info(f"[{task_id}] Cloud Run Job starting")
    logger.info(f"[{task_id}] URL={meeting_url} DURATION={duration} AUDIO={record_audio} VIDEO={record_video}")
    logger.info("-" * 80)

    record_task(
        meeting_url,
        max_duration=duration,
        task_id=task_id,
        record_audio=record_audio,
        record_video=record_video,
    )

    logger.info(f"[{task_id}] Job finished")
