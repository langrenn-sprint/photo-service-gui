"""Module for user adapter."""

import logging
import os
from http import HTTPStatus

import jwt
from aiohttp import ClientSession, hdrs, web
from aiohttp_session import Session
from multidict import MultiDict

from photo_service_gui.services import (
    GooglePhotosAdapter,
)

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")
USER_SERVICE_URL = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}"


class UserAdapter:

    """Class representing user."""

    async def create_user(
        self,
        token: str,
        role: str,
        username: str,
        password: str,
    ) -> str:
        """Create user function."""
        servicename = "create_user"
        result = ""
        request_body = {
            "role": role,
            "username": username,
            "password": password,
        }
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ],
        )
        async with ClientSession() as session, session.post(
            f"{USER_SERVICE_URL}/users", headers=headers, json=request_body,
        ) as resp:
            if resp.status == HTTPStatus.CREATED:
                logging.info(f"create user - got response {resp}")
                location = resp.headers[hdrs.LOCATION]
                result = location.split(os.path.sep)[-1]
            elif resp.status == HTTPStatus.UNAUTHORIZED:
                raise web.HTTPBadRequest(reason=f"401 Unathorized - {servicename}")
            else:
                logging.error(f"create_user failed - {resp.status}")
                raise web.HTTPBadRequest(reason="Create user failed.")

        return result

    async def delete_user(self, token: str, uid: str) -> int:
        """Delete user function."""
        servicename = "delete_user"
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ],
        )
        url = f"{USER_SERVICE_URL}/users/{uid}"
        async with ClientSession() as session, session.delete(
            url, headers=headers,
        ) as resp:
            pass
        logging.info(f"Delete user: {uid} - res {resp.status}")
        if resp.status == HTTPStatus.NO_CONTENT:
            logging.info(f"result - got response {resp}")
        elif resp.status == HTTPStatus.UNAUTHORIZED:
            raise web.HTTPBadRequest(reason=f"401 Unathorized - {servicename}")
        else:
            logging.error(f"delete_user failed - {resp.status}, {resp}")
            raise web.HTTPBadRequest(reason="Delete user failed.")
        return resp.status

    async def get_all_users(self, token: str) -> list:
        """Get all users function."""
        users = []
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
                (hdrs.AUTHORIZATION, f"Bearer {token}"),
            ],
        )

        async with ClientSession() as session, session.get(
            f"{USER_SERVICE_URL}/users", headers=headers,
        ) as resp:
            logging.info(f"get_all_users - got response {resp.status}")
            if resp.status == HTTPStatus.OK:
                users = await resp.json()
                logging.info(f"users - got response {users}")
            else:
                logging.error(f"Error {resp.status} getting users: {resp} ")
        return users

    async def login(self, username: str, password: str, cookiestorage: Session) -> int:
        """Perform login function."""
        result = 0
        request_body = {
            "username": username,
            "password": password,
        }
        headers = MultiDict(
            [
                (hdrs.CONTENT_TYPE, "application/json"),
            ],
        )
        async with ClientSession() as session, session.post(
            f"{USER_SERVICE_URL}/login", headers=headers, json=request_body,
        ) as resp:
            result = resp.status
            logging.info(f"do login - got response {result}")
            if result == HTTPStatus.OK:
                body = await resp.json()
                token = body["token"]

                # store token to session variable
                cookiestorage["token"] = token
                cookiestorage["name"] = username
                cookiestorage["loggedin"] = True
                cookiestorage["g_jwt"] = ""
                cookiestorage["g_name"] = ""
                cookiestorage["g_loggedin"] = False
                cookiestorage["g_auth_photos"] = False
                cookiestorage["g_scope"] = ""
                cookiestorage["g_client_id"] = ""
                cookiestorage["g_photos_token"] = USER_SERVICE_URL
        return result

    def login_google(self, g_jwt: str, user: dict, cookiestorage: Session) -> int:
        """Login based upon google token."""
        decoded_jwt = jwt.decode(g_jwt, options={"verify_signature": False})

        # store token to session variable
        cookiestorage["token"] = user["token"]
        cookiestorage["name"] = user["name"]
        cookiestorage["loggedin"] = user["loggedin"]
        cookiestorage["g_jwt"] = g_jwt
        cookiestorage["g_name"] = decoded_jwt["name"]
        cookiestorage["g_loggedin"] = True
        cookiestorage["g_auth_photos"] = user["g_auth_photos"]
        cookiestorage["g_scope"] = ""
        cookiestorage["g_client_id"] = ""
        cookiestorage["g_photos_token"] = USER_SERVICE_URL
        return 200

    def login_google_photos(
        self, redirect_url: str, event: dict, user: dict, cookiestorage: Session,
    ) -> int:
        """Login google photos, check that scope is correct."""
        # store to session variable
        cookiestorage["token"] = user["token"]
        cookiestorage["name"] = user["name"]
        cookiestorage["loggedin"] = user["loggedin"]
        cookiestorage["g_jwt"] = user["g_jwt"]
        cookiestorage["g_name"] = user["g_name"]
        cookiestorage["g_loggedin"] = user["g_loggedin"]
        cookiestorage["g_scope"] = user["g_scope"]
        cookiestorage["g_client_id"] = user["g_client_id"]
        if "photoslibrary" in user["g_scope"]:
            cookiestorage["g_auth_photos"] = True
            cookiestorage["g_photos_token"] = GooglePhotosAdapter().get_g_token(
                user, event, redirect_url,
            )
            return HTTPStatus.OK
        # Unathorized
        cookiestorage["g_auth_photos"] = False
        return HTTPStatus.UNAUTHORIZED

    def isloggedin(self, cookiestorage: Session) -> bool:
        """Check if user is logged in function."""
        try:
            result = cookiestorage["loggedin"]
        except Exception:
            result = False
        return result

    def isloggedin_google(self, cookiestorage: Session) -> bool:
        """Check if user is logged in with google function."""
        try:
            result = cookiestorage["loggedin"]
            if result:
                result = cookiestorage["g_loggedin"]
        except Exception:
            result = False
        return result

    def isloggedin_google_photos(self, cookiestorage: Session) -> bool:
        """Check if user has authorized google photos access."""
        try:
            result = cookiestorage["loggedin"]
            if result:
                result = cookiestorage["g_loggedin"]
                if result:
                    result = cookiestorage["g_auth_photos"]
        except Exception:
            result = False
        return result
