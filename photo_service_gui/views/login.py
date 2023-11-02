"""Resource module for login view."""
import logging
import os

from aiohttp import web
import aiohttp_jinja2
from aiohttp_session import new_session

from photo_service_gui.services import UserAdapter
from .utils import check_login_open


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
        GOOGLE_OAUTH_CLIENT_ID = str(os.getenv("GOOGLE_OAUTH_CLIENT_ID"))

        return await aiohttp_jinja2.render_template_async(
            "login.html",
            self.request,
            {
                "action": action,
                "GOOGLE_OAUTH_CLIENT_ID": GOOGLE_OAUTH_CLIENT_ID,
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
        logging.debug(f"Login: {self}")

        try:
            form = await self.request.post()
            try:
                event_id = self.request.rel_url.query["event_id"]
                logging.debug(f"Event: {event_id}")
            except Exception:
                event_id = ""
            # Perform google login
            user = await check_login_open(self)
            g_jwt = str(form["g_jwt"])
            # get public key from google and store in session
            session = await new_session(self.request)
            result = UserAdapter().login_google(g_jwt, user, session)
            if result == 200:
                informasjon = "Innlogget Google!"
            else:
                informasjon = f"Innlogging feilet - {result}"

            event = {"name": "Langrenn", "organiser": "Ikke valgt"}
            if result != 200:
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
            logging.error(f"Error: {e}")
            informasjon = f"Det har oppstått en feil - {e.args}."
            result = 400
        return web.HTTPSeeOther(location=f"/?informasjon={informasjon}")
