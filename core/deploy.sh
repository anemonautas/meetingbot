echo 'clean old image'
gcloud run jobs delete meeting-recorder-job --region europe-west1

echo 'build image'
docker build -t europe-west1-docker.pkg.dev/anemonautas-1f3cf/scribe/recorder:latest .

echo 'push image'
docker push europe-west1-docker.pkg.dev/anemonautas-1f3cf/scribe/recorder:latest

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


export MEETING_URL='https://teams.microsoft.com/l/meetup-join/19%3ameeting_ZDJhMzY1YTQtMDQwZS00MjZhLWFkMjMtYWM0ZmFlZjBhMDMy%40thread.v2/0?context=%7b%22Tid%22%3a%2234ff9106-4c49-4535-98fa-c6566a9218f8%22%2c%22Oid%22%3a%22619a0a3b-ad73-47cd-b36b-07e588d11db1%22%7d'


gcloud alpha run jobs execute meeting-recorder-job --region europe-west1 --update-env-vars MEETING_URL=${MEETING_URL},DURATION=1800,RECORD_AUDIO=true,RECORD_VIDEO=false,TASK_ID="foo-$(date +%s)"


gcloud run jobs describe meeting-recorder-job --region europe-west1
