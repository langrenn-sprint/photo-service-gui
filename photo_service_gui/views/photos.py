"""Resource module for photo edit view."""

import logging

import aiohttp_jinja2
from aiohttp import web

from photo_service_gui.services import EventsAdapter, GoogleCloudStorageAdapter

from .utils import (
    check_login,
    get_event,
)


class Photos(web.View):

    """Class representing the photos edit view."""

    async def get(self) -> web.Response:
        """Get route function that return the dashboards page."""
        try:
            action = self.request.rel_url.query["action"]
        except Exception:
            action = ""
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
            photos = GoogleCloudStorageAdapter().list_blobs(
                event_id, "",
            )
            photos.reverse()

            return await aiohttp_jinja2.render_template_async(
                "photos.html",
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
        form = dict(await self.request.post())
        event_id = str(form["event_id"])
        user = await check_login(self)
        if not user:
                informasjon = "Ingen tilgang, vennligst logg inn på nytt."
                return web.HTTPSeeOther(
                    location=f"/login?informasjon={informasjon}",
                )

        try:
            if "delete_all_local" in form:
                informasjon = "TODO: Sletting av alle lokale kopier."
            elif "delete_select" in form:
                informasjon = "Sletting utført: "
                for key, value in form.items():
                    if key.startswith("delete_photo"):
                        photo_name = str(value)
                        result = GoogleCloudStorageAdapter().delete_blob(photo_name)
                        logging.debug(f"Deleted photo - {result}")
                        informasjon += f"{key} "
        except Exception as e:
            logging.exception("Error")
            informasjon = f"Det har oppstått en feil - {e.args}."
            error_reason = str(e)
            if error_reason.startswith("401"):
                informasjon = f"Ingen tilgang, vennligst logg inn på nytt. {e}"
                return web.HTTPSeeOther(
                    location=f"/login?informasjon={informasjon}",
                )

        return web.HTTPSeeOther(
            location=f"/photos?event_id={event_id}&informasjon={informasjon}",
        )
