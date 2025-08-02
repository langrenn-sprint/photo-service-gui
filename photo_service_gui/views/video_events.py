"""Resource module for video_event resources."""

import json
import logging

import aiohttp_jinja2
from aiohttp import web

from photo_service_gui.services import (
    ConfigAdapter,
    PhotosFileAdapter,
    StatusAdapter,
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
                    "trigger_line_xyxyn": await ConfigAdapter().get_config(
                        user["token"], event_id, "TRIGGER_LINE_XYXYN",
                    ),
                    "video_url": await ConfigAdapter().get_config(
                        user["token"], event_id, "VIDEO_URL",
                    ),
                    "service_status": await get_service_status(user["token"], event),
                    "sim_list": await ConfigAdapter().get_config(
                        user["token"], event_id, "SIMULATION_START_LIST_FILE",
                    ),
                    "sim_fastest_time": await ConfigAdapter().get_config(
                        user["token"], event_id, "SIMULATION_FASTEST_TIME",
                    ),
                },
            )
        except Exception as e:
            logging.exception("Error. Redirect to main page.")
            return web.HTTPSeeOther(location=f"/?informasjon={e}")

    async def post(self) -> web.Response:
        """Post route function that updates video events."""
        response = {
            "pub_message": "",
            "video_analytics": "",
            "video_status": "",
            "photo_queue": [],
            "capture_queue_length": 0,
            "filter_queue_length": 0,
            "trigger_line_url": "",
        }
        event_id = ""
        try:
            informasjon = ""
            form = await self.request.post()
            user = await check_login(self)
            event_id = str(form["event_id"])
            event = await get_event(user, event_id)
            if "update_config" in form:
                informasjon = await update_config(user["token"], event, dict(form))
            elif "reset_config" in form:
                informasjon = await reset_config(user["token"], event)
            elif "integration_start" in form:
                informasjon = await start_integration(user["token"], event)
            elif "integration_stop" in form:
                informasjon = await stop_integration(user["token"], event)
            elif "video_start" in form:
                informasjon = await start_video_analytics(user["token"], event)
            elif "video_stop" in form:
                informasjon = await stop_video_analytics(user["token"], event)
            if informasjon:
                return web.HTTPSeeOther(
                    location=f"/video_events?event_id={event_id}&informasjon={informasjon}",
                )
            if "video_status" in form or "photo_queue" in form:
                response["video_status"] = await get_analytics_status(
                    user["token"], event,
                )
                response["photo_queue"] = PhotosFileAdapter().get_all_photo_urls()
                response[
                    "capture_queue_length"
                ], response[
                    "filter_queue_length"
                ] = PhotosFileAdapter().get_clip_queue_length()
                response[
                    "trigger_line_url"
                ] = await PhotosFileAdapter().get_trigger_line_file_url(
                    user["token"], event,
                )
        except Exception as e:
            err_msg = f"Error updating video events: {e}"
            logging.exception("Video events update")
            return web.HTTPSeeOther(
                location=f"/video_events?event_id={event_id}&informasjon={err_msg}",
            )
        json_response = json.dumps(response)
        return web.Response(body=json_response)


async def get_analytics_status(token: str, event: dict) -> str:
    """Get video analytics status messages."""
    response = ""
    result_list = await StatusAdapter().get_status(token, event["id"], 25)
    for res in result_list:
        info_time = f"<a title={res['time']}>{res['time'][-8:]}</a>"
        response += f"{info_time} - {res['message']}<br>"
    return response


async def start_integration(token: str, event: dict) -> str:
    """Start video analytics."""
    await ConfigAdapter().update_config(
        token, event["id"], "INTEGRATION_SERVICE_START", "True",
    )
    return "Integration started"


async def stop_integration(token: str, event: dict) -> str:
    """Stop video analytics."""
    await ConfigAdapter().update_config(
        token, event["id"], "INTEGRATION_SERVICE_START", "False",
    )
    return "Stop video analytics initiert."


async def start_video_analytics(token: str, event: dict) -> str:
    """Start video analytics."""
    informasjon = "Video analytics started: "
    video_status = await get_service_status(token, event)

    await ConfigAdapter().update_config(
        token, event["id"], "CAPTURE_VIDEO_SERVICE_START", "True",
    )
    await ConfigAdapter().update_config(
        token, event["id"], "FILTER_VIDEO_SERVICE_START", "True",
    )
    await ConfigAdapter().update_config(
        token, event["id"], "DETECT_VIDEO_SERVICE_START", "True",
    )
    if video_status["capture_video_available"]:
        informasjon += "CAPTURE started. "
    else:
        informasjon += "Warning: CAPTURE not available. "
    if video_status["filter_video_available"]:
        informasjon += "FILTER started. "
    else:
        informasjon += "Warning: FILTER not available. "
    if video_status["detect_video_available"]:
        informasjon += "DETECT started. "
    else:
        informasjon += "Warning: DETECTION not available."
    return informasjon


