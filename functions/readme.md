# Cloud functions of the project

- Need a passeplat for a given file be exposed to gemini.
- This function will be triggered by a creation of a file in a given bucket.

## Deployment

To deploy this function to Google Cloud, run the following command (replace `YOUR_TRIGGER_BUCKET` with your actual bucket name):

```bash
gcloud functions deploy expose-to-gemini \
    --gen2 \
    --runtime=python311 \
    --region=us-central1 \
    --source=./functions \
    --entry-point=expose_to_gemini \
    --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
    --trigger-event-filters="bucket=anemophotoser" \
    --set-env-vars=GEMINI_API_KEY=$your_gemini_api_key
```

> **Note:** Ensure `GEMINI_API_KEY` is set in the environment variables.

## Local Emulation

You can run the function locally using `functions-framework`.

1. **Install dependencies:**

   ```bash
   pip install -r functions/requirements.txt
   ```

2. **Run the function:**

   ```bash
   # Set your API key first
   export GEMINI_API_KEY=your_api_key
   
   functions-framework --target=expose_to_gemini --debug
   ```

3. **Trigger with cURL:**
   Since this is a CloudEvent function, you need to send a properly formatted POST request.

   ```bash
   curl -X POST localhost:8000 \
      -H "Content-Type: application/json" \
      -H "ce-id: 1234567890" \
      -H "ce-specversion: 1.0" \
      -H "ce-type: google.cloud.storage.object.v1.finalized" \
      -H "ce-source: //storage.googleapis.com/projects/_/buckets/anemophotoser" \
      -d '{
            "bucket": "anemophotoser",
            "name": "18451c14/audio.wav"
          }'
   ```

*Note: The function now expects `.wav` files and will try to download them from the specified bucket, so ensure the file actually exists in your GCS bucket and you have credentials to access it locally (e.g. via `gcloud auth application-default login`).*
