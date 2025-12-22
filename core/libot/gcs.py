import os
from google.cloud import storage
from libot.config import GCS_BUCKET, GCS_PREFIX
from libot.logger import logger
from typing import Iterable, Iterator, Optional, Tuple
 
def upload_recordings_to_gcs(task_id, path, file_name="recording.mp4"):
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


def upload_transcriptions_to_gcs(task_id, transcription_file):
    if not GCS_BUCKET:
        logger.warning("No GCS_BUCKET defined. Skipping upload.")
        return

    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        base = f"{GCS_PREFIX}/{task_id}" if GCS_PREFIX else task_id

        if transcription_file and os.path.exists(transcription_file):
            blob = bucket.blob(
                f"{base}/transcriptions/{os.path.basename(transcription_file)}"
            )
            blob.upload_from_filename(transcription_file)
            logger.info(
                f"✅ Uploaded file: gs://{GCS_BUCKET}/{base}/transcriptions/{os.path.basename(transcription_file)}"
            )
        else:
            logger.error(f"❌ File not found for upload: {transcription_file}")

    except Exception as e:
        logger.error(f"❌ GCS Upload failed: {e}")


def iter_bucket_files_bytes(
    bucket_name: str,
    *,
    prefix: Optional[str] = None,
) -> Iterator[Tuple[str, bytes]]:
    client = storage.Client()
    # list_blobs handles pagination internally :contentReference[oaicite:2]{index=2}
    for blob in client.list_blobs(bucket_name, prefix=prefix):
        # Skip "directory marker" objects if present
        if blob.name.endswith("/"):
            continue
        text = blob.download_as_text(encoding="utf-8")
        logger.info(text)
        yield blob.name, text


def fetch_transcriptions_from_gcs(task_id: str):
    if not GCS_BUCKET:
        logger.warning("No GCS_BUCKET defined. Skipping upload.")
        return

    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        base = f"{task_id}/transcriptions" 

        transcript = []
        for name, data in iter_bucket_files_bytes(bucket, prefix=base):

            print(name, len(data))
            transcript.append(data)

        full_transcript = "".join(transcript)
        logger.info(full_transcript)
        return full_transcript


    except Exception as e:
        logger.error(f"❌ GCS Upload failed: {e}")
