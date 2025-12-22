# Cloud functions of the project

## `trigger_meeting_recorder`

As long as Cloud Run Jobs has not a RestAPI, we need to use a Cloud Function to trigger it.

The following are the instructions to doit:

### Prerequisites

Run the function locally. As long as they are cloud functions, we may use vanilla `pip` to install the dependencies.

```bash
pip install -r requirements.txt
```

Run the function:

```bash
python -m functions_framework --target=trigger_meeting_recorder --port=8000
```

### Set the environment variables

```bash
export FUNCTION_URL='http://127.0.0.1:8000'

# You may replace this for any recent Teams meeting URL.
export MEETING_URL='https://teams.microsoft.com/l/meetup-join/19%3ameeting_MzhiMDM4M2ItMTA1NC00ZjhjLWIwY2UtNDZiZmQ0OWE4Yjk4%40thread.v2/0?context=%7b%22Tid%22%3a%2234ff9106-4c49-4535-98fa-c6566a9218f8%22%2c%22Oid%22%3a%22254a0c0c-2c9d-4477-9de2-c0e2bd0f1487%22%7d'
```

2. Trigger the function

```bash
curl -X POST "${FUNCTION_URL}" \
     -H "Content-Type: application/json" \
     -d "{
       \"meeting_url\": \"${MEETING_URL}\",
       \"duration\": ${DURATION}
     }"

```

