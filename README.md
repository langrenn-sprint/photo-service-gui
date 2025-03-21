# webserver photo-service-gui

Hovedfunksjonen til photo-service-gui er å analysere video og generere events på passeringer. Events inkuderer både skjermbilder og analyse av innholdet som deles på PubSub.

![image](https://github.com/langrenn-sprint/photo-service-gui/assets/56455987/2b7599a2-a58e-4ade-816e-c15abb1d6f7b)

## Slik går du fram for å kjøre dette lokalt

## Utvikle og kjøre lokalt

### Krav til programvare

- [pyenv](https://github.com/pyenv/pyenv) (recommended)
- [poetry](https://python-poetry.org/)
- [nox](https://nox.thea.codes/en/stable/)
- [nox-poetry](https://pypi.org/project/nox-poetry/)

### Installere programvare og sette miljøvariable

```Shell
% git clone https://github.com/langrenn-sprint/photo-service-gui.git
% cd photo-service-gui
% pyenv install 3.11
% pyenv local 3.11
% pipx install poetry
% pipx install nox
% pipx inject nox nox-poetry
% poetry install
```

### If required - virtual environment

Install: curl <https://pyenv.run> | bash
Create: python -m venv .venv (replace .venv with your preferred name)
Install python 3.12: pyenv install 3.12
Activate:
source .venv/bin/activate

## oppdatere

```Shell
% poetry update / poetry add <module>
```

## Miljøvariable

```Shell
Du må sette opp ei .env fil med miljøvariable. Eksempel:
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
LOCAL_PHOTO_DIRECTORY=/home/github/photo-service-gui/photo_service_gui/files

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

### Innstillinger i google cloud
- Create OAuth2.0 client Id: <https://console.cloud.google.com/apis/credentials>
- Hints1: Javascript origins: http://localhost:8080 and http://localhost
- Hints2: Redirect URI: http://localhost:8080/photos_adm and http://localhost/photos_adm
- Download client_secret.json and save it in secrets folder, remember to add it to .env file
- Set up conset screen
- PUBSUB: Create topic and subscription
- Install python libraries: pip install --upgrade google-cloud-pubsub
- Set upp application default credentials: https://cloud.google.com/docs/authentication/provide-credentials-adc#how-to
- Cloud storage: Bucket - https://storage.googleapis.com/langrenn-photo/result2.jpg
  - Hint: Set to publicly available and allUsers principals, role Viewer

Denne fila _skal_ ligge i .dockerignore og .gitignore
### Kjøre webserver lokalt
```

## Start lokal webserver mha aiohttp-devtools(adev)

```zsh
source .env
poetry run adev runserver -p 8096 photo_service_gui
poetry run adev runserver --no-livereload -p 8096 photo_service_gui
docker-compose up photo-service user-service event-service competition-format-service integration-service mongodb
```

### If required - virtual environment

Install: curl <https://pyenv.run> | bash
Create: python -m venv .venv (replace .venv with your preferred name)
Install python 3.12: pyenv install 3.12
Activate:
source .venv/bin/activate

## Referanser

Dokumentasjon: <https://langrenn-sprint.github.io/docs/>
aiohttp: <https://docs.aiohttp.org/>
Googel OAuth2: <https://developers.google.com/identity/protocols/oauth2>
Google Photos API: <https://developers.google.com/photos/library/guides/get-started>

## testfiler for video

VIDEO_URL=<http://10.0.0.6:8080/video>
VIDEO_URL=https://harnaes.no/maalfoto/2023SkiMaal.mp4
VIDEO_URL=20240113_105758_KJ.mp4
VIDEO_URL=<https://harnaes.no/maalfoto/2023SkiMaal.mp4>
VIDEO_URL=/Users/t520834/github/vision-ai-service/20240113_105758_KJ.mp4
VIDEO_URL=rtsp://stream:Video1@10.0.0.18:88/videoMain
VIDEO_URL=rtsp://stream:Video1@192.168.1.160:88/videoSub
VIDEO_URL=<http://192.168.1.152:8080/video>
