"""Resource module for photo push view."""
import logging

from aiohttp import web
import aiohttp_jinja2

from photo_service_gui.services import EventsAdapter, FotoService, PhotosFileAdapter
from .utils import (
    check_login,
    get_event,
)


class PhotoPush(web.View):
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
            user = await check_login(self)
        except Exception as e:
            return web.HTTPSeeOther(location=f"{e}")
        try:
            event = await get_event(user, event_id)
            # check if automatic sync is active
            try:
                if action in ["auto_sync", "one_sync"]:
                    # Todo: check if automatic sync is active
                    logging.debug(f"Action: {action}")
            except Exception as e:
                informasjon = f"Det har oppstått en feil ved synkronisering. {e}"
                action = ""
            photos = PhotosFileAdapter().get_all_photos()
            return await aiohttp_jinja2.render_template_async(
                "photo_push.html",
                self.request,
                {
                    "lopsinfo": "",
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
            logging.error(f"Error: {e}. Redirect to main page.")
            return web.HTTPSeeOther(location=f"/?informasjon={e}")

    async def post(self) -> web.Response:
        """Post route function that updates a collection of klasses."""
        action = "photo_push"
        informasjon = ""
        form = await self.request.post()
        event_id = str(form["event_id"])
        user = await check_login(self)

        try:
            if "photo_push" in form.keys():
                # push photos to album, analyze and create event - finally move photos to archive
                informasjon = await FotoService().push_new_photos_from_file(event_id)
        except Exception as e:
            error_reason = str(e)
            if error_reason.startswith("401"):
                return web.HTTPSeeOther(
                    location=f"/login?informasjon=Ingen tilgang, vennligst logg inn på nytt. {e}"
                )
            else:
                logging.error(f"Error: {e}")
                informasjon = (
                    f"Det har oppstått en feil - {e.args}. Bruker: {user['name']}"
                )

        return web.HTTPSeeOther(
            location=f"/photo_push?event_id={event_id}&informasjon={informasjon}&action={action}"
        )
