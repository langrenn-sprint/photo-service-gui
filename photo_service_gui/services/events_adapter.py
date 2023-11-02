"""Module for events adapter."""
from datetime import datetime
import json
import logging
import os
from typing import List
from zoneinfo import ZoneInfo

from aiohttp import ClientSession
from aiohttp import hdrs
from aiohttp import web
from multidict import MultiDict

EVENTS_HOST_SERVER = os.getenv("EVENTS_HOST_SERVER", "localhost")
EVENTS_HOST_PORT = os.getenv("EVENTS_HOST_PORT", "8082")
EVENT_SERVICE_URL = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"


class EventsAdapter:
    """Class representing events."""

    async def generate_classes(self, token: str, event_id: str) -> str:
        """Generate classes based upon registered contestants."""
        servicename = "generate_classes"
        headers = MultiDict(
            [
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ]
        )
        url = f"{EVENT_SERVICE_URL}/events/{event_id}/generate-raceclasses"
        async with ClientSession() as session:
            async with session.post(url, headers=headers) as resp:
                res = resp.status
                logging.debug(f"generate_raceclasses result - got response {resp}")
                if res == 201:
                    pass
                elif resp.status == 401:
                    raise web.HTTPBadRequest(reason=f"401 Unathorized - {servicename}")
                else:
                    body = await resp.json()
                    logging.error(f"{servicename} failed - {resp.status} - {body}")
                    raise web.HTTPBadRequest(
                        reason=f"Error - {resp.status}: {body['detail']}."
                    )
        information = "Opprettet klasser."
        return information

    async def get_all_events(self, token: str) -> List:
        """Get all events function."""
        events = []

        # TODO: must be updated to use new event service
        event = {
            "id": "1",
            "name": "Testevent foto",
            "date_of_event": "2023-12-11",
            "time_of_event": "12:00",
            "timezone": "Europe/Oslo",
            "competition_format": "Individual sprint",
            "organiser": "Kjelsås IL",
            "webpage": "langrenn.kjelsaas.no",
            "information": "",
        }
        events.append(event)
        return events

    async def get_event(self, token: str, id: str) -> dict:
        """Get event function."""
        event = {}
        events = await self.get_all_events(token)
        for e in events:
            if e["id"] == id:
                event = e
                break
        return event

    def get_global_setting(self, param_name: str) -> str:
        """Get global settings from .env file."""
        config_files_directory = f"{os.getcwd()}/photo_service_gui/config"
        try:
            with open(f"{config_files_directory}/global_settings.json") as json_file:
                settings = json.load(json_file)
                global_setting = settings[param_name]
        except Exception as e:
            logging.error(
                f"Global setting {param_name} not found. File path {config_files_directory} - {e}"
            )
            raise Exception from e
        return global_setting

    def get_local_datetime_now(self, event: dict) -> datetime:
        """Return local datetime object, time zone adjusted from event info."""
        timezone = event["timezone"]
        if timezone:
            local_time_obj = datetime.now(ZoneInfo(timezone))
        else:
            local_time_obj = datetime.now()
        return local_time_obj

    def get_local_time(self, event: dict, format: str) -> str:
        """Return local time string, time zone adjusted from event info."""
        local_time = ""
        timezone = event["timezone"]
        if timezone:
            time_now = datetime.now(ZoneInfo(timezone))
        else:
            time_now = datetime.now()

        if format == "HH:MM":
            local_time = (
                f"{time_now.strftime('%H')}:{time_now.strftime('%M')}"
            )
        elif format == "log":
            local_time = f"{time_now.strftime('%Y')}-{time_now.strftime('%m')}-{time_now.strftime('%d')}T{time_now.strftime('%X')}"
        else:
            local_time = time_now.strftime("%X")
        return local_time

    def get_club_logo_url(self, club_name: str) -> str:
        """Get url to club logo - input is 4 first chars of club name."""
        config_files_directory = f"{os.getcwd()}/photo_service_gui/config"
        try:
            club_name_short = club_name[:4]
            with open(f"{config_files_directory}/sports_clubs.json") as json_file:
                logo_urls = json.load(json_file)
            logo_url = logo_urls[club_name_short]
        except Exception as e:
            logging.error(f"Club logo not found - {club_name}, error: {e}")
            logo_url = ""
        return logo_url
