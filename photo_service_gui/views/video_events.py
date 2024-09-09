"""Resource module for video_event resources."""

import json
import logging

from aiohttp import web
import aiohttp_jinja2

from photo_service_gui.services import (
    ConfigAdapter,
    FotoService,
    PhotosFileAdapter,
    StatusAdapter,
)
from .utils import (
    check_login,
    get_event,
)

PHOTOS_URL_PATH = "files"


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

            trigger_line_file = await ConfigAdapter().get_config(
                user["token"], event, "TRIGGER_LINE_CONFIG_FILE"
            )
            trigger_line_file_url = f"{PHOTOS_URL_PATH}/{trigger_line_file}"

            """Get route function."""
            return await aiohttp_jinja2.render_template_async(
                "video_events.html",
                self.request,
                {
                    "event": event,
                    "event_id": event_id,
                    "informasjon": informasjon,
                    "username": user["name"],
                    "line_config_file": trigger_line_file_url,
                    "trigger_line_xyxyn": await ConfigAdapter().get_config(
                        user["token"], event, "TRIGGER_LINE_XYXYN"
                    ),
                    "photo_queue": PhotosFileAdapter().get_all_photo_urls(),
                    "video_url": await ConfigAdapter().get_config(
                        user["token"], event, "VIDEO_URL"
                    ),
                    "video_analytics_available": await ConfigAdapter().get_config(
                        user["token"], event, "VIDEO_ANALYTICS_AVAILABLE"
                    ),
                    "video_analytics_running": await ConfigAdapter().get_config(
                        user["token"], event, "VIDEO_ANALYTICS_RUNNING"
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
            try:
                event_id = str(form["event_id"])
                event = await get_event(user, event_id)
            except Exception:
                event_id = ""

            logging.debug(f"User: {user}")
            if "update_config" in form.keys():
                informasjon = await update_config(user["token"], event, form)  # type: ignore
                return web.HTTPSeeOther(
                    location=f"/video_events?event_id={event_id}&informasjon={informasjon}"
                )
            if "pub_message" in form.keys():
                res = await FotoService().push_new_photos_from_file(
                    user["token"], event
                )
                response["pub_message"] = res
            if "video_analytics_start" in form.keys():
                response["video_analytics"] = await start_video_analytics(
                    user["token"], event
                )
            elif "video_analytics_stop" in form.keys():
                response["video_analytics"] = await stop_video_analytics(
                    user["token"], event
                )
            if "video_status" in form.keys():
                status_type = await ConfigAdapter().get_config(
                    user["token"], event, "VIDEO_ANALYTICS_STATUS_TYPE"
                )
                result_list = await StatusAdapter().get_status_by_type(
                    user["token"], event, status_type, 25
                )
                for res in result_list:
                    response["video_status"] += f"{res['time']} - {res['message']}<br>"  # type: ignore
        except Exception as e:
            response["video_status"] = f"Det har oppstått en feil: {e}"
            logging.error(f"Video events update - {e}")
        json_response = json.dumps(response)
        return web.Response(body=json_response)


async def start_video_analytics(token: str, event: dict) -> str:
    """Start video analytics."""
    analytics_running = await ConfigAdapter().get_config_bool(
        token, event, "VIDEO_ANALYTICS_RUNNING"
    )
    if analytics_running:
        return "Video analytics already running"
    else:
        await ConfigAdapter().update_config(
            token, event, "VIDEO_ANALYTICS_START", "True"
        )
    return "Video analytics started"


async def stop_video_analytics(token: str, event: dict) -> str:
    """Stop video analytics."""
    await ConfigAdapter().update_config(token, event, "VIDEO_ANALYTICS_STOP", "True")
    return "Stop video analytics initiert."


async def update_config(token: str, event: dict, form: dict) -> str:
    """Draw trigger line with ultraltyics."""
    await ConfigAdapter().update_config(
        token, event, "TRIGGER_LINE_XYXYN", str(form["trigger_line_xyxyn"])
    )
    await ConfigAdapter().update_config(
        token, event, "VIDEO_URL", str(form["video_url"])
    )
    await ConfigAdapter().update_config(token, event, "DRAW_TRIGGER_LINE", "True")
    return "Config updated - reload if new trigger line photo not is visible"
