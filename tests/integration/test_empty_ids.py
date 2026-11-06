"""Integration test cases for empty ids in adapter URLs.

An empty id turned a URL such as /photos/{id} into /photos/. The services
redirect that to /photos, and the client follows the redirect: a GET got the
list of all photos, and a DELETE could delete every item in the list. Now the
adapters refuse an empty id. See langrenn-sprint/result-service-gui#247.
"""

import pytest
from aiohttp import web

from photo_service_gui.services.albums_adapter import AlbumsAdapter
from photo_service_gui.services.ids import require_id
from photo_service_gui.services.photos_adapter import PhotosAdapter


@pytest.fixture
async def requests(aiohttp_server, monkeypatch: pytest.MonkeyPatch) -> list:
    """Start a fake photo-service and return the requests it gets."""
    received: list[tuple[str, str]] = []

    async def handle(request: web.Request) -> web.Response:
        received.append((request.method, request.path))
        return web.json_response([])

    app = web.Application()
    app.router.add_route("*", "/{tail:.*}", handle)
    server = await aiohttp_server(app)
    url = str(server.make_url("")).rstrip("/")
    services = "photo_service_gui.services"
    monkeypatch.setattr(f"{services}.photos_adapter.PHOTO_SERVICE_URL", url)
    monkeypatch.setattr(f"{services}.albums_adapter.PHOTO_SERVICE_URL", url)
    return received


@pytest.mark.integration
def test_require_id() -> None:
    """An empty id raises, other ids are returned as text."""
    assert require_id("abc") == "abc"
    assert require_id(12) == "12"
    for empty in ["", "  ", None]:
        with pytest.raises(Exception, match="Mangler id"):
            require_id(empty)


@pytest.mark.integration
async def test_get_photo_without_id_is_not_sent(requests: list) -> None:
    """Before, it got the list of all photos."""
    with pytest.raises(Exception, match="Mangler id"):
        await PhotosAdapter().get_photo("t", "")
    assert requests == []


@pytest.mark.integration
async def test_delete_without_id_is_not_sent(requests: list) -> None:
    """Before, the DELETE was sent to the list of all photos or albums."""
    with pytest.raises(Exception, match="Mangler id"):
        await PhotosAdapter().delete_photo("t", "")
    with pytest.raises(Exception, match="Mangler id"):
        await AlbumsAdapter().delete_album("t", "")
    assert requests == []
