# Meetings Recorder

## Requirements

GEMINI_API_KEY
GOOGLE_API_KEY
GCS_BUCKET

## Architecture

The main process is executed as a Google Run Job, which emulates a Chrome browser and records a meeting. 

For activating this process you need to create a Google Run Job and set the environment variables.
For doing this, you can use the following command:

```bash
gcloud run jobs create meeting-recorder-job \
  --image europe-west1-docker.pkg.dev/anemonautas-1f3cf/scribe/recorder:latest \
  --region europe-west1 \
  --cpu 1 \
  --memory 2Gi \
  --max-retries 0 \
  --task-timeout 3600s \
  --set-env-vars OUTPUT_DIR=/tmp/output \
  --set-env-vars EXIT_ON_FINISH=true \
  --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY} \
  --set-env-vars GCS_BUCKET=${GCS_BUCKET}
```


## Development Setup

The whole project is dockerized. You can run it with

```bash
./run.sh
```

or docker compose yourself

```bash
docker compose up --build
```

It will create a volume called `recordings` where the recordings will be stored.


### Python setup

As we are using `uv` as our python manager, you can use the following commands to install the dependencies:

```bash
cd /core
uv .venv
source .venv/bin/activate
uv sync
```

