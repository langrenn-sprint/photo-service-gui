"""Resource module for main view."""
import logging

from aiohttp import web
import aiohttp_jinja2

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
            logging.error(f"Error: {e}. Redirect to login page.")
            return web.HTTPSeeOther(location=f"/login?informasjon={e}")

    async def post(self) -> web.Response:
        """Post route function."""
        informasjon = ""
        form = await self.request.post()
        user = await check_login(self)
        try:
            if "get_events" in form.keys():
                serverUrl = form["serverUrl"]
                informasjon = await EventsAdapter().sync_events(user["token"], serverUrl)  # type: ignore
            elif "json_events" in form.keys():
                informasjon = await EventsAdapter().create_events_json(user["token"], form["eventsJson"])  # type: ignore
            elif "delete_event" in form.keys():
                informasjon = await EventsAdapter().delete_event(user["token"], form["event_id"])  # type: ignore
        except Exception as e:
            error_reason = str(e)
            if error_reason.startswith("401"):
                return web.HTTPSeeOther(
                    location=f"/login?informasjon=Ingen tilgang, vennligst logg inn på nytt. {e}"
                )
            else:
                logging.error(f"Error: {e}")
                informasjon = f"Det har oppstått en feil - {e.args}. Bruker: {user['name']}"

        return web.HTTPSeeOther(location=f"/?informasjon={informasjon}")
