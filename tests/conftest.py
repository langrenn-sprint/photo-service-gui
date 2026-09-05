"""Conftest module."""

import time
from collections.abc import Iterator
from http import HTTPStatus
from os import environ as env
from pathlib import Path
from typing import Any

import pytest
import requests
from aiohttp.test_utils import TestClient as _TestClient
from dotenv import load_dotenv
from pytest_docker.plugin import DockerComposeExecutor, Services
from requests.exceptions import ConnectionError as RequestsConnectionError

from photo_service_gui import create_app

load_dotenv()
# Container-internal port event-service listens on (not the gui's own HOST_PORT)
EVENT_SERVICE_CONTAINER_PORT = int(env.get("EVENT_SERVICE_CONTAINER_PORT", "8000"))


@pytest.fixture(scope="session")
def docker_services(
    docker_compose_command: str,
    docker_compose_file: Any,
    docker_compose_project_name: str,
    docker_setup: Any,
    docker_clean: Any,
) -> Iterator[Services]:
    """Override pytest_docker's fixture to also clean up if setup itself fails.

    Upstream only tears down containers in a `finally` around the *yield*, so a
    failing `up --build --wait` (e.g. a crashing service) leaves containers behind.
    """
    docker_compose = DockerComposeExecutor(
        docker_compose_command, docker_compose_file, docker_compose_project_name,
    )
    try:
        commands = [docker_setup] if isinstance(docker_setup, str) else docker_setup
        for command in commands or []:
            docker_compose.execute(command)
        yield Services(docker_compose)
    finally:
        commands = [docker_clean] if isinstance(docker_clean, str) else docker_clean
        for command in commands or []:
            docker_compose.execute(command)


@pytest.fixture
async def client(aiohttp_client: Any) -> _TestClient:
    """Instantiate server and start it."""
    app = await create_app()
    return await aiohttp_client(app)


def is_responsive(url: str) -> bool:
    """Return true if response from service is 200."""
    url = f"{url}/ping"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == HTTPStatus.OK:
            time.sleep(2)  # sleep extra 2 sec
            return True
    except RequestsConnectionError:
        pass
    return False


@pytest.fixture(scope="session")
def http_service(docker_ip: Any, docker_services: Any) -> Any:
    """Ensure that HTTP service is up and responsive."""
    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("event-service", EVENT_SERVICE_CONTAINER_PORT)
    url = f"http://{docker_ip}:{port}"
    docker_services.wait_until_responsive(
        timeout=30.0,
        pause=0.1,
        check=lambda: is_responsive(url),
    )
    return url


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig: Any) -> Any:
    """Override default location of docker-compose.yml file."""
    return Path(str(pytestconfig.rootdir)) / "docker-compose.yml"


@pytest.fixture(scope="session")
def docker_clean() -> str:
    """Also remove orphaned containers/networks left by a failed setup."""
    return "down -v --remove-orphans"
