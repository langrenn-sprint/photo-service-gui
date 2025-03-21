"""Module for events adapter."""

import copy
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

from .competition_format_adapter import CompetitionFormatAdapter
from .config_adapter import ConfigAdapter

EVENTS_HOST_SERVER = os.getenv("EVENTS_HOST_SERVER", "localhost")
EVENTS_HOST_PORT = os.getenv("EVENTS_HOST_PORT", "8082")
EVENT_SERVICE_URL = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"

config_files_directory = f"{os.getcwd()}/photo_service_gui/config"


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
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ]
        )

        async with ClientSession() as session:
            async with session.get(
                f"{EVENT_SERVICE_URL}/events", headers=headers
            ) as resp:
                logging.debug(f"get_all_events - got response {resp.status}")
                if resp.status == 200:
                    events = await resp.json()
                    logging.debug(f"events - got response {events}")
                elif resp.status == 401:
                    raise Exception(f"Login expired: {resp}")
                else:
                    logging.error(f"Error {resp.status} getting events: {resp} ")
        return events

    async def get_event(self, token: str, id: str) -> dict:
        """Get event function."""
        event = {}
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ]
        )

        async with ClientSession() as session:
            async with session.get(
                f"{EVENT_SERVICE_URL}/events/{id}", headers=headers
            ) as resp:
                logging.debug(f"get_event {id} - got response {resp.status}")
                if resp.status == 200:
                    event = await resp.json()
                    logging.debug(f"event - got response {event}")
                elif resp.status == 401:
                    raise Exception(f"Login expired: {resp}")
                else:
                    servicename = "get_event"
                    body = await resp.json()
                    logging.error(f"{servicename} failed - {resp.status} - {body}")
                    raise web.HTTPBadRequest(
                        reason=f"Error - {resp.status}: {body['detail']}."
                    )
        return event

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
            local_time = f"{time_now.strftime('%H')}:{time_now.strftime('%M')}"
        elif format == "log":
            local_time = f"{time_now.strftime('%Y')}-{time_now.strftime('%m')}-{time_now.strftime('%d')}T{time_now.strftime('%X')}"
        else:
            local_time = time_now.strftime("%X")
        return local_time

    def get_club_logo_url(self, club_name: str) -> str:
        """Get url to club logo - input is 4 first chars of club name."""
        try:
            club_name_short = club_name[:4]
            with open(f"{config_files_directory}/sports_clubs.json") as json_file:
                logo_urls = json.load(json_file)
            logo_url = logo_urls[club_name_short]
        except Exception as e:
            logging.error(f"Club logo not found - {club_name}, error: {e}")
            logo_url = ""
        return logo_url

    # import events from remote server
    async def sync_events(self, token: str, remote_url: str) -> str:
        """Import events from remote server and store in local db."""
        servicename = "sync_events"
        information = "Importerer events."
        current_events = await self.get_all_events(token)
        current_event_ids = []
        for event in current_events:
            current_event_ids.append(event["id"])

        headers = MultiDict(
            [
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ]
        )
        url = f"{remote_url}/?action=REST"
        async with ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                res = resp.status
                if res == 200:
                    events = await resp.json()
                    # import events to local database
                    if events:
                        for event in events:
                            if event["id"] not in current_event_ids:
                                information += await EventsAdapter().create_event(
                                    token, event
                                )
                elif resp.status == 401:
                    raise web.HTTPBadRequest(reason=f"401 Unathorized - {servicename}")
                else:
                    body = await resp.json()
                    logging.error(f"{servicename} failed - {resp.status} - {body}")
                    raise web.HTTPBadRequest(
                        reason=f"Error - {resp.status}: {body['detail']}."
                    )
        return information

    async def create_event(self, token: str, event: dict) -> str:
        """Create new event function."""
        servicename = "create_event"

        # create competition formats if nessesary
        competition_formats = await CompetitionFormatAdapter().get_competition_formats(
            token
        )
        if len(competition_formats) == 0:
            request_body = CompetitionFormatAdapter().get_default_competition_format(
                "default_individual_sprint"
            )
            await CompetitionFormatAdapter().create_competition_format(
                token, request_body
            )

        id = ""
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ]
        )
        request_body = copy.deepcopy(event)

        async with ClientSession() as session:
            async with session.post(
                f"{EVENT_SERVICE_URL}/events", headers=headers, json=request_body
            ) as resp:
                if resp.status == 201:
                    logging.debug(f"result - got response {resp}")
                    location = resp.headers[hdrs.LOCATION]
                    id = location.split(os.path.sep)[-1]
                elif resp.status == 401:
                    raise web.HTTPBadRequest(reason=f"401 Unathorized - {servicename}")
                else:
                    body = await resp.json()
                    logging.error(f"{servicename} failed - {resp.status} - {body}")
                    raise web.HTTPBadRequest(
                        reason=f"Error - {resp.status}: {body['detail']}."
                    )
        # initialize config for event
        event = await self.get_event(token, id)
        await ConfigAdapter().init_config(token, event)

        return id

    async def delete_event(self, token: str, id: str) -> str:
        """Delete event function."""
        servicename = "delete_event"
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ]
        )
        url = f"{EVENT_SERVICE_URL}/events/{id}"
        async with ClientSession() as session:
            async with session.delete(url, headers=headers) as resp:
                pass
            logging.debug(f"Delete event: {id} - res {resp.status}")
            if resp.status == 204:
                logging.debug(f"result - got response {resp}")
            else:
                body = await resp.json()
                logging.error(f"{servicename} failed - {resp.status} - {body}")
                raise web.HTTPBadRequest(
                    reason=f"Error - {resp.status}: {body['detail']}."
                )
        return str(resp.status)

    async def update_event(self, token: str, id: str, request_body: dict) -> str:
        """Update event function."""
        servicename = "update_event"
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ]
        )

        async with ClientSession() as session:
            async with session.put(
                f"{EVENT_SERVICE_URL}/events/{id}", headers=headers, json=request_body
            ) as resp:
                if resp.status == 204:
                    logging.debug(f"update event - got response {resp}")
                elif resp.status == 401:
                    raise web.HTTPBadRequest(reason=f"401 Unathorized - {servicename}")
                else:
                    body = await resp.json()
                    logging.error(f"{servicename} failed - {resp.status} - {body}")
                    raise web.HTTPBadRequest(
                        reason=f"Error - {resp.status}: {body['detail']}."
                    )
            logging.debug(f"Updated event: {id} - res {resp.status}")
        return str(resp.status)
