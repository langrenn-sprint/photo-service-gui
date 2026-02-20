# webserver photo-service-gui

Hovedfunksjonen til photo-service-gui er å analysere video og generere events på passeringer. Events inkuderer både skjermbilder og analyse av innholdet som deles på PubSub.

![image](https://github.com/langrenn-sprint/photo-service-gui/assets/56455987/2b7599a2-a58e-4ade-816e-c15abb1d6f7b)

## Slik går du fram for å kjøre dette lokalt

Example of usage:

```Zsh
% curl -H "Content-Type: application/json" \
  -X POST \
  --data '{"username":"admin","password":"passw123"}' \
  http://localhost:8080/login
% export ACCESS="" #token from response
% curl -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -X POST \
  --data @tests/files/user.json \
  http://localhost:8080/users
% curl -H "Authorization: Bearer $ACCESS"  http://localhost:8080/users
```

## Architecture

Layers:

- views: routing functions, maps representations to/from model
- services: enforce validation, calls adapter-layer for storing/retrieving objects
- models: model-classes
- adapters: adapters to external services

## Environment variables

To run the service locally, you need to supply a set of environment variables. A simple way to solve this is to supply a .env file in the root directory.

A minimal .env:

```Zsh
JWT_SECRET=secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=password
DB_USER=admin
DB_PASSWORD=password
EVENTS_HOST_SERVER=localhost
EVENTS_HOST_PORT=8082
PHOTOS_HOST_SERVER=localhost
PHOTOS_HOST_PORT=8092
FERNET_KEY=23EHUWpP_MyKey_MyKeyhxndWqyc0vO-MyKeySMyKey=
JWT_EXP_DELTA_SECONDS=3600
LOGGING_LEVEL=INFO
USERS_HOST_SERVER=localhost
USERS_HOST_PORT=8086
GOOGLE_STORAGE_BUCKET=langrenn-sprint
GOOGLE_STORAGE_SERVER=https://storage.googleapis.com
GOOGLE_CLOUD_PROJECT=sigma-celerity-257719
GOOGLE_APPLICATION_CREDENTIALS=/home/hh/github/secrets/application_default_credentials.json


### If required - virtual environment

Install: curl <https://pyenv.run> | bash
Create: python -m venv .venv (replace .venv with your preferred name)
Install python 3.13: pyenv install 3.13
Activate:
source .venv/bin/activate

## oppdatere

```Shell
% poetry update / poetry add <module>
```

### Kjøre webserver lokalt
## Requirement for development

Install [uv](https://docs.astral.sh/uv/), e.g.:

```Zsh
% curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the dependencies:

```Zsh
% uv sync
```

## Start the server locally (with all required services):

set -a
source .env
set +a
uv run adev runserver -p 8096 photo_service_gui
docker compose up integration-service race-service competition-format-service photo-service user-service event-service mongodb capture-video-service

## Running the wsgi-server in Docker

To build and run the service in a Docker container:

```Zsh
% docker build -t langrenn-sprint/photo-service-gui:latest .
% docker run --env-file .env -p 8080:8080 -d langrenn-sprint/photo-service-gui:latest
```

The easier way would be with docker-compose:

```Zsh
docker compose up --build
```

## Running tests

We use [pytest](https://docs.pytest.org/en/latest/) for contract testing.

To run linters, checkers and tests:

```Zsh
% uv run poe release
```

To run tests with logging, do:

```Zsh
% uv run pytest -m integration -- --log-cli-level=DEBUG
```

### Rydde opp i docker stuff
docker system prune

### Starte services i docker
sudo docker-compose pull #oppdatere images
sudo docker-compose up --build #bygge og debug modus
sudo docker-compose up -d #kjøre-modus

### Oppdatere services i docker
sudo docker-compose stop #oppdatere images
sudo docker-compose pull #oppdatere images
sudo git pull #photo-service-gui
sudo docker-compose up --build #bygge og debug modus
sudo docker-compose stop #oppdatere images
sudo docker-compose up -d #kjøre-modus


## testfiler for video

VIDEO_URL=<http://10.0.0.6:8080/video>
VIDEO_URL=https://harnaes.no/maalfoto/2023SkiMaal.mp4
VIDEO_URL=/home/heming/Nedlastinger/20250525_GKOpp1.mp4
VIDEO_URL=https://storage.googleapis.com/langrenn-sprint/photos/20240309_Ragde_kort.mp4
VIDEO_URL=rtsp://stream:Video1@10.0.0.18:88/videoMain
VIDEO_URL=rtsp://stream:Video1@192.168.1.160:88/videoSub
VIDEO_URL=<http://192.168.1.152:8080/video>

## CAPTURE_SRT
Capture video using Google Live Stream API. Creates an SRT Push endpoint that waits for incoming video streams and stores them directly to cloud storage with configurable clip duration. This is a cloud-native approach that requires no local compute resources.

**When to use CAPTURE_SRT:**
- Event-based or sporadic streaming (lower cost for low usage)
- Serverless/cloud-native architecture preferred
- Minimal infrastructure maintenance desired

See [video-streaming/README.md](video-streaming/README.md) for detailed documentation, [video-streaming/COMPARISON.md](video-streaming/COMPARISON.md) for feature comparison, and [video-streaming/SETUP.md](video-streaming/SETUP.md) for setup instructions.

