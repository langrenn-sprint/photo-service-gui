"""Resource module for video_event resources."""
import logging

from aiohttp import web
import aiohttp_jinja2

from photo_service_gui.services import (
    GooglePubSubAdapter,
)
from .utils import (
    check_login,
    get_event,
)


class VideoEvents(web.View):
    """Class representing the video_event view."""

    async def get(self) -> web.Response:
        """Get route function that return the video_eventlister page."""
        event_id = self.request.rel_url.query["event_id"]
        try:
            informasjon = self.request.rel_url.query["informasjon"]
        except Exception:
            informasjon = ""
        try:
            user = await check_login(self)
            event = await get_event(user, event_id)

            """Get route function."""
            return await aiohttp_jinja2.render_template_async(
                "video_events.html",
                self.request,
                {
                    "event": event,
                    "event_id": event_id,
                    "informasjon": informasjon,
                    "username": user["name"],
                },
            )
        except Exception as e:
            logging.error(f"Error: {e}. Redirect to main page.")
            return web.HTTPSeeOther(location=f"/?informasjon={e}")

    async def post(self) -> web.Response:
        """Post route function that updates video events."""
        try:
            result = ""
            form = await self.request.post()
            user = await check_login(self)
            if user["name"] == "":
                raise Exception("401 unathorized: Logg inn for å hente events.")
            if "pub_message" in form.keys() :
                pub_message = str(form["pub_message"])
                result = await GooglePubSubAdapter().publish_message(
                    pub_message
                )
            elif "pull_message" in form.keys():
                result = str(await GooglePubSubAdapter().pull_messages())
        except Exception as e:
            if "401" in str(e):
                result = "401 unathorized: Logg inn for å hente events."
            else:
                result = "Det har oppstått en feil ved henting av video events."
            logging.error(f"Video events update - {e}")
        return web.Response(text=str(result))
