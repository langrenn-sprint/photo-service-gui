"""Utilities module for gui services."""
import logging

from aiohttp import web
from aiohttp_session import get_session, new_session

from photo_service_gui.services import (
    EventsAdapter,
    GooglePhotosAdapter,
    UserAdapter,
)


async def get_auth_url_google_photos(self, redirect_url: str, event_id: str) -> str:
    """Check authorization for google photos and return url - blank if authorized."""
    session = await get_session(self.request)
    authorized = UserAdapter().isloggedin_google_photos(session)
    if not authorized:
        authorization_request_url = await GooglePhotosAdapter().get_auth_request_url(
            redirect_url, event_id
        )
    else:
        authorization_request_url = ""
    return authorization_request_url


async def login_google_photos(
    self, redirect_url: str, event_id: str, user: dict
) -> int:
    """Check scope authorization for google photos and store in session."""
    session = await new_session(self.request)
    result = UserAdapter().login_google_photos(redirect_url, event_id, user, session)
    return result


async def check_login(self) -> dict:
    """Check login and return user credentials."""
    session = await get_session(self.request)
    loggedin = UserAdapter().isloggedin(session)
    if not loggedin:
        informasjon = "Logg inn for å se denne siden"
        raise web.HTTPSeeOther(location=f"/login?informasjon={informasjon}")  # type: ignore

    return {
        "name": session["name"],
        "loggedin": True,
        "token": session["token"],
        "g_loggedin": session["g_loggedin"],
        "g_name": session["g_name"],
        "g_jwt": session["g_jwt"],
        "g_auth_photos": session["g_auth_photos"],
        "g_scope": session["g_scope"],
        "g_client_id": session["g_client_id"],
        "g_photos_token": session["g_photos_token"],
    }


async def check_login_google(self, event_id: str) -> dict:
    """Check login with google and return user credentials."""
    session = await get_session(self.request)
    loggedin = UserAdapter().isloggedin_google(session)
    if not loggedin:
        informasjon = "informasjon=Logg inn med google for å se denne siden."
        info = f"action=g_login&event_id={event_id}"
        raise Exception(f"/login?{info}&{informasjon}")

    return {
        "name": session["name"],
        "loggedin": loggedin,
        "token": session["token"],
        "g_loggedin": session["g_loggedin"],
        "g_name": session["g_name"],
        "g_jwt": session["g_jwt"],
        "g_auth_photos": session["g_auth_photos"],
        "g_scope": session["g_scope"],
        "g_client_id": session["g_client_id"],
        "g_photos_token": session["g_photos_token"],
    }


async def check_login_google_photos(self, event_id: str) -> dict:
    """Check login with google and return user credentials."""
    session = await get_session(self.request)
    loggedin = UserAdapter().isloggedin_google_photos(session)
    if not loggedin:
        informasjon = "informasjon=Logg inn med google for å se denne siden."
        info = f"action=g_login&event_id={event_id}"
        raise Exception(f"/login?{info}&{informasjon}")

    return {
        "name": session["name"],
        "loggedin": loggedin,
        "token": session["token"],
        "g_loggedin": session["g_loggedin"],
        "g_name": session["g_name"],
        "g_jwt": session["g_jwt"],
        "g_auth_photos": session["g_auth_photos"],
        "g_scope": session["g_scope"],
        "g_client_id": session["g_client_id"],
        "g_photos_token": session["g_photos_token"],
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
        logging.debug(f"get_event {event_id}")
        event = await EventsAdapter().get_event(user["token"], event_id)

    return event