async def stop_video_analytics(token: str, event: dict) -> str:
    """Stop video analytics."""
    await ConfigAdapter().update_config(
        token, event["id"], "CAPTURE_VIDEO_SERVICE_START", "False",
    )
    await ConfigAdapter().update_config(
        token, event["id"], "FILTER_VIDEO_SERVICE_START", "False",
    )
    await ConfigAdapter().update_config(
        token, event["id"], "DETECT_VIDEO_SERVICE_START", "False",
    )
    return "Video analytics stopped."


async def reset_config(token: str, event: dict) -> str:
    """Reset config for video service."""
    config_map = {
        "INTEGRATION_SERVICE_AVAILABLE": "False",
        "CAPTURE_VIDEO_SERVICE_AVAILABLE": "False",
        "FILTER_VIDEO_SERVICE_AVAILABLE": "False",
        "DETECT_VIDEO_SERVICE_AVAILABLE": "False",
        "INTEGRATION_SERVICE_MODE": "push",
    }

    for key, value in config_map.items():
        await ConfigAdapter().update_config(
            token, event["id"], key, value,
        )
    return "Video settings reset."


async def update_config(token: str, event: dict, form: dict) -> str:
    """Draw trigger line or initiate simulation."""
    informasjon = ""
    if "trigger_line_xyxyn" in form:
        await ConfigAdapter().update_config(
            token, event["id"], "TRIGGER_LINE_XYXYN", str(form["trigger_line_xyxyn"]),
        )
        await ConfigAdapter().update_config(
            token, event["id"], "VIDEO_URL", str(form["video_url"]),
        )
        await ConfigAdapter().update_config(
            token,
            event["id"],
            "VIDEO_ANALYTICS_IMAGE_SIZE",
            str(form["image_size"]),
        )
        await ConfigAdapter().update_config(
            token, event["id"], "DRAW_TRIGGER_LINE", "True",
        )
        informasjon = "Video settings updated."
    elif "sim_actual_url" in form:
        await ConfigAdapter().update_config(
            token,
            event["id"],
            "SIMULATION_START_LIST_FILE",
            str(form["sim_actual_url"]),
        )
        fastest_time = str(form["sim_fastest_time"])
        await ConfigAdapter().update_config(
            token, event["id"], "SIMULATION_FASTEST_TIME", fastest_time,
        )
        await ConfigAdapter().update_config(
            token, event["id"], "SIMULATION_CROSSINGS_START", "True",
        )
        informasjon = "Simulering av passeringer er initiert."
    return informasjon


async def get_service_status(token: str, event: dict) -> dict:
    """Get config details from db."""
    config_map = {
        "integration_available": ("INTEGRATION_SERVICE_AVAILABLE", "get_config_bool"),
        "integration_running": ("INTEGRATION_SERVICE_RUNNING", "get_config_bool"),
        "integration_start": ("INTEGRATION_SERVICE_START", "get_config_bool"),
        "integration_mode": ("INTEGRATION_SERVICE_MODE", "get_config"),
        "capture_video_available": (
            "CAPTURE_VIDEO_SERVICE_AVAILABLE", "get_config_bool",
        ),
        "capture_video_running": ("CAPTURE_VIDEO_SERVICE_RUNNING", "get_config_bool"),
        "capture_video_start": ("CAPTURE_VIDEO_SERVICE_START", "get_config_bool"),
        "capture_video_stop": ("CAPTURE_VIDEO_SERVICE_STOP", "get_config_bool"),
        "filter_video_available": (
            "FILTER_VIDEO_SERVICE_AVAILABLE", "get_config_bool",
        ),
        "filter_video_running": ("FILTER_VIDEO_SERVICE_RUNNING", "get_config_bool"),
        "filter_video_start": ("FILTER_VIDEO_SERVICE_START", "get_config_bool"),
        "filter_video_stop": ("FILTER_VIDEO_SERVICE_STOP", "get_config_bool"),
        "detect_video_available": ("DETECT_VIDEO_SERVICE_AVAILABLE", "get_config_bool"),
        "detect_video_running": ("DETECT_VIDEO_SERVICE_RUNNING", "get_config_bool"),
        "detect_video_start": ("DETECT_VIDEO_SERVICE_START", "get_config_bool"),
        "detect_video_stop": ("DETECT_VIDEO_SERVICE_STOP", "get_config_bool"),
        "video_analytics_im_size": ("VIDEO_ANALYTICS_IMAGE_SIZE", "get_config"),
        "video_analytics_im_size_def": (
            "VIDEO_ANALYTICS_DEFAULT_IMAGE_SIZES", "get_config_list",
        ),
    }

    adapter = ConfigAdapter()
    result = {}

    for key, (config_key, method) in config_map.items():
        if method == "get_config":
            result[key] = await adapter.get_config(token, event["id"], config_key)
        elif method == "get_config_bool":
            result[key] = await adapter.get_config_bool(token, event["id"], config_key)
        elif method == "get_config_list":
            result[key] = await adapter.get_config_list(token, event["id"], config_key)

    return result
