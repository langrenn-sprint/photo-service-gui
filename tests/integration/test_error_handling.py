"""Integration test cases for error handling in the views.

See langrenn-sprint/result-service-gui#240. A user who is not logged in, or
whose login has expired (401), is sent to the login page. Other errors send
the user to the main page with an understandable message. If the main page
itself fails, an error page is shown. An event without organiser does not
break the pages.
"""

from http import HTTPStatus
from typing import Any

import pytest
from aiohttp import web
from yarl import URL

from photo_service_gui.services import EventsAdapter
from photo_service_gui.views.utils import (
    LOGIN_AGAIN,
    LOGIN_REQUIRED,
    UNEXPECTED_ERROR,
    error_text,
    is_login_error,
    raise_error,
)

EVENT = {
    "id": "e1",
    "name": "Test",
    "date_of_event": "2026-11-06",
    "time_of_event": "12:00:00",
    "organiser": "Lyn Ski",
}
USER = {"name": "tester", "loggedin": True, "token": "t"}


def location(resp: Any) -> tuple[str, dict]:
    """Path and query of the redirect target."""
    url = URL(resp.headers["Location"])
    return url.path, dict(url.query)


@pytest.fixture
def config_page(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Log in on the settings page, and let get_event raise .error."""

    class State:
        error: Exception = TypeError("'NoneType' object is not subscriptable")

    state = State()

    async def fake_check_login(*_: Any) -> dict:
        return USER

    async def fake_get_event(*_: Any) -> dict:
        raise state.error

    views = "photo_service_gui.views.config"
    monkeypatch.setattr(f"{views}.check_login", fake_check_login)
    monkeypatch.setattr(f"{views}.get_event", fake_get_event)
    return state


@pytest.fixture
def main_page(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Run the main page with no backend: .event, or the error set in .error."""

    class State:
        error: Exception | None = None
        event: dict = EVENT

    state = State()

    async def get_all_events(*_: Any) -> list:
        if state.error:
            raise state.error
        return []

    async def get_event(*_: Any) -> dict:
        return state.event

    monkeypatch.setattr(EventsAdapter, "get_all_events", get_all_events)
    monkeypatch.setattr("photo_service_gui.views.main.get_event", get_event)
    return state


# --- error_text and is_login_error ----------------------------------------------------


@pytest.mark.integration
def test_error_text() -> None:
    """Messages are shown, programming errors give a general message."""
    assert error_text(Exception("Albumet finnes ikke")) == (
        "Det har oppstått en feil: Albumet finnes ikke"
    )
    assert error_text(web.HTTPBadRequest(reason="Error - 404: Not found.")) == (
        "Det har oppstått en feil: Error - 404: Not found."
    )
    assert error_text(TypeError("'NoneType' object is not subscriptable")) == (
        UNEXPECTED_ERROR
    )


@pytest.mark.integration
def test_is_login_error() -> None:
    """The ways the adapters report 401."""
    assert is_login_error(web.HTTPBadRequest(reason="401 Unathorized - get_event"))
    assert is_login_error(Exception("401 Unauthorized - get_albums"))
    assert is_login_error(Exception("Login expired: <ClientResponse 401>"))
    assert not is_login_error(Exception("Albumet finnes ikke"))


@pytest.mark.integration
def test_raise_error_lets_redirects_through() -> None:
    """A redirect raised in the view, e.g. to the login page, passes through."""
    redirect = web.HTTPSeeOther(location="/login?informasjon=Logg+inn")

    class View:
        request = None

    with pytest.raises(web.HTTPSeeOther) as e:
        raise_error(View(), redirect)  # type: ignore[arg-type]
    assert e.value is redirect


# --- Not logged in --------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("page", ["/config?event_id=e1", "/photos", "/status"])
async def test_not_logged_in_sends_to_login_page(client: Any, page: str) -> None:
    """Before, /photos and /status redirected to the error text as a URL."""
    resp = await client.get(page, allow_redirects=False)
    assert resp.status == HTTPStatus.SEE_OTHER
    assert location(resp) == ("/login", {"informasjon": LOGIN_REQUIRED})


# --- A page that fails ----------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize(
    ("error", "message"),
    [
        (TypeError("'NoneType' object is not subscriptable"), UNEXPECTED_ERROR),
        (
            Exception("Albumet finnes ikke"),
            "Det har oppstått en feil: Albumet finnes ikke",
        ),
        (
            web.HTTPBadRequest(reason="Error - 404: Event not found."),
            "Det har oppstått en feil: Error - 404: Event not found.",
        ),
    ],
)
async def test_error_sends_to_main_page_with_message(
    client: Any, config_page: Any, error: Exception, message: str,
) -> None:
    """Not to the login page, as before."""
    config_page.error = error
    resp = await client.get("/config?event_id=e1", allow_redirects=False)
    assert resp.status == HTTPStatus.SEE_OTHER
    assert location(resp) == ("/", {"informasjon": message})


@pytest.mark.integration
async def test_expired_login_sends_to_login_page(client: Any, config_page: Any) -> None:
    """401 from a backend service sends the user to the login page."""
    config_page.error = web.HTTPBadRequest(reason="401 Unathorized - get_event")
    resp = await client.get("/config?event_id=e1", allow_redirects=False)
    assert resp.status == HTTPStatus.SEE_OTHER
    assert location(resp) == ("/login", {"informasjon": LOGIN_AGAIN})


# --- The main page --------------------------------------------------------------------


@pytest.mark.integration
async def test_main_page_error_shows_error_page(client: Any, main_page: Any) -> None:
    """The other pages send errors to the main page, so it does not redirect."""
    main_page.error = TypeError("'NoneType' object is not subscriptable")
    resp = await client.get("/", allow_redirects=False)
    assert resp.status == HTTPStatus.INTERNAL_SERVER_ERROR
    text = await resp.text()
    assert UNEXPECTED_ERROR in text
    assert 'href="/logout"' in text


@pytest.mark.integration
async def test_main_page_expired_login_sends_to_login_page(
    client: Any, main_page: Any,
) -> None:
    """401 on the main page sends the user to the login page."""
    main_page.error = Exception("401 Unathorized - get_all_events")
    resp = await client.get("/", allow_redirects=False)
    assert resp.status == HTTPStatus.SEE_OTHER
    assert location(resp)[0] == "/login"


# --- Event without organiser ----------------------------------------------------------


@pytest.mark.integration
async def test_event_without_organiser(client: Any, main_page: Any) -> None:
    """Organiser is optional in event-service; the page uses the neutral style."""
    main_page.event = {**EVENT, "organiser": None}
    resp = await client.get("/", allow_redirects=False)
    assert resp.status == HTTPStatus.OK
    assert "styles_whitelabel.css" in await resp.text()
