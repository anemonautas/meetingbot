import os
from google import genai
from libot.logger import logger
from libot.config import OUTPUT_DIR
from libot.gcs import upload_transcriptions_to_gcs

MODEL_ID = "gemini-flash-latest"

def persist_transcription(task_id, transcription, idx):
    logger.info(f"{transcription}")
    task_dir = os.path.join(OUTPUT_DIR, task_id, 'transcriptions')
    os.makedirs(task_dir, exist_ok=True)

    transcription_file = os.path.join(task_dir, f"{task_id}_{idx}.txt")
    with open(transcription_file, "w") as f:
        f.write(transcription)
        logger.info(f"✅ Transcription saved to {transcription_file}")


    upload_transcriptions_to_gcs(task_id, transcription_file)


def gemini_transcription(file_name, task_id, idx):
    """
    Transcribes an audio file using Gemini.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not set. Skipping Gemini upload.")
        return

    client = genai.Client(api_key=api_key)
    sample_file = client.files.upload(
        file=file_name,
    )

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[
            sample_file,
            "Extract a complete transcript labeling the different speakers.",
        ],
    )
    persist_transcription(task_id, response.text, idx)
    return response.text
