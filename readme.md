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
      