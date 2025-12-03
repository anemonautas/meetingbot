import os
import subprocess
from libot.config import AVATAR_Y4M, AVATAR_IMAGE
from libot.logger import logger


def ensure_avatar_y4m():
    """Generates a raw video file from an image for Chrome to use as a webcam."""
    if AVATAR_Y4M and os.path.exists(AVATAR_Y4M):
        return AVATAR_Y4M
    
    return None
