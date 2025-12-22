import os
import json
from google import genai
from google.genai import types
from libot.logger import logger
from libot.config import OUTPUT_DIR
from libot.gcs import upload_transcriptions_to_gcs

MODEL_ID = "gemini-flash-latest"

generate_content_config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=genai.types.Schema(
        type=genai.types.Type.OBJECT,
        required=["conversation"],
        properties={
            "conversation": genai.types.Schema(
                type=genai.types.Type.ARRAY,
                items=genai.types.Schema(
                    type=genai.types.Type.OBJECT,
                    required=["speaker", "text"],
                    properties={
                        "speaker": genai.types.Schema(
                            type=genai.types.Type.STRING,
                        ),
                        "text": genai.types.Schema(
                            type=genai.types.Type.STRING,
                        ),
                    },
                ),
            ),
        },
    ),
)

generate_content_config_briefing = types.GenerateContentConfig(
    system_instruction="""Ton role est d'écrire des emails CompteRendu pour elmy.
    Tes outputs ne doivent pas contenir des ``` or other delimiters.
    Resume la reunion dans une phrase, dans le output "subject"
    """,
        response_mime_type="application/json",

    response_schema=genai.types.Schema(
        type=genai.types.Type.OBJECT,
        required=["subject", "htmlBody"],
        properties={
            "subject": genai.types.Schema(
                type=genai.types.Type.STRING
            ),
            "htmlBody": genai.types.Schema(
                type=genai.types.Type.STRING
            ),
        })
    )


def persist_transcription(task_id, transcription, idx):
    task_dir = os.path.join(OUTPUT_DIR, task_id, "transcriptions")
    os.makedirs(task_dir, exist_ok=True)

    transcription_file = os.path.join(task_dir, f"{task_id}_{idx}.json")
    with open(transcription_file, "w") as f:
        f.write(json.dumps(transcription))
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
        config=generate_content_config,
    )

    response_json = response.text
    persist_transcription(task_id, response_json, idx)

    return response.text



def make_briefing(task_id: str, transcript: str):
    logger.info(f'Using gemini for get a briefing from {task_id}')
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not set. Skipping Gemini upload.")
        return

    client = genai.Client(api_key=api_key)
  
  
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[
            types.Part.from_text(text=transcript),
            types.Part.from_text(text="""
Fait un compte rendu detaillé en pur HTML du transcript partagé.
Ton output doit etre directement le html car ce sera inseré directement dans un mail
Sections :
- Contenu de la reunion
- Prochaines étapes:
  - Responsable action: Tache
- Autres actions

""")
        ],
        config=generate_content_config_briefing,
    )
    
    return response.text