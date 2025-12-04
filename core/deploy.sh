echo 'build image'
docker build -t europe-west1-docker.pkg.dev/anemonautas-1f3cf/scribe/recorder:latest .

echo 'push image'
docker push europe-west1-docker.pkg.dev/anemonautas-1f3cf/scribe/recorder:latest

echo 'deploy image'
gcloud run deploy scribe-meetings \
  --image europe-west1-docker.pkg.dev/anemonautas-1f3cf/scribe/recorder:latest \
  --region europe-west1 \
  --memory=2Gi \
  --cpu=1 \
  --platform managed \
  --allow-unauthenticated