"""Resource module for video_event resources."""
import logging

from aiohttp import web
import aiohttp_jinja2

from photo_service_gui.services import (
    EventsAdapter,
    FotoService,
    PhotosFileAdapter,
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
            if "update_config" in form.keys():
                event_id = str(form["event_id"])
                informasjon = update_config(form)  # type: ignore
                return web.HTTPSeeOther(
                    location=f"/video_events?event_id={event_id}&informasjon={informasjon}"
                )
            if "pub_message" in form.keys():
                event_id = str(form["event_id"])
                res = await FotoService().push_new_photos_from_file(event_id)
                result = f" {res}"
            if "video_analytics_start" in form.keys():
                event_id = str(form["event_id"])
                result = start_video_analytics(event_id)
            if "video_analytics_stop" in form.keys():
                result = stop_video_analytics()
            if "video_status" in form.keys():
                result_list = EventsAdapter().get_video_service_messages()
                tmp_result = ""
                for res in result_list:
                    tmp_result += f"{res}<br>"
                result = tmp_result

        except Exception as e:
            result = f"Det har oppstått en feil: {e}"
            logging.error(f"Video events update - {e}")
        return web.Response(text=str(result))


def start_video_analytics(event_id: str) -> str:
    """Start video analytics."""
    analytics_running = EventsAdapter().get_global_setting("VIDEO_ANALYTICS_RUNNING")
    if analytics_running == "true":
        return "Video analytics already running"
    else:
        EventsAdapter().update_global_setting("VIDEO_ANALYTICS_START", "true")
    return "Video analytics started"


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

    EventsAdapter().update_global_setting("DRAW_TRIGGER_LINE", "true")
    return "Config updated - reload if new trigger line photo not is visible"
