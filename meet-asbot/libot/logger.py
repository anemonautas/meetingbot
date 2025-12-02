import logging
import sys
import os
from .config import OUTPUT_DIR

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
