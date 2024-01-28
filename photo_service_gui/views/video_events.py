"""Resource module for video_event resources."""
import logging

from aiohttp import web
import aiohttp_jinja2

from photo_service_gui.services import (
    EventsAdapter,
    FotoService,
    PhotosFileAdapter,
    VisionAIService,
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
                    "line_config_file": EventsAdapter().get_global_setting(
                        "LINE_CONFIG_FILE_URL"
                    ),
                    "trigger_line_xyxyn": EventsAdapter().get_global_setting(
                        "TRIGGER_LINE_XYXYN"
                    ),
                    "photo_queue": PhotosFileAdapter().get_all_photo_urls(),
                    "video_url": EventsAdapter().get_global_setting("VIDEO_URL"),
                    "video_analytics_running": EventsAdapter().get_global_setting(
                        "VIDEO_ANALYTICS_RUNNING"
                    ),
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
            logging.debug(f"User: {user}")
            if "pub_message" in form.keys():
                event_id = str(form["event_id"])
                res = await FotoService().push_new_photos_from_file(event_id)
                result += f" {res}"
            elif "video_status" in form.keys():
                result = str(EventsAdapter().get_video_service_status_messages())
            elif "video_analytics_start" in form.keys():
                result = await start_video_analytics()
            elif "video_analytics_stop" in form.keys():
                result = stop_video_analytics()
            elif "update_config" in form.keys():
                event_id = str(form["event_id"])
                informasjon = update_config(form)  # type: ignore
                return web.HTTPSeeOther(
                    location=f"/video_events?event_id={event_id}&informasjon={informasjon}"
                )

        except Exception as e:
            if "401" in str(e):
                result = "401 unathorized: Logg inn for å hente events."
            else:
                result = "Det har oppstått en feil ved henting av video events."
            logging.error(f"Video events update - {e}")
        return web.Response(text=str(result))


async def start_video_analytics() -> str:
    """Start video analytics."""
    result = await VisionAIService().detect_crossings_with_ultraltyics()
    return result


def stop_video_analytics() -> str:
    """Stop video analytics."""
    EventsAdapter().update_global_setting("VIDEO_ANALYTICS_STOP", "true")
    return "Stop video analytics initiert."


def update_config(form: dict) -> str:
    """Draw trigger line with ultraltyics."""
    EventsAdapter().update_global_setting(
        "TRIGGER_LINE_XYXYN", str(form["trigger_line_xyxyn"])
    )
    EventsAdapter().update_global_setting("VIDEO_URL", str(form["video_url"]))
    result = VisionAIService().draw_trigger_line_with_ultraltyics()
    return result
