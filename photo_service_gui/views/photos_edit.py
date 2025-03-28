"""Resource module for photo edit view."""

import logging

import aiohttp_jinja2
from aiohttp import web

from photo_service_gui.services import EventsAdapter, FotoService, PhotosAdapter

from .utils import (
    check_login_google_photos,
    get_event,
)


class PhotosEdit(web.View):

    """Class representing the photos edit view."""

    async def get(self) -> web.Response:
        """Get route function that return the dashboards page."""
        try:
            action = self.request.rel_url.query["action"]
        except Exception:
            action = ""
        try:
            event_id = self.request.rel_url.query["event_id"]
        except Exception:
            event_id = ""
        try:
            informasjon = self.request.rel_url.query["informasjon"]
        except Exception:
            informasjon = ""
        try:
            user = await check_login_google_photos(self, event_id)
        except Exception as e:
            return web.HTTPSeeOther(location=f"{e}")

        try:
            event = await get_event(user, event_id)
            photos = await PhotosAdapter().get_all_photos(
                user["token"], event_id,
            )

            return await aiohttp_jinja2.render_template_async(
                "photos_edit.html",
                self.request,
                {
                    "lopsinfo": "Foto redigering",
                    "action": action,
                    "event": event,
                    "event_id": event_id,
                    "informasjon": informasjon,
                    "local_time_now": EventsAdapter().get_local_time(event, "HH:MM"),
                    "photos": photos,
                    "username": user["name"],
                },
            )
        except Exception as e:
            logging.exception("Error. Redirect to main page.")
            return web.HTTPSeeOther(location=f"/?informasjon={e}")

    async def post(self) -> web.Response:
        """Post route function that updates a collection of photos."""
        informasjon = ""
        form = {}
        event_id = ""

        try:
            form = await self.request.post()
            event_id = str(form["event_id"])
            user = await check_login_google_photos(self, event_id)
            if "update_race_info" in form:
                informasjon = await FotoService().update_race_info(
                    user["token"], event_id, dict(form),
                )
            elif "delete_all_local" in form:
                informasjon = await FotoService().delete_all_local_photos(
                    user["token"], event_id,
                )
        except Exception as e:
            logging.exception("Error")
            informasjon = f"Det har oppstått en feil - {e.args}."
            error_reason = str(e)
            if error_reason.startswith("401"):
                informasjon = "Ingen tilgang, vennligst logg inn på nytt."
                return web.HTTPSeeOther(
                    location=f"/login?informasjon={informasjon}",
                )

        return web.HTTPSeeOther(
            location=f"/photos_edit?event_id={event_id}&informasjon={informasjon}",
        )
