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

    def _delete_photos(self, form: dict) -> tuple[str, str]:
        """Delete selected photos."""
        informasjon = "Sletting utført: "
        error_text = ""
        for key, value in form.items():
            if key.startswith("edit_photo"):
                photo_name = str(value)
                result = GoogleCloudStorageAdapter().delete_blob(photo_name)
                logging.debug(f"Deleted photo - {result}")
                informasjon += f"{key} "
        return informasjon, error_text

    def _move_photos_to_capture(self, form: dict) -> tuple[str, str]:
        """Move selected photos from archive to capture (inbox)."""
        informasjon = "Flytting til innboks utført: "
        error_text = ""
        for key, value in form.items():
            if key.startswith("edit_photo"):
                photo_name = str(value)
                if "/DETECT_ARCHIVE/" in photo_name:
                    new_photo_name = photo_name.replace(
                        "/DETECT_ARCHIVE/",
                        "/DETECT/",
                    )
                    result = GoogleCloudStorageAdapter().move_blob(
                        photo_name,
                        new_photo_name,
                    )
                    logging.debug(f"Moved photo to capture - {result}")
                    informasjon += f"{key}. "
                else:
                    error_text += f" {key}. "
        return informasjon, error_text

    def _move_photos_to_archive(self, form: dict) -> tuple[str, str]:
        """Move selected photos from capture (inbox) to archive."""
        informasjon = "Flytting til arkiv utført: "
        error_text = ""
        for key, value in form.items():
            if key.startswith("edit_photo"):
                photo_name = str(value)
                if "/DETECT/" in photo_name:
                    new_photo_name = photo_name.replace(
                        "/DETECT/",
                        "/DETECT_ARCHIVE/",
                    )
                    result = GoogleCloudStorageAdapter().move_blob(
                        photo_name,
                        new_photo_name,
                    )
                    logging.debug(f"Moved photo to archive - {result}")
                    informasjon += f"{key}. "
                else:
                    error_text += f" {key}. "
        return informasjon, error_text

    async def get(self) -> web.Response:
        """Get route function that return the dashboards page."""
        try:
            action = self.request.rel_url.query["action"]
        except Exception:
            action = ""
        try:
            photo_type = self.request.rel_url.query["photo_type"]
        except Exception:
            photo_type = ""
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

            if photo_type:
                photos = [photo for photo in photos if photo_type in photo["name"]]

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
                    "photo_type": photo_type,
                    "username": user["name"],
                },
            )
        except Exception as e:
            logging.exception("Error. Redirect to main page.")
            return web.HTTPSeeOther(location=f"/?informasjon={e}")

    async def post(self) -> web.Response:
        """Post route function that updates a collection of photos."""
        form = dict(await self.request.post())
        event_id = str(form["event_id"])
        user = await check_login(self)

        if not user:
            informasjon = "Ingen tilgang, vennligst logg inn på nytt."
            return web.HTTPSeeOther(
                location=f"/login?informasjon={informasjon}",
            )

        try:
            if "delete_select" in form:
                informasjon, error_text = self._delete_photos(form)
            elif "move_to_capture" in form:
                informasjon, error_text = self._move_photos_to_capture(form)
            elif "move_to_archive" in form:
                informasjon, error_text = self._move_photos_to_archive(form)
            else:
                informasjon, error_text = "", ""

            if error_text:
                informasjon += f"Feil (ulovlig flytting): {error_text}"

        except Exception as e:
            logging.exception("Error")
            informasjon = f"Det har oppstått en feil - {e.args}."
            if "401 Unauthorized" in str(e):
                informasjon = "401 Unauthorized - Ingen tilgang, logg inn på nytt."
                return web.HTTPSeeOther(
                    location=f"/login?informasjon={informasjon}",
                )

        return web.HTTPSeeOther(
            location=f"/photos?event_id={event_id}&informasjon={informasjon}",
        )
