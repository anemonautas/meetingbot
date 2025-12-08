import os
from libot.config import AVATAR_Y4M
from libot.logger import logger


def ensure_avatar_y4m():
    """Generates a raw video file from an image for Chrome to use as a webcam."""
    if AVATAR_Y4M and os.path.exists(AVATAR_Y4M):
        logger.debug("AVATAR_Y4M set. Using avatar.")
        return AVATAR_Y4M

    logger.warning("AVATAR_Y4M not set. Skipping using avatar.")
    return None
