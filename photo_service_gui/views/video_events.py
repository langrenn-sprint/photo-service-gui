"""Resource module for video_event resources."""

import json
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

PHOTOS_URL_PATH = "files"
TRIGGER_LINE_CONFIG_FILE = EventsAdapter().get_global_setting(
    "TRIGGER_LINE_CONFIG_FILE"
)
TRIGGER_LINE_CONFIG_URL = f"{PHOTOS_URL_PATH}/{TRIGGER_LINE_CONFIG_FILE}"


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
                    "line_config_file": TRIGGER_LINE_CONFIG_URL,
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
        response = {"pub_message": "", "video_analytics": "", "video_status": ""}
        try:
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
                response["pub_message"] = res
            if "video_analytics_start" in form.keys():
                event_id = str(form["event_id"])
                response["video_analytics"] = start_video_analytics(event_id)
            elif "video_analytics_stop" in form.keys():
                response["video_analytics"] = stop_video_analytics()
            if "video_status" in form.keys():
                result_list = EventsAdapter().get_video_service_status_messages()
                for res in result_list:
                    response["video_status"] += f"{res}<br>"
        except Exception as e:
            response["video_status"] = f"Det har oppstått en feil: {e}"
            logging.error(f"Video events update - {e}")
        json_response = json.dumps(response)
        return web.Response(body=json_response)


def start_video_analytics(event_id: str) -> str:
    """Start video analytics."""
    analytics_running = EventsAdapter().get_global_setting_bool(
        "VIDEO_ANALYTICS_RUNNING"
    )
    if analytics_running:
        return "Video analytics already running"
    else:
        EventsAdapter().update_global_setting("VIDEO_ANALYTICS_START", "True")
    return "Video analytics started"


def stop_video_analytics() -> str:
    """Stop video analytics."""
    EventsAdapter().update_global_setting("VIDEO_ANALYTICS_STOP", "True")
    return "Stop video analytics initiert."


def update_config(form: dict) -> str:
    """Draw trigger line with ultraltyics."""
    EventsAdapter().update_global_setting(
        "TRIGGER_LINE_XYXYN", str(form["trigger_line_xyxyn"])
    )
    EventsAdapter().update_global_setting("VIDEO_URL", str(form["video_url"]))

    EventsAdapter().update_global_setting("DRAW_TRIGGER_LINE", "True")
    return "Config updated - reload if new trigger line photo not is visible"
