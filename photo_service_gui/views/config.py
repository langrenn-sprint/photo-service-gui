"""Resource module for main view."""

import logging

import aiohttp_jinja2
from aiohttp import web

from photo_service_gui.services import (
    ConfigAdapter,
    LiveStreamService,
    ServiceInstanceAdapter,
)

from .utils import check_login, get_event


class Config(web.View):

    """Class representing the main view."""

    async def get(self) -> web.Response:
        """Get function that return the index page."""
        try:
            informasjon = self.request.rel_url.query["informasjon"]
        except Exception:
            informasjon = ""
        try:
            event_id = self.request.rel_url.query["event_id"]
        except Exception:
            event_id = ""
        try:
            action = self.request.rel_url.query["action"]
        except Exception:
            action = ""

        try:
            user = await check_login(self)
            event = await get_event(user, event_id)

            srt_streams = await get_srt_streams()

            try:
                event_config = await ConfigAdapter().get_all_configs(
                    user["token"], event_id,
                )
            except Exception:
                event_config = []
                informasjon += " Feil ved innlasting av config."

            s_instances = await ServiceInstanceAdapter().get_all_service_instances(
                user["token"], event_id,
            )

            return await aiohttp_jinja2.render_template_async(
                "config.html",
                self.request,
                {
                    "action": action,
                    "lopsinfo": "Langrenn-sprint",
                    "event": event,
                    "event_id": event_id,
                    "event_config": event_config,
                    "informasjon": informasjon,
                    "srt_streams": srt_streams,
                    "service_instances": s_instances,
                    "username": user["name"],
                },
            )
        except Exception as e:
            logging.exception("Error. Redirect to login page.")
            return web.HTTPSeeOther(location=f"/login?informasjon={e}")

    async def post(self) -> web.Response:
        """Post route function that updates video events."""
        event_id = ""
        try:
            informasjon = ""
            form = await self.request.post()
            user = await check_login(self)
            event_id = str(form["event_id"])
            event = await get_event(user, event_id)

            if "update_one" in form:
                key = str(form["key"])
                await ConfigAdapter().update_config(
                    user["token"], event_id, key, str(form["value"]),
                )
                informasjon = "Suksess. Informasjon er oppdatert."
            elif "delete_instance" in form:
                await ServiceInstanceAdapter().delete_service_instance(
                    user["token"], str(form["id"]),
                )
                informasjon = "Suksess. Instans er slettet."
            elif "delete_channel" in form:
                channel_name = str(form["name"])
                service = LiveStreamService()
                await delete_instance_by_channel_name(
                    user["token"], event_id, channel_name,
                )
                informasjon = service.delete_channel(channel_name)
                if "input" in form:
                    input_name = str(form["input"])
                    informasjon += " " + service.delete_input(input_name)
            elif "delete_input" in form:
                input_name = str(form["name"])
                service = LiveStreamService()
                informasjon = service.delete_input(input_name)
            elif "create_channel" in form:
                name = str(form["name"]).strip().lower()
                service = LiveStreamService()
                informasjon = await service.create_and_start_channel(
                    user["token"], event, name,
                )

        except Exception as e:
            logging.exception("Error")
            informasjon = f"Det har oppstått en feil - {e.args}."
            error_reason = str(e)
            if error_reason.count("401 Unauthorized") > 0   :
                informasjon = "401 Unauthorized - Ingen tilgang, logg inn på nytt."
                return web.HTTPSeeOther(
                    location=f"/login?informasjon={informasjon}",
                )

        return web.HTTPSeeOther(
            location=f"/config?action=edit_mode&event_id={event_id}&informasjon={informasjon}",
        )

async def get_srt_streams() -> dict:
    """Get all srt streams."""
    service = LiveStreamService()
    channels = await service.list_active_channels()
    inputs = await service.list_active_inputs()
    return {"channels": channels, "inputs": inputs}

async def delete_instance_by_channel_name(
        token: str, event_id: str, channel_name: str,
    ) -> None:
    """Delete service instance by channel name."""
    instances = await ServiceInstanceAdapter().get_all_service_instances(
        token, event_id,
    )
    for instance in instances:
        if channel_name.endswith(instance["instance_name"]):
            await ServiceInstanceAdapter().delete_service_instance(
                token, instance["id"],
            )
            break
