"""Utilities module for gui services."""

import logging
from typing import NoReturn
from urllib.parse import urlencode

from aiohttp import web
from aiohttp_session import get_session, new_session

from photo_service_gui.services import (
    EventsAdapter,
    UserAdapter,
)

UNEXPECTED_ERROR = "Det har oppstått en uventet feil. Feilen er logget."
LOGIN_AGAIN = "Innloggingen er utløpt. Logg inn på nytt."
LOGIN_REQUIRED = "Logg inn for å se denne siden"


def login_location(informasjon: str) -> str:
    """Return the login page URL, with a message."""
    return f"/login?{urlencode({'informasjon': informasjon})}"


def is_login_error(e: Exception) -> bool:
    """Return True if the error is a missing or expired login (401).

    The adapters report 401 as "401 Unathorized - …", "401 Unauthorized - …"
    or "Login expired: …".
    """
    text = str(e.reason) if isinstance(e, web.HTTPException) else str(e)
    return text.startswith("401") or "Login expired" in text


def error_text(e: Exception) -> str:
    """Return a message for the user about an error.

    Errors from our own code (plain Exception) and from the backend services
    (HTTP errors from the adapters) carry a message for the user. Other errors,
    e.g. TypeError, are programming errors: the user gets a general message,
    and the details are only logged.
    """
    if isinstance(e, web.HTTPException):
        return f"Det har oppstått en feil: {e.reason}"
    if type(e) is Exception:
        return f"Det har oppstått en feil: {e}"
    return UNEXPECTED_ERROR


def raise_error(view: web.View, e: Exception, location: str = "/") -> NoReturn:
    """Handle an error in a view: log it, and send the user on with a message.

    Redirects raised in the view, e.g. to the login page, pass through. A
    missing or expired login sends the user to the login page. Any other error
    sends the user to `location` with a message: the user is still logged in.
    """
    if isinstance(e, web.HTTPRedirection):
        raise e
    request = view.request
    logging.error("Error in %s %s", request.method, request.path_qs, exc_info=e)
    if is_login_error(e):
        raise web.HTTPSeeOther(location=login_location(LOGIN_AGAIN)) from e
    query = urlencode({"informasjon": error_text(e)})
    raise web.HTTPSeeOther(location=f"{location}?{query}") from e


async def check_login(self) -> dict:
    """Check login and return user credentials.

    A user that is not logged in is sent to the login page.
    """
    session = await get_session(self.request)
    loggedin = UserAdapter().isloggedin(session)
    if not loggedin:
        raise web.HTTPSeeOther(location=login_location(LOGIN_REQUIRED))

    return {
        "name": session["name"],
        "loggedin": True,
        "token": session["token"],
    }


async def check_login_open(self) -> dict:
    """Check login and return credentials."""
    user = {}
    session = await get_session(self.request)
    loggedin = UserAdapter().isloggedin(session)
    if loggedin:
        user = {
            "name": session["name"],
            "loggedin": True,
            "token": session["token"],
        }
    else:
        user = {"name": "Gjest", "loggedin": False, "token": ""}

    return user


async def get_event(user: dict, event_id: str) -> dict:
    """Get event - return new if no event found."""
    event = {"id": event_id, "name": "Langrenn-sprint", "organiser": "Ikke valgt"}
    if event_id:
        logging.info(f"get_event {event_id}")
        event = await EventsAdapter().get_event(user["token"], event_id)

    return event
