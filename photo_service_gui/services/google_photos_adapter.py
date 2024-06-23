"""Module for google photos adapter."""

import json
import logging
import os
from typing import Dict, List

from aiohttp import ClientSession
from aiohttp import hdrs
from aiohttp import web
import google_auth_oauthlib.flow
from multidict import MultiDict

from .config_adapter import ConfigAdapter

GOOGLE_PHOTO_CREDENTIALS_FILE = str(os.getenv("GOOGLE_PHOTO_CREDENTIALS_FILE"))


class GooglePhotosAdapter:
    """Class representing google photos."""

    async def upload_photo_to_google(
        self, token: str, event: dict, g_token: str, photo_list: list, album_id: str
    ) -> str:
        """Upload photo to a specific album in google photos."""
        i = 0
        servicename = "upload_photo_to_album"
        GOOGLE_PHOTO_SERVER = await ConfigAdapter().get_config(
            token, event, "GOOGLE_PHOTO_SERVER"
        )

        try:
            for photo in photo_list:
                # Step 1: Upload the photos to get an uploadToken
                upload_url = f"{GOOGLE_PHOTO_SERVER}/uploads"
                image_type = "image/jpeg"
                headers = {
                    "Authorization": f"Bearer {g_token}",
                    "Content-Type": "application/octet-stream",
                    "X-Goog-Upload-Content-Type": image_type,
                    "X-Goog-Upload-Protocol": "raw",
                    "X-Goog-Upload-File-Name": os.path.basename(photo),
                }

                async with ClientSession() as session:
                    async with session.post(
                        upload_url, data=open_photo_binary(photo), headers=headers
                    ) as response:
                        if response.status != 200:
                            raise Exception(
                                f"Upload step1 failed for {photo} - {response}."
                            )
                        else:
                            logging.info(f"Upload step1 ok - {photo}.")
                        upload_token = await response.text()

                # Step 2: Use the uploadToken to add the photo to the album
                create_item_url = f"{GOOGLE_PHOTO_SERVER}/mediaItems:batchCreate"
                headers = {
                    "Authorization": f"Bearer {g_token}",
                    "Content-Type": "application/json",
                }
                body = json.dumps(
                    {
                        "newMediaItems": [
                            {
                                "description": "Uploaded from photo-service-gui",
                                "simpleMediaItem": {"uploadToken": upload_token},
                            }
                        ],
                        "albumId": album_id,
                    }
                )
                async with ClientSession() as session:
                    async with session.post(
                        create_item_url, data=body, headers=headers
                    ) as response:
                        if response.status != 200:
                            raise Exception(
                                f"Upload step2 failed for {photo} - {response}."
                            )
                        else:
                            logging.info(f"Upload step2 ok - {photo}.")
                i += 1
        except Exception as e:
            logging.error(f"{servicename} failed - {e}")
            raise Exception(f"Error {servicename} - {e}.") from e
        informasjon = f"Lastet opp {i} bilder"
        return informasjon

    async def get_album_items(
        self, token: str, event: dict, g_token: str, album_id: str
    ) -> List:
        """Get all items for an album."""
        album_items = []
        morePages = True
        pageToken = ""
        servicename = "get_album_items"
        GOOGLE_PHOTO_SERVER = await ConfigAdapter().get_config(
            token, event, "GOOGLE_PHOTO_SERVER"
        )
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {g_token}"),
            ]
        )
        request_body = {"albumId": album_id, "pageSize": 100}
        while morePages:
            if pageToken:
                request_body["pageToken"] = pageToken

            async with ClientSession() as session:
                async with session.post(
                    f"{GOOGLE_PHOTO_SERVER}/mediaItems:search",
                    headers=headers,
                    json=request_body,
                ) as resp:
                    logging.debug(f"{servicename} - got response {resp.status}")
                    if resp.status == 200:
                        tmp_album_items = await resp.json()
                    else:
                        body = await resp.json()
                        logging.error(f"{servicename} failed - {resp.status} - {body}")
                        raise web.HTTPBadRequest(
                            reason=f"Error - {resp.status}: {body}."
                        )
            if "nextPageToken" in tmp_album_items.keys():
                pageToken = tmp_album_items["nextPageToken"]
            else:
                morePages = False
            album_items.extend(tmp_album_items["mediaItems"])
        return album_items

    async def get_album(
        self, token: str, event: dict, g_token: str, album_id: str
    ) -> Dict:
        """Get one album."""
        album = {}
        servicename = "get_album"
        GOOGLE_PHOTO_SERVER = await ConfigAdapter().get_config(
            token, event, "GOOGLE_PHOTO_SERVER"
        )
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {g_token}"),
            ]
        )
        async with ClientSession() as session:
            async with session.get(
                f"{GOOGLE_PHOTO_SERVER}/albums/{album_id}", headers=headers
            ) as resp:
                logging.debug(f"{servicename} - got response {resp.status}")
                if resp.status == 200:
                    album = await resp.json()
                else:
                    body = await resp.json()
                    logging.error(f"{servicename} failed - {resp.status} - {body}")
                    raise web.HTTPBadRequest(reason=f"Error - {resp.status}: {body}.")
        return album

    async def get_albums(self, token: str, event: dict, g_token: str) -> List:
        """Get all albums."""
        albums = []
        servicename = "get_albums"
        GOOGLE_PHOTO_SERVER = await ConfigAdapter().get_config(
            token, event, "GOOGLE_PHOTO_SERVER"
        )
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {g_token}"),
            ]
        )
        async with ClientSession() as session:
            async with session.get(
                f"{GOOGLE_PHOTO_SERVER}/albums", headers=headers
            ) as resp:
                logging.debug(f"{servicename} - got response {resp.status}")
                if resp.status == 200:
                    albums = await resp.json()
                else:
                    body = await resp.json()
                    logging.error(f"{servicename} failed - {resp.status} - {body}")
                    raise web.HTTPBadRequest(reason=f"Error - {resp.status}: {body}.")
        return albums

    async def get_auth_request_url(
        self, token: str, event: dict, redirect_url: str
    ) -> str:
        """Get auth URL for request to read from Photos API."""
        # Use the client_secret.json file to identify the application requesting
        # authorization. The client ID (from that file) and access scopes are required.
        GOOGLE_PHOTO_SCOPE = await ConfigAdapter().get_config(
            token, event, "GOOGLE_PHOTO_SCOPE"
        )
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            GOOGLE_PHOTO_CREDENTIALS_FILE, scopes=GOOGLE_PHOTO_SCOPE
        )

        # Indicate where the API server will redirect the user after the user completes
        # the authorization flow. The redirect URI is required. The value must exactly
        # match one of the authorized redirect URIs for the OAuth 2.0 client, which you
        # configured in the API Console. If this value doesn't match an authorized URI,
        # you will get a 'redirect_uri_mismatch' error.
        flow.redirect_uri = redirect_url

        # Generate URL for request to Google's OAuth 2.0 server.
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            login_hint="info.renn.langrenn.kjelsaas@gmail.com",
            state=event["id"],
        )
        return authorization_url

    async def get_g_token(self, user: dict, event: dict, redirect_url: str) -> str:
        """Get token for request to read from Photos API."""
        GOOGLE_PHOTO_SCOPE = await ConfigAdapter().get_config(
            user["token"], event, "GOOGLE_PHOTO_SCOPE"
        )
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            GOOGLE_PHOTO_CREDENTIALS_FILE, scopes=GOOGLE_PHOTO_SCOPE, state=event["id"]
        )
        flow.redirect_uri = redirect_url
        flow.fetch_token(code=user["g_client_id"])

        # Return the credentials.
        return flow.credentials.token


def open_photo_binary(file_path: str) -> bytes:
    """Open photo in binary mode."""
    with open(file_path, "rb") as file:
        return file.read()
