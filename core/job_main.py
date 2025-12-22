from libot.logger import _log_end_job, _log_start_job
from libot.recorder import record_task
from libot.config import (
    TASK_ID,
    SEGMENT_SECONDS,
    MEETING_URL,
    DURATION,
    RECORD_AUDIO,
    RECORD_VIDEO,
)


def job_main():
    _log_start_job(TASK_ID)

    record_task(
        meeting_url=MEETING_URL,
        max_duration=DURATION,
        task_id=TASK_ID,
        record_audio=RECORD_AUDIO,
        record_video=RECORD_VIDEO,
        segment_seconds=SEGMENT_SECONDS,
    )

    _log_end_job(TASK_ID)


if __name__ == "__main__":
    job_main()
