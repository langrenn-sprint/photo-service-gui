"""Resource module for login view."""

import logging
import os
from http import HTTPStatus

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import new_session

from photo_service_gui.services import UserAdapter

from .utils import check_login, check_login_open


class Login(web.View):

    """Class representing the main view."""

    async def get(self) -> web.Response:
        """Get route function that return the index page."""
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

        user = await check_login_open(self)

        event = {"name": "Administrasjon", "organiser": "Ikke valgt"}

        return await aiohttp_jinja2.render_template_async(
            "login.html",
            self.request,
            {
                "action": action,
                "GOOGLE_OAUTH_CLIENT_ID": str(os.getenv("GOOGLE_OAUTH_CLIENT_ID")),
                "lopsinfo": "Login",
                "event": event,
                "event_id": event_id,
                "informasjon": informasjon,
                "username": user["name"],
            },
        )

    async def post(self) -> web.Response:
        """Get route function that return the index page."""
        informasjon = ""
        result = 0
        logging.info(f"Login: {self}")

        try:
            form = await self.request.post()
            try:
                event_id = self.request.rel_url.query["event_id"]
                logging.info(f"Event: {event_id}")
            except Exception:
                event_id = ""
            try:
                action = self.request.rel_url.query["action"]
            except Exception:
                action = ""
            # Perform login
            if action == "login":
                session = await new_session(self.request)
                result = await UserAdapter().login(
                    str(form["username"]), str(form["password"]), session,
                )
                if result == HTTPStatus.OK:
                    informasjon = "Innlogget!"
                else:
                    informasjon = f"Innlogging feilet - {result}"
            elif action == "g_login":
                user = await check_login(self)
                g_jwt = str(form["g_jwt"])
                # get public key from google and store in session
                session = await new_session(self.request)
                result = UserAdapter().login_google(g_jwt, user, session)
                if result == HTTPStatus.OK:
                    informasjon = "Innlogget Google!"
                else:
                    informasjon = f"Innlogging feilet - {result}"

            event = {"name": "Langrenn", "organiser": "Ikke valgt"}
            if result != HTTPStatus.OK:
                return await aiohttp_jinja2.render_template_async(
                    "login.html",
                    self.request,
                    {
                        "lopsinfo": "Login resultat",
                        "event": event,
                        "event_id": event_id,
                        "informasjon": informasjon,
                    },
                )
        except Exception as e:
            logging.exception("Error")
            informasjon = f"Det har oppstått en feil - {e.args}."
        return web.HTTPSeeOther(location=f"/?informasjon={informasjon}")
