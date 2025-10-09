"""Utilities module for gui services."""

import logging

from aiohttp_session import get_session, new_session

from photo_service_gui.services import (
    EventsAdapter,
    UserAdapter,
)


async def check_login(self) -> dict:
    """Check login and return user credentials."""
    session = await get_session(self.request)
    loggedin = UserAdapter().isloggedin(session)
    if not loggedin:
        informasjon = "Logg inn for å se denne siden"
        raise Exception(informasjon)

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
