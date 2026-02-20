"""Resource module for video_event resources."""

import json
import logging

import aiohttp_jinja2
from aiohttp import web

from photo_service_gui.services import (
    ConfigAdapter,
    EventsAdapter,
    GoogleCloudStorageAdapter,
    LiveStreamService,
    PhotosFileAdapter,
    ServiceInstanceAdapter,
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
            _instances = await ServiceInstanceAdapter().get_all_service_instances(
                        user["token"], event_id,
                    )

            """Get route function."""
            return await aiohttp_jinja2.render_template_async(
                "video_events.html",
                self.request,
                {
                    "event": event,
                    "event_id": event_id,
                    "informasjon": informasjon,
                    "local_time_now": EventsAdapter().get_local_time(event, "HH:MM"),
                    "username": user["name"],
                    "trigger_line_xyxyn": await ConfigAdapter().get_config(
                        user["token"], event_id, "TRIGGER_LINE_XYXYN",
                    ),
                    "video_url": await ConfigAdapter().get_config(
                        user["token"], event_id, "VIDEO_URL",
                    ),
                    "service_status": await get_service_status(user["token"], event),
                    "service_instances": _instances,
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
            "local_raw_captured_queue_length": 0,
            "local_captured_queue_length": 0,
            "cloud_captured_queue_length": 0,
            "trigger_line_url": "",
            "photo_latest": "",
            "service_status": {},
            "service_instances": [],
        }
        event_id = ""
        try:
            form = await self.request.post()
            user = await check_login(self)
            event_id = str(form["event_id"])
            event = await get_event(user, event_id)
            if "instance_action" in form or "update_config" in form:
                informasjon = await handle_form_actions(
                    user, event, dict(form),
                )
                json_response = json.dumps(informasjon)
                return web.Response(body=json_response)

            if "video_status" in form or "photo_queue" in form:
                response["video_status"] = await get_analytics_status(
                    user["token"], event,
                )
                response[
                    "local_raw_captured_queue_length"
                ] = PhotosFileAdapter().get_local_raw_capture_queue_length()
                response[
                    "local_captured_queue_length"
                ] = PhotosFileAdapter().get_local_capture_queue_length()
                response[
                    "cloud_captured_queue_length"
                ] = GoogleCloudStorageAdapter().list_blobs(
                    event_id, "CAPTURE/",
                ).__len__()
                response[
                    "trigger_line_url"
                ] = await ConfigAdapter().get_config(
                    user["token"], event_id, "TRIGGER_LINE_PHOTO_URL",
                )
                response["photo_latest"] = await ConfigAdapter().get_config(
                    user["token"], event_id, "LATEST_DETECTED_PHOTO_URL",
                )
                response["service_status"] = await get_service_status(
                    user["token"], event,
                )
                response["service_instances"] = await get_service_instances(user, event)
        except Exception as e:
            err_msg = f"Error updating video events: {e}"
            logging.exception("Video events update")
            return web.HTTPSeeOther(
                location=f"/video_events?event_id={event_id}&informasjon={err_msg}",
            )
        json_response = json.dumps(response)

        return web.Response(body=json_response)

async def get_service_instances(user: dict, event: dict) -> list:
    """Get active service instances."""
    service_instances = await ServiceInstanceAdapter().get_all_service_instances(
        user["token"], event["id"],
    )
    if service_instances:
        service = LiveStreamService()
        for instance in service_instances:
            try:
                channel = await service.get_channel_status(instance["instance_name"])
                instance["status"] = channel["state"]
            except Exception:
                logging.exception(f"Error getting channel {instance['instance_name']}")
                instance["status"] = "ERROR"
    return service_instances



async def handle_form_actions(user: dict, event: dict, form: dict) -> str:
    """Handle form actions for video events."""
    informasjon = ""

    if "instance_action" in form:
        informasjon = await ServiceInstanceAdapter().update_service_instance_action(
            user["token"], event, form["instance_id"], form["instance_action"],
        )
    if "update_config" in form:
        informasjon += await update_config(user["token"], event, form)
    return informasjon

async def get_analytics_status(token: str, event: dict) -> str:
    """Get video analytics status messages."""
    response = ""
    result_list = await StatusAdapter().get_status(token, event["id"], 8)
    for res in result_list:
        info_time = f"<a title={res['time']}>{res['time'][-8:]}</a>"
        res_type = ""
        if res["type"] in ["video_status_CAPTURE_SRT", "video_status_CAPTURE_LOCAL"]:
            res_type = "<img id=menu_icon src=../static/capture.png title=Video>"
        elif res["type"] == "video_status_DETECT":
            res_type = "<img id=menu_icon src=../static/detect.png title=Deteksjon>"
        elif res["type"] == "integration_status":
            res_type = "<img id=menu_icon src=../static/upload.png title=Opplasting>"
        if "Error" in res["message"]:
            msg = res["message"]
            response += f"{info_time} {res_type} <span id=red>{msg}</span><br>"
            if res["details"]:
                details_tag = '<details style="display: inline;">'
                summary_tag = (
                    '<summary style="display: inline; list-style: none; '
                    'color: #0066cc; text-decoration: underline; '
                    'cursor: pointer;">'
                )
                pre_style = (
                    "margin: 5px 0; padding: 8px; background: #f5f5f5; "
                    "border-left: 3px solid #ccc; font-size: 0.9em; "
                    "white-space: pre-wrap;"
                )
                details = res["details"]
                response += (
                    f'{details_tag}{summary_tag}(detaljer)</summary>'
                    f'<pre style="{pre_style}">{details}</pre></details>'
                )
        else:
            response += f"{info_time} {res_type} {res['message']}<br>"
    return response

async def update_config(token: str, event: dict, form: dict) -> str:
    """Draw trigger line."""
    informasjon = ""
    if "trigger_line_xyxyn" in form:
        await ConfigAdapter().update_config(
            token, event["id"], "TRIGGER_LINE_XYXYN", str(form["trigger_line_xyxyn"]),
        )
        await ConfigAdapter().update_config(
            token, event["id"], "NEW_TRIGGER_LINE_PHOTO", "True",
        )
        await ConfigAdapter().update_config(
            token, event["id"], "VIDEO_URL", str(form["video_url"]),
        )
        await ConfigAdapter().update_config(
            token,
            event["id"],
            "DETECT_ANALYTICS_IMAGE_SIZE",
            str(form["detect_image_size"]),
        )
        await ConfigAdapter().update_config(
            token, event["id"], "DRAW_TRIGGER_LINE", "True",
        )
        await ConfigAdapter().update_config(
            token, event["id"], "VIDEO_CLIP_DURATION", str(form["video_clip_duration"]),
        )
        await ConfigAdapter().update_config(
            token, event["id"], "VIDEO_CLIP_FPS", str(form["video_clip_fps"]),
        )
        await ConfigAdapter().update_config(
            token, event["id"], "CONFIDENCE_LIMIT", str(form["confidence_limit"]),
        )
        informasjon = "Video settings updated. "

    if "storage_mode" in form:
        new_storage_mode = str(form["storage_mode"])
        informasjon += await update_storage_mode(token, event, new_storage_mode)

    return informasjon

async def update_storage_mode(token: str, event: dict, new_storage_mode: str) -> str:
    """Update storage mode."""
    if new_storage_mode == "0":
        return "" # No change
    if new_storage_mode == "local_storage":
        await ConfigAdapter().update_config(
            token, event["id"], "VIDEO_STORAGE_MODE", "local_storage",
        )
        return f"Oppdatert storage mode til {new_storage_mode}. "
    if new_storage_mode == "cloud_storage":
        await ConfigAdapter().update_config(
            token, event["id"], "VIDEO_STORAGE_MODE", "cloud_storage",
        )
        return f"Oppdatert storage mode til {new_storage_mode}. "
    return "Ugyldig storage mode valgt. "

async def get_service_status(token: str, event: dict) -> dict:
    """Get config details from db."""
    config_map = {
        "confidence_limit": ("CONFIDENCE_LIMIT", "get_config"),
        "storage_mode_name": ("VIDEO_STORAGE_MODE", "get_config"),
        "detect_analytics_im_size": (
            "DETECT_ANALYTICS_IMAGE_SIZE", "get_config",
        ),
        "video_analytics_im_size_def": (
            "VIDEO_ANALYTICS_DEFAULT_IMAGE_SIZES", "get_config_list",
        ),
        "video_clip_duration": ("VIDEO_CLIP_DURATION", "get_config"),
        "video_clip_fps": ("VIDEO_CLIP_FPS", "get_config"),
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
