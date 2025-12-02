import os
from google.cloud import storage
from .config import GCS_BUCKET, GCS_PREFIX
from .logger import logger

# --- GCS UPLOAD ---
def upload_recordings_to_gcs(task_id, video_path):
    """
    Uploads the resulting video to Google Cloud Storage.
    """
    if not GCS_BUCKET:
        logger.warning("No GCS_BUCKET defined. Skipping upload.")
        return

    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        base = f"{GCS_PREFIX}/{task_id}" if GCS_PREFIX else task_id
        
        if video_path and os.path.exists(video_path):
            blob = bucket.blob(f"{base}/recording.mp4")
            blob.upload_from_filename(video_path)
            logger.info(f"✅ Uploaded video: gs://{GCS_BUCKET}/{base}/recording.mp4")
        else:
            logger.error(f"❌ Video file not found for upload: {video_path}")
            
    except Exception as e:
        logger.error(f"❌ GCS Upload failed: {e}")
