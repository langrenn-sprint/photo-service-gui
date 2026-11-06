"""Resource module for main view."""

import logging

import aiohttp_jinja2
from aiohttp import web

from photo_service_gui.services import EventsAdapter

from .utils import (
    check_login,
    check_login_open,
    error_message,
    error_text,
    get_event,
    is_login_error,
    raise_error,
)


class Main(web.View):

    """Class representing the main view."""

    async def get(self) -> web.Response:
        """Get function that return the index page."""
        try:
            informasjon = self.request.rel_url.query["informasjon"]
        except Exception:
            informasjon = ""

        try:
            reload = self.request.rel_url.query["reload"]
        except Exception:
            reload = ""

        try:
            user = await check_login_open(self)
            event = await get_event(user, "")

            events = await EventsAdapter().get_all_events(user["token"])

            return await aiohttp_jinja2.render_template_async(
                "index.html",
                self.request,
                {
                    "lopsinfo": "Langrenn-sprint",
                    "event": event,
                    "event_id": "",
                    "events": events,
                    "informasjon": informasjon,
                    "reload": reload,
                    "username": user["name"],
                },
            )
        except Exception as e:
            if is_login_error(e):
                raise_error(self, e)
            # The other pages send errors here, so show an error page instead:
            logging.exception("Error on the main page")
            return await aiohttp_jinja2.render_template_async(
                "error.html",
                self.request,
                {"informasjon": error_text(e)},
                status=web.HTTPInternalServerError.status_code,
            )

    async def post(self) -> web.Response:
        """Post route function."""
        informasjon = ""
        form = await self.request.post()
        user = await check_login(self)
        try:
            if "get_events" in form:
                server_url = str(form["server_url"])
                informasjon = await EventsAdapter().sync_events(
                    user["token"],
                    server_url,
                )
            elif "delete_event" in form:
                informasjon = await EventsAdapter().delete_event(
                    user["token"],
                    form["event_id"],  # type: ignore[no-untyped-call]
                )
        except Exception as e:
            informasjon = error_message(self, e)

        raise web.HTTPSeeOther(location=f"/?informasjon={informasjon}")
