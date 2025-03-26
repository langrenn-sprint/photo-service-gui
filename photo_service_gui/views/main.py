"""Resource module for main view."""

import logging

import aiohttp_jinja2
from aiohttp import web

from photo_service_gui.services import EventsAdapter

from .utils import check_login, check_login_open, get_event


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
            logging.exception("Error. Redirect to login page.")
            return web.HTTPSeeOther(location=f"/login?informasjon={e}")

    async def post(self) -> web.Response:
        """Post route function."""
        informasjon = ""
        form = await self.request.post()
        user = await check_login(self)
        try:
            if "get_events" in form:
                server_url = str(form["server_url"])
                informasjon = await EventsAdapter().sync_events(
                    user["token"], server_url,
                )
            elif "delete_event" in form:
                informasjon = await EventsAdapter().delete_event(
                    user["token"], form["event_id"],  # type: ignore[no-untyped-call]
                )
        except Exception as e:
            error_reason = str(e)
            if error_reason.startswith("401"):
                return web.HTTPSeeOther(
                    location=f"/login?informasjon=Vennligst logg inn på nytt. {e}",
                )
            logging.exception("Error")
            informasjon = (
                f"Det har oppstått en feil - {e.args}. Bruker: {user['name']}"
            )

        return web.HTTPSeeOther(location=f"/?informasjon={informasjon}")
