"""Resource module for video_event resources."""

import json
import logging

from aiohttp import web
import aiohttp_jinja2

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
                        user["token"], event, "TRIGGER_LINE_XYXYN"
                    ),
                    "video_url": await ConfigAdapter().get_config(
                        user["token"], event, "VIDEO_URL"
                    ),
                    "service_status": await get_service_status(user["token"], event),
                    "sim_list": await ConfigAdapter().get_config(
                        user["token"], event, "SIMULATION_START_LIST_FILE"
                    ),
                    "sim_fastest_time": await ConfigAdapter().get_config(
                        user["token"], event, "SIMULATION_FASTEST_TIME"
                    ),
                },
            )
        except Exception as e:
            logging.error(f"Error: {e}. Redirect to main page.")
            return web.HTTPSeeOther(location=f"/?informasjon={e}")

    async def post(self) -> web.Response:
        """Post route function that updates video events."""
        response = {
            "pub_message": "",
            "video_analytics": "",
            "video_status": "",
            "photo_queue": [],
            "trigger_line_url": "",
        }
        try:
            form = await self.request.post()
            user = await check_login(self)
            try:
                event_id = str(form["event_id"])
                event = await get_event(user, event_id)
            except Exception:
                event_id = ""

            if "update_config" in form.keys():
                informasjon = await update_config(user["token"], event, form)  # type: ignore
                return web.HTTPSeeOther(
                    location=f"/video_events?event_id={event_id}&informasjon={informasjon}"
                )
            if "integration_start" in form.keys():
                response["integration_start"] = await start_integration(
                    user["token"], event
                )
            if "integration_stop" in form.keys():
                response["integration_stop"] = await stop_integration(
                    user["token"], event
                )
            if "video_analytics_start" in form.keys():
                response["video_analytics"] = await start_video_analytics(
                    user["token"], event
                )
            elif "video_analytics_stop" in form.keys():
                response["video_analytics"] = await stop_video_analytics(
                    user["token"], event
                )
            if "video_status" in form.keys():
                response["video_status"] = await get_analytics_status(
                    user["token"], event
                )
            if "photo_queue" in form.keys():
                response["photo_queue"] = PhotosFileAdapter().get_all_photo_urls()
                response[
                    "trigger_line_url"
                ] = await PhotosFileAdapter().get_trigger_line_file_url(
                    user["token"], event
                )
        except Exception as e:
            response["video_status"] = f"Det har oppstått en feil: {e}"
            logging.error(f"Video events update - {e}")

        json_response = json.dumps(response)
        return web.Response(body=json_response)


async def get_analytics_status(token: str, event: dict) -> str:
    """Get video analytics status messages."""
    response = ""
    result_list = await StatusAdapter().get_status(token, event, 25)
    for res in result_list:
        info_time = f"<a title={res['time']}>{res['time'][-8:]}</a>"  # type: ignore
        response += f"{info_time} - {res['message']}<br>"  # type: ignore
    return response


async def start_integration(token: str, event: dict) -> str:
    """Start video analytics."""
    await ConfigAdapter().update_config(
        token, event, "INTEGRATION_SERVICE_START", "True"
    )
    return "Integration started"


async def stop_integration(token: str, event: dict) -> str:
    """Stop video analytics."""
    await ConfigAdapter().update_config(
        token, event, "INTEGRATION_SERVICE_START", "False"
    )
    return "Stop video analytics initiert."


async def start_video_analytics(token: str, event: dict) -> str:
    """Start video analytics."""
    await ConfigAdapter().update_config(token, event, "VIDEO_ANALYTICS_START", "True")
    return "Video analytics started"


async def stop_video_analytics(token: str, event: dict) -> str:
    """Stop video analytics."""
    await ConfigAdapter().update_config(token, event, "VIDEO_ANALYTICS_STOP", "True")
    return "Stop video analytics initiert."


async def update_config(token: str, event: dict, form: dict) -> str:
    """Draw trigger line or initiate simulation."""
    informasjon = ""
    if "trigger_line_xyxyn" in form.keys():
        await ConfigAdapter().update_config(
            token, event, "TRIGGER_LINE_XYXYN", str(form["trigger_line_xyxyn"])
        )
        await ConfigAdapter().update_config(
            token, event, "VIDEO_URL", str(form["video_url"])
        )
        await ConfigAdapter().update_config(token, event, "DRAW_TRIGGER_LINE", "True")
        informasjon = "Video settings updated."
    elif "sim_list" in form.keys():
        await ConfigAdapter().update_config(
            token, event, "SIMULATION_START_LIST_FILE", str(form["sim_list"])
        )
        await ConfigAdapter().update_config(
            token, event, "SIMULATION_FASTEST_TIME", str(form["sim_fastest_time"])
        )
        await ConfigAdapter().update_config(
            token, event, "SIMULATION_CROSSINGS_START", "True"
        )
        informasjon = "Simulering av passeringer er initiert."
    return informasjon


async def get_service_status(token: str, event: dict) -> dict:
    """Get config details from db."""
    integration_available = await ConfigAdapter().get_config(
        token, event, "INTEGRATION_SERVICE_AVAILABLE"
    )
    integration_running = await ConfigAdapter().get_config_bool(
        token, event, "INTEGRATION_SERVICE_RUNNING"
    )
    integration_start = await ConfigAdapter().get_config_bool(
        token, event, "INTEGRATION_SERVICE_START"
    )
    integration_mode = await ConfigAdapter().get_config(
        token, event, "INTEGRATION_SERVICE_MODE"
    )
    video_analytics_running = await ConfigAdapter().get_config_bool(
        token, event, "VIDEO_ANALYTICS_RUNNING"
    )
    video_analytics_start = await ConfigAdapter().get_config_bool(
        token, event, "VIDEO_ANALYTICS_START"
    )
    video_analytics_stop = await ConfigAdapter().get_config_bool(
        token, event, "VIDEO_ANALYTICS_STOP"
    )
    video_analytics_available = await ConfigAdapter().get_config(
        token, event, "VIDEO_ANALYTICS_AVAILABLE"
    )
    return {
        "integration_available": integration_available,
        "integration_running": integration_running,
        "integration_start": integration_start,
        "integration_mode": integration_mode,
        "video_analytics_running": video_analytics_running,
        "video_analytics_start": video_analytics_start,
        "video_analytics_stop": video_analytics_stop,
        "video_analytics_available": video_analytics_available,
    }
