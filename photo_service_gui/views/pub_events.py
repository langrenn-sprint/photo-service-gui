"""Resource module for photo update through ajax."""
import logging

from aiohttp import web

from photo_service_gui.services import FotoService, VisionAIService
from .utils import (
    check_login,
)


class PubEvents(web.View):
    """Class representing the simple photo update service."""

    async def post(self) -> web.Response:
        """Post route function that updates a collection of photos."""
        result = "200"
        try:
            form = await self.request.post()
            action = form["action"]
            event_id = str(form["event_id"])
            user = await check_login(self)
            logging.debug(f"User: {user}")
            if action == "pub":
                res = await FotoService().push_new_photos_from_file(event_id)
                result += f" {res}"
            elif action == "pub_from_file":
                res = await FotoService().push_data_from_file(event_id)
                result += f" {res}"
            elif action == "detect_crossings":
                video_url = form["video_url"]
                res = VisionAIService().detect_crossings_with_ultraltyics(video_url)
                result += f"Analyse fullført: {res}"
        except Exception as e:
            error_reason = str(e)
            if error_reason.startswith("401"):
                return web.HTTPSeeOther(
                    location=f"/login?informasjon=Ingen tilgang, vennligst logg inn på nytt. {e}"
                )
            else:
                logging.error(f"Error: {e}")
                result = f"Det har oppstått en feil - {e.args}"
        return web.Response(text=result)
