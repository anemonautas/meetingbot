# Meeting Recorder Core

This is the core of the project. It is an `uv` package that can be used to record a meeting from a given URL. For doing so it uses the `libot` library.

## Developed entrypoints

- `rest_api.py`: A FastAPI application that provides a REST API for triggering the recording bot. 
If you want to run it under a kubernetes infrastructure, this is what you should hit.
- `job_main.py`: The main entrypoint for the Cloud Run Job. This is an asynchronous entrypoint that will be triggered by the Cloud Run Job. The advantages are the Cloudness of the app testing the Cloud Run Job infrastructure.


### Project structure

```
..
├── core                              # Core of the project
│   ├── assets                        # Assets for the virtual user
│   │   ├── avatar.mjpeg
│   │   └── avatar.png
│   ├── conftest.py                   # Configuration for the tests
│   ├── deploy.sh                     # Deployment script
│   ├── Dockerfile                    # Dockerfile for the project
│   ├── entrypoint.sh                 # Entrypoint for the container
│   ├── job_main.py                   # Main entrypoint for the Cloud Run Job
│   ├── libot                         # Library for the virtual recording bot
│   │   ├── audio.py                  # Audio handling
│   │   ├── avatar.py                 # Avatar fetcher
│   │   ├── browser.py                # Virtual Browser (Selenium)
│   │   ├── compress.py               # Compress sound functions
│   │   ├── config.py                 # Configuration for the virtual recording bot
│   │   ├── gcs.py                    # Google Cloud Storage 
│   │   ├── gemini.py                 # Gemini processing
│   │   ├── js_scripts.py             # JavaScript functions for handle the sites
│   │   ├── logger.py                 # Logger
│   │   ├── meeting.py                # Handle meeting interactions
│   │   ├── recorder.py               # Recorder process
│   │   └── routes.py                 # Routes for the REST API
│   ├── openapi.yaml                  # OpenAPI specification for the REST API
│   ├── pyproject.toml                # Project `uv` configuration
│   ├── README.md                     # Project README
│   ├── rest_api.py                   # REST API entrypoint
│   ├── tests                         # Tests directory
│   │   ├── fixture                   # Fixtures directory
│   │   ├── test_chrome_min.py        # Chrome min test
│   │   ├── test_config_and_logger.py # Configuration and logger test
│   │   └── test_gcs.py               # Google Cloud Storage test
│   └── uv.lock                       # Project `uv` lock file
├── docker-compose.yml                # Docker Compose configuration
├── functions                         # Functions directory
│   ├── main.py                       # HTTP Trigger entrypoint for the Cloud Run Job
│   ├── readme.md                     # Functions README
│   ├── requirements.txt              # Functions requirements
│   └── test_local.py                 # Local test for the functions
├── _Jenkinsfile                      # Jenkinsfile for the CI/CD pipeline
├── readme.md                         # Project README
├── recordings                        # Recordings directory. This is added as a volume to the container.
├── run.sh                            # Run the job in local.

```

