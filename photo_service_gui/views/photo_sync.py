"""Resource module for photo edit view."""

import logging

import aiohttp_jinja2
from aiohttp import web

from photo_service_gui.services import EventsAdapter, FotoService, GooglePhotosAdapter

from .utils import (
    check_login_google_photos,
    get_event,
)


class PhotoSync(web.View):
    """Class representing the photo edit view."""

    async def get(self) -> web.Response:
        """Get route function that return the dashboards page."""
        try:
            event_id = self.request.rel_url.query["event_id"]
        except Exception:
            event_id = ""
        try:
            informasjon = self.request.rel_url.query["informasjon"]
        except Exception:
            informasjon = ""
        try:
            action = self.request.rel_url.query["action"]
        except Exception:
            action = ""
        try:
            user = await check_login_google_photos(self, event_id)
        except Exception as e:
            return web.HTTPSeeOther(location=f"{e}")

        try:
            event = await get_event(user, event_id)
            g_albums = await GooglePhotosAdapter().get_albums(
                user["token"], event, user["g_photos_token"]
            )
            return await aiohttp_jinja2.render_template_async(
                "photo_sync.html",
                self.request,
                {
                    "lopsinfo": "",
                    "action": action,
                    "g_albums": g_albums,
                    "event": event,
                    "event_id": event_id,
                    "informasjon": informasjon,
                    "local_time_now": EventsAdapter().get_local_time(event, "HH:MM"),
                    "username": user["name"],
                },
            )
        except Exception as e:
            logging.exception("Error. Redirect to main page.")
            return web.HTTPSeeOther(location=f"/?informasjon={e}")

    async def post(self) -> web.Response:
        """Post route function that updates a collection of klasses."""
        action = ""
        informasjon = ""
        form = await self.request.post()
        event_id = str(form["event_id"])
        user = await check_login_google_photos(self, event_id)
        album_id = str(form["album_id"])
        album_title = str(form["album_title"])
        logging.info(f"Form {form}")

        try:
            if "sync_from_google" in form:
                # the actual sync is done on get-processing
                try:
                    action = str(form["action"])
                    if action == "auto_sync":
                        informasjon = "Autosynk er på."
                except Exception:
                    action = "one_sync"
        except Exception as e:
            logging.exception("Error")
            informasjon = f"Det har oppstått en feil - {e.args}. Bruker: {user['name']}"
            error_reason = str(e)
            if error_reason.startswith("401"):
                return web.HTTPSeeOther(
                    location=f"/login?informasjon=Vennligst logg inn på nytt. {e}"
                )

        info = (
            f"album_id={album_id}&album_title={album_title}&informasjon={informasjon}"
        )
        return web.HTTPSeeOther(
            location=f"/photo_sync?event_id={event_id}&{info}&action={action}"
        )
