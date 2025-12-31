"""Resource module for photo edit view."""

import logging

import aiohttp_jinja2
from aiohttp import web

from photo_service_gui.services import EventsAdapter, StatusAdapter

from .utils import (
    check_login,
    get_event,
)


class Status(web.View):

    """Class representing the status edit view."""

    async def get(self) -> web.Response:
        """Get route function that return the dashboards page."""
        try:
            action = self.request.rel_url.query["action"]
        except Exception:
            action = ""
        try:
            count = int(self.request.rel_url.query["count"])
        except Exception:
            count = 50
        try:
            my_filter = self.request.rel_url.query["filter"]
        except Exception:
            my_filter = ""
        logging.debug(f"Action: {action}, Filter: {my_filter}")
        try:
            event_id = self.request.rel_url.query["event_id"]
        except Exception:
            event_id = ""
        try:
            informasjon = self.request.rel_url.query["informasjon"]
        except Exception:
            informasjon = ""
        try:
            user = await check_login(self)
        except Exception as e:
            return web.HTTPSeeOther(location=f"{e}")

        try:
            event = await get_event(user, event_id)
            status = []
            if my_filter:
                status = await StatusAdapter().get_status_by_type(
                    user["token"], event, my_filter, count,
                )
            else:
                status = await StatusAdapter().get_status(
                    user["token"], event["id"], count,
                )

            return await aiohttp_jinja2.render_template_async(
                "status.html",
                self.request,
                {
                    "lopsinfo": "Status detaljer",
                    "action": action,
                    "event": event,
                    "event_id": event_id,
                    "filter": my_filter,
                    "informasjon": informasjon,
                    "status": status,
                    "username": user["name"],
                },
            )
        except Exception as e:
            logging.exception("Error. Redirect to main page.")
            return web.HTTPSeeOther(location=f"/?informasjon={e}")

    async def post(self) -> web.Response:
        """Post route function that updates a collection of status."""
        informasjon = ""
        form = dict(await self.request.post())
        event_id = str(form["event_id"])
        user = await check_login(self)
        if not user:
                informasjon = "Ingen tilgang, vennligst logg inn på nytt."
                return web.HTTPSeeOther(
                    location=f"/login?informasjon={informasjon}",
                )
        event = await get_event(user, event_id)

        try:
            if "delete_all" in form:
                informasjon = await StatusAdapter().delete_all_status(
                    user["token"], event,
                )
            elif "delete_select" in form:
                informasjon = "Funksjon ikke implementert ennå."
        except Exception as e:
            logging.exception("Error")
            informasjon = f"Det har oppstått en feil - {e.args}."
            error_reason = str(e)
            if error_reason.count("401 Unauthorized") > 0   :
                informasjon = "401 Unauthorized - Ingen tilgang, logg inn på nytt."
                return web.HTTPSeeOther(
                    location=f"/login?informasjon={informasjon}",
                )
        return web.HTTPSeeOther(
            location=f"/status?event_id={event_id}&action=delete_select&informasjon={informasjon}",
        )
