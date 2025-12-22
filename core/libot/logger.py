import logging
import sys
import os

from libot.config import OUTPUT_DIR


log_file_path = os.path.join(OUTPUT_DIR, "service.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_file_path)],
)
logger = logging.getLogger("bot")


def _log_start_job(task_id: str):
    logger.info("-" * 20)
    logger.info(f"[{task_id}] Cloud Run Job starting")
    logger.info("-" * 20)


def _log_end_job(task_id: str):
    logger.info("-" * 20)
    logger.info(f"[{task_id}] Cloud Run Job finished")
    logger.info("-" * 20)
