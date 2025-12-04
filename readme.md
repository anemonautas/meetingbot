# Meetings Recorder

## Requirements

GEMINI_API_KEY
GOOGLE_API_KEY
GCS_BUCKET

## Architecture

The main process is a Flask app that runs in a container. It
emulates a Chrome browser and records a meeting. 



curl -X POST localhost:8080 \
      -H "Content-Type: application/json" \
      -d '{"url": "https://teams.microsoft.com/l/meetup-join/19%3ameeting_MTVjNjNlNGQtYWJhZi00ODNjLWIwOTEtZWFmYmM5NWJhNGVl%40thread.v2/0?context=%7b%22Tid%22%3a%2234ff9106-4c49-4535-98fa-c6566a9218f8%22%2c%22Oid%22%3a%22619a0a3b-ad73-47cd-b36b-07e588d11db1%22%7d", "duration": 3600}'
   


gcloud run deploy scribe-meetings \
  --image europe-west1-docker.pkg.dev/anemonautas-1f3cf/scribe/recorder:latest \
  --region europe-west1 \
  --memory=2Gi \
  --cpu=1 \
  --platform managed \
  --allow-unauthenticated


gcloud run services update scribe-meetings \
  --region europe-west1 \
  --set-env-vars=GEMINI_API_KEY=${GEMINI_API_KEY},GCS_BUCKET=${GCS_BUCKET}





curl -X POST https://scribe-meetings-ue5edez4qq-ew.a.run.app \
   -H "Content-Type: application/json" \
   -d '{"url": "https://teams.microsoft.com/l/meetup-join/19%3ameeting_MTVjNjNlNGQtYWJhZi00ODNjLWIwOTEtZWFmYmM5NWJhNGVl%40thread.v2/0?context=%7b%22Tid%22%3a%2234ff9106-4c49-4535-98fa-c6566a9218f8%22%2c%22Oid%22%3a%22619a0a3b-ad73-47cd-b36b-07e588d11db1%22%7d", "duration": 3600, "record_audio": false, "record_video": false}'



gcloud builds submit --tag europe-west1-docker.pkg.dev/anemonautas-1f3cf/scribe/recorder:latest


gcloud run jobs delete meeting-recorder-job --region europe-west1

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



gcloud run jobs execute meeting-recorder-job --region europe-west1 --update-var-envs MEETING_URL="https://teams.microsoft.com/l/meetup-join/19%3ameeting_MTVjNjNlNGQtYWJhZi00ODNjLWIwOTEtZWFmYmM5NWJhNGVl%40thread.v2/0?context=%7b%22Tid%22%3a%2234ff9106-4c49-4535-98fa-c6566a9218f8%22%2c%22Oid%22%3a%22619a0a3b-ad73-47cd-b36b-07e588d11db1%22%7d",DURATION=1800,RECORD_AUDIO=true,RECORD_VIDEO=false,TASK_ID="foo-$(date +%s)"
