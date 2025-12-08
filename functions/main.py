import functions_framework

import os
import logging
import uuid
from google.cloud import run_v2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = run_v2.JobsClient()

PROJECT_ID = os.environ.get('GCP_PROJECT', 'anemonautas-1f3cf') # or set manually
REGION = os.environ.get('REGION', 'europe-west1')
JOB_NAME = os.environ.get('JOB_NAME', 'meeting-recorder-job')


@functions_framework.http
def trigger_meeting_recorder(request):
    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            raise ValueError("Empty or invalid JSON body")
    except ValueError as e:
        logger.error(f"Bad Request: {e}")
        return ({'error': 'Invalid JSON provided'}, 400)

    meeting_url = request_json.get('meeting_url')
    if not meeting_url:
        logger.warning("Attempted to trigger job without meeting_url")
        return ({'error': 'meeting_url is required'}, 400)

    # 3. Prepare Job Configuration
    # Generate a unique ID for this specific run
    task_id = f"rec-{str(uuid.uuid4())}"
    
    # Prepare environment variables for the job container
    # Note: We convert all values to strings as EnvVars must be strings
    env_vars = {
        "meeting_url": meeting_url,
        "duration": str(request_json.get('duration', 1800)),
        "record_audio": str(request_json.get('record_audio', True)).lower(),
        "record_video": str(request_json.get('record_video', False)).lower(),
        "task_id": task_id
    }

    logger.info(f"Preparing to trigger job {JOB_NAME} for task {task_id}")

    job_path = client.job_path(PROJECT_ID, REGION, JOB_NAME)

    env_var_objects = [
        run_v2.EnvVar(name=k, value=v) for k, v in env_vars.items()
    ]

    overrides = run_v2.RunJobRequest.Overrides(
        container_overrides=[
            run_v2.RunJobRequest.Overrides.ContainerOverride(
                env=env_var_objects
            )
        ]
    )

    request_obj = run_v2.RunJobRequest(
        name=job_path,
        overrides=overrides
    )

    try:
        operation = client.run_job(request=request_obj)
        execution_name = operation.metadata.name
        
        logger.info(f"Job triggered successfully. Execution: {execution_name}")
        
        return ({
            'message': 'Job started successfully',
            'executionName': execution_name,
            'taskId': task_id
        }, 200)

    except Exception as e:
        logger.exception("Failed to trigger Cloud Run Job")
        return ({'error': str(e)}, 500)

