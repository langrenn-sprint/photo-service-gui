"""Resource module for photo admin view."""

import logging
from http import HTTPStatus

from aiohttp import web

from .utils import (
    check_login_google,
    get_auth_url_google_photos,
    get_event,
    login_google_photos,
)

WEBSERVER_PHOTO_URL = "http://localhost:8080/photos_adm"


class PhotosAdm(web.View):

    """Class representing the photo admin view."""

    async def get(self) -> web.Response:
        """Get route function that return the dashboards page."""
        try:
            event_id = self.request.rel_url.query["event_id"]
        except Exception:
            event_id = ""
        try:
            user = await check_login_google(self, event_id)
            event = await get_event(user, event_id)
        except Exception as e:
            return web.HTTPSeeOther(location=f"{e}")
        try:
            action = self.request.rel_url.query["action"]
        except Exception:
            action = ""

        try:
            if not user["g_auth_photos"]:
                if not event_id:
                    # handle authorization response from google photo
                    event_id = self.request.rel_url.query["state"]
                    user["g_scope"] = self.request.rel_url.query["scope"]
                    user["g_client_id"] = self.request.rel_url.query["code"]
                    result = await login_google_photos(
                        self, WEBSERVER_PHOTO_URL, event, user,
                    )
                    if result == HTTPStatus.OK:
                        # reload user session information
                        user = await check_login_google(self, event_id)
                    else:
                        raise_auth_error(result)
                else:
                    # initiate authorization for google photo
                    auth_url = await get_auth_url_google_photos(
                        self, user["token"], event, WEBSERVER_PHOTO_URL,
                    )
                    if auth_url:
                        return web.HTTPSeeOther(location=f"{auth_url}")
            # authenticated ok send to sync page
            if action == "photo_push":
                return web.HTTPSeeOther(location=f"photo_push?event_id={event_id}")
            return web.HTTPSeeOther(location=f"photo_sync?event_id={event_id}")

        except Exception as e:
            logging.exception("Error. Redirect to main page.")
            return web.HTTPSeeOther(location=f"/?informasjon={e}")

def raise_auth_error(result) -> None:
    """Raise error message."""
    err_msg = f"Feil med google autorisasjon - {result}"
    raise Exception(err_msg)
