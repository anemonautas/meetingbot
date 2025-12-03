import os
import time
import functions_framework
from google.cloud import storage
from google import genai
import tempfile

MODEL_ID = "gemini-flash-lite-latest"

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
                "Listen to this audio file and provide a concise transcription of what was said."
            ]
        )
    print("-" * 20)
    print(f"BRIEF FOR {file_name}:")
    print(response.text)
    print("-" * 20)
    
    return response.text



@functions_framework.cloud_event
def expose_to_gemini(cloud_event):
    """
    Triggered by a change to a Cloud Storage bucket.
    Downloads the .wav, uploads to Gemini, and generates a brief.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY not set. Skipping Gemini upload.")
        return

    client = genai.Client(api_key=api_key)

    data = cloud_event.data
    bucket_name = data["bucket"]
    file_name = data["name"]
    
    # Simple filter to ensure we only process .wav files
    if not file_name.lower().endswith(".wav"):
        print(f"Skipping non-wav file: {file_name}")
        return

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    _, temp_local_filename = tempfile.mkstemp(suffix=".wav")
    
    try:
        print(f"Downloading {file_name}...")
        blob.download_to_filename(temp_local_filename)

        print("Uploading to Gemini File API...")
        sample_file = client.files.upload(
            file=temp_local_filename, 
        )
        
        print(f"File uploaded. URI: {sample_file.uri}")

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                sample_file, 
                "Listen to this audio file and provide a concise transcription of what was said."
            ]
        )

        print("-" * 20)
        print(f"BRIEF FOR {file_name}:")
        print(response.text)
        print("-" * 20)

    except Exception as e:
        print(f"Error processing file: {e}")
        raise e
    finally:
        if os.path.exists(temp_local_filename):
            os.remove(temp_local_filename)
