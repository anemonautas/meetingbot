import os
from google import genai

MODEL_ID = "gemini-flash-latest"

def gemini_transcription(file_name):
    """
    Transcribes an audio file using Gemini.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set. Skipping Gemini upload.")
        return

    client = genai.Client(api_key=api_key)
    sample_file = client.files.upload(
            file=file_name, 
        )
    
    response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                sample_file, 
                "Extract a complete transcript labeling the different speakers."
            ]
        )
    return response.text


