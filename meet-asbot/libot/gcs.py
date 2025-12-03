import os
from google.cloud import storage
from libot.config import GCS_BUCKET, GCS_PREFIX
from libot.logger import logger

def upload_recordings_to_gcs(task_id, path, file_name = "recording.mp4"):
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
        
        if path and os.path.exists(path):
            blob = bucket.blob(f"{base}/{file_name}")
            blob.upload_from_filename(path)
            logger.info(f"✅ Uploaded file: gs://{GCS_BUCKET}/{base}/{file_name}")
        else:
            logger.error(f"❌ File not found for upload: {path}")
            
    except Exception as e:
        logger.error(f"❌ GCS Upload failed: {e}")
