"""Package for exposing validation endpoint."""

import base64
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp_session import get_session, setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from dotenv import load_dotenv

from .views import (
    Config,
    Login,
    Logout,
    Main,
    Photos,
    Ping,
    Status,
    VideoEvents,
)

load_dotenv()
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
PROJECT_ROOT = f"{Path.cwd()}/photo_service_gui"
logging.info(f"PROJECT_ROOT: {PROJECT_ROOT}")
gs_config_file = f"{PROJECT_ROOT}/config/global_settings.json"


async def handler(request) -> web.Response:
    """Create a session handler."""
    session = await get_session(request)
    last_visit = session.get("last_visit", None)
    session["last_visit"] = time.time()
    text = f"Last visited: {last_visit}"
    return web.Response(text=text)


async def create_app() -> web.Application:
    """Create an web application."""
    app = web.Application()

    # sesson handling - secret_key must be 32 url-safe base64-encoded bytes
    fernet_key = os.getenv("FERNET_KEY", "23EHUWpP_tpleR_RjuX5hxndWqyc0vO-cjNUMSzbjN4=")
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))
    app.router.add_get("/secret", handler)

    # Set up logging - errors to separate file
    logging.basicConfig(level=LOGGING_LEVEL)
    file_handler = RotatingFileHandler("error.log", maxBytes=1024 * 1024, backupCount=5)
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)

    # Set up template path
    template_path = f"{PROJECT_ROOT}/templates"
    aiohttp_jinja2.setup(
        app,
        enable_async=True,
        loader=jinja2.FileSystemLoader(template_path),
    )
    logging.info(f"template_path: {template_path}")

    app.add_routes(
        [
            web.view("/", Main),
            web.view("/config", Config),
            web.view("/login", Login),
            web.view("/logout", Logout),
            web.view("/ping", Ping),
            web.view("/photos", Photos),
            web.view("/status", Status),
            web.view("/video_events", VideoEvents),
        ],
    )
    static_dir = f"{PROJECT_ROOT}/static"
    files_dir = f"{PROJECT_ROOT}/files"
    logging.info(f"static_dir: {static_dir}")
    logging.info(f"files_dir: {files_dir}")

    app.router.add_static("/static/", path=static_dir, name="static")
    app.router.add_static("/files/", path=files_dir, name="files")

    return app
