"""Module for events adapter."""

import copy
import datetime
import json
import logging
import os
from http import HTTPStatus
from pathlib import Path
from zoneinfo import ZoneInfo

from aiohttp import ClientSession, hdrs, web
from multidict import MultiDict

from .competition_format_adapter import CompetitionFormatAdapter

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
            ],
        )
        url = f"{EVENT_SERVICE_URL}/events/{event_id}/generate-raceclasses"
        async with ClientSession() as session, session.post(
            url, headers=headers,
        ) as resp:
            res = resp.status
            logging.info(f"generate_raceclasses result - got response {resp}")
            if res == HTTPStatus.CREATED:
                pass
            elif resp.status == HTTPStatus.UNAUTHORIZED:
                err_msg = f"401 Unathorized - {servicename}"
                raise web.HTTPBadRequest(reason=err_msg)
            else:
                body = await resp.json()
                logging.error(f"{servicename} failed - {resp.status} - {body}")
                raise web.HTTPBadRequest(
                    reason=f"Error - {resp.status}: {body['detail']}.",
                )
        return "Opprettet klasser."

    async def get_all_events(self, token: str) -> list:
        """Get all events function."""
        events = []
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ],
        )

        async with ClientSession() as session, session.get(
            f"{EVENT_SERVICE_URL}/events", headers=headers,
        ) as resp:
            logging.info(f"get_all_events - got response {resp.status}")
            if resp.status == HTTPStatus.OK:
                events = await resp.json()
                logging.info(f"events - got response {events}")
            elif resp.status == HTTPStatus.UNAUTHORIZED:
                err_msg = f"Login expired: {resp}"
                raise Exception(err_msg)

            else:
                logging.error(f"Error {resp.status} getting events: {resp} ")
        return events

    async def get_event(self, token: str, my_id: str) -> dict:
        """Get event function."""
        event = {}
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ],
        )

        async with ClientSession() as session, session.get(
            f"{EVENT_SERVICE_URL}/events/{my_id}", headers=headers,
        ) as resp:
            logging.info(f"get_event {my_id} - got response {resp.status}")
            if resp.status == HTTPStatus.OK:
                event = await resp.json()
                logging.info(f"event - got response {event}")
            elif resp.status == HTTPStatus.UNAUTHORIZED:
                err_msg = f"Login expired: {resp}"
                raise Exception(err_msg)

            else:
                servicename = "get_event"
                body = await resp.json()
                logging.error(f"{servicename} failed - {resp.status} - {body}")
                raise web.HTTPBadRequest(
                    reason=f"Error - {resp.status}: {body['detail']}.",
                )
        return event

    def get_local_datetime_now(self, event: dict) -> datetime.datetime:
        """Return local datetime object, time zone adjusted from event info."""
        time_zone = event["timezone"]
        if time_zone:
            local_time_obj = datetime.datetime.now(ZoneInfo(time_zone))
        else:
            local_time_obj = datetime.datetime.now(datetime.UTC)
        return local_time_obj

    def get_local_time(self, event: dict, time_format: str) -> str:
        """Return local time string, time zone adjusted from event info."""
        lt = "" # local time
        time_zone = event["timezone"]
        tn = datetime.datetime.now(
            ZoneInfo(time_zone),
        )if time_zone else datetime.datetime.now(datetime.UTC)

        if time_format == "HH:MM":
            lt = f"{tn.strftime('%H')}:{tn.strftime('%M')}"
        elif time_format == "log":
            lt = f"{
                tn.strftime('%Y')
            }-{tn.strftime('%m')}-{tn.strftime('%d')}T{tn.strftime('%X')}"
        else:
            lt = tn.strftime("%X")
        return lt

    def get_club_logo_url(self, club_name: str) -> str:
        """Get url to club logo - input is 4 first chars of club name."""
        config_file = Path(f"{Path.cwd()}/photo_service_gui/config/sports_clubs.json")
        logo_url = ""
        if club_name:
            try:
                club_name_short = club_name[:4].ljust(4)
                with config_file.open() as json_file:
                    logo_urls = json.load(json_file)
                logo_url = logo_urls[club_name_short]
            except Exception:
                logging.exception(f"Club logo not found - {club_name}")
        return logo_url

    # import events from remote server
    async def sync_events(self, token: str, remote_url: str) -> str:
        """Import events from remote server and store in local db."""
        servicename = "sync_events"
        information = "Importerer events."
        current_events = await self.get_all_events(token)
        current_event_ids = [event["id"] for event in current_events]

        headers = MultiDict(
            [
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ],
        )
        url = f"{remote_url}/?action=REST"
        async with ClientSession() as session, session.get(
            url, headers=headers,
        ) as resp:
            res = resp.status
            if res == HTTPStatus.OK:
                events = await resp.json()
                # import events to local database
                if events:
                    for event in events:
                        if event["id"] not in current_event_ids:
                            information += await EventsAdapter().create_event(
                                token, event,
                            )
            elif resp.status == HTTPStatus.UNAUTHORIZED:
                raise web.HTTPBadRequest(reason=f"401 Unathorized - {servicename}")
            else:
                body = await resp.json()
                logging.error(f"{servicename} failed - {resp.status} - {body}")
                raise web.HTTPBadRequest(
                    reason=f"Error - {resp.status}: {body['detail']}.",
                )
        return information

    async def create_event(self, token: str, event: dict) -> str:
        """Create new event function."""
        servicename = "create_event"
        result = ""
        # add default values for selected competition format
        competition_formats = await CompetitionFormatAdapter().get_competition_formats(
            token,
        )
        if not competition_formats:
            # create default competition formats
            _cf = CompetitionFormatAdapter().get_default_competition_format(
                event["competition_format"],
            )
            await CompetitionFormatAdapter().create_competition_format(token, _cf)
            competition_formats.append(_cf)
        for cf in competition_formats:
            if cf["name"] == event["competition_format"]:
                event["datatype"] = cf["datatype"]
                if cf["datatype"] == "interval_start":
                    event["intervals"] = cf["intervals"]
                elif cf["datatype"] == "individual_sprint":
                    event["time_between_groups"] = cf["time_between_groups"]
                    event["time_between_rounds"] = cf["time_between_rounds"]
                    event["time_between_heats"] = cf["time_between_heats"]
                    event["max_no_of_contestants_in_race"] = cf[
                        "max_no_of_contestants_in_race"
                    ]
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ],
        )
        request_body = copy.deepcopy(event)

        async with ClientSession() as session, session.post(
                f"{EVENT_SERVICE_URL}/events", headers=headers, json=request_body,
            ) as resp:
                if resp.status == HTTPStatus.CREATED:
                    logging.info(f"result - got response {resp}")
                    location = resp.headers[hdrs.LOCATION]
                    result = location.split(os.path.sep)[-1]
                elif resp.status == HTTPStatus.UNAUTHORIZED:
                    err_msg = f"401 Unathorized - {servicename}"
                    raise web.HTTPBadRequest(reason=err_msg)
                else:
                    body = await resp.json()
                    logging.error(f"{servicename} failed - {resp.status} - {body}")
                    raise web.HTTPBadRequest(
                        reason=f"Error - {resp.status}: {body['detail']}.",
                    )
        return result

    async def delete_event(self, token: str, my_id: str) -> str:
        """Delete event function."""
        servicename = "delete_event"
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ],
        )
        url = f"{EVENT_SERVICE_URL}/events/{my_id}"
        async with ClientSession() as session, session.delete(
            url, headers=headers,
        ) as resp:
            if resp.status == HTTPStatus.NO_CONTENT:
                logging.info(f"result - got response {resp}")
            else:
                body = await resp.json()
                logging.error(f"{servicename} failed - {resp.status} - {body}")
                raise web.HTTPBadRequest(
                    reason=f"Error - {resp.status}: {body['detail']}.",
                )
        return str(resp.status)

    async def update_event(self, token: str, my_id: str, request_body: dict) -> str:
        """Update event function."""
        servicename = "update_event"
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ],
        )

        async with ClientSession() as session, session.put(
            f"{EVENT_SERVICE_URL}/events/{my_id}", headers=headers, json=request_body,
        ) as resp:
            result = resp.status
            if resp.status == HTTPStatus.NO_CONTENT:
                logging.info(f"update event - got response {resp}")
            elif resp.status == HTTPStatus.UNAUTHORIZED:
                err_msg = f"401 Unathorized - {servicename}"
                raise web.HTTPBadRequest(reason=err_msg)
            else:
                body = await resp.json()
                logging.error(f"{servicename} failed - {resp.status} - {body}")
                raise web.HTTPBadRequest(
                    reason=f"Error - {resp.status}: {body['detail']}.",
                )
        return str(result)
