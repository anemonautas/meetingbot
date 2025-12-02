import os
import subprocess
from .config import AVATAR_Y4M, AVATAR_IMAGE, AVATAR_RESOLUTION, AVATAR_DURATION
from .logger import logger

def ensure_avatar_y4m():
    """Generates a raw video file from an image for Chrome to use as a webcam."""
    if AVATAR_Y4M and os.path.exists(AVATAR_Y4M):
        return AVATAR_Y4M
    
    if AVATAR_IMAGE and os.path.exists(AVATAR_IMAGE):
        try:
            logger.info(f"🎨 Generating avatar video from {AVATAR_IMAGE}")
            width, height = AVATAR_RESOLUTION.split("x")
            # FFmpeg command to create a looping raw video file
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", AVATAR_IMAGE, "-t", str(AVATAR_DURATION),
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-pix_fmt", "yuv420p", AVATAR_Y4M
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return AVATAR_Y4M
        except Exception as e:
            logger.error(f"Failed to generate avatar: {e}")
            pass
    return None
