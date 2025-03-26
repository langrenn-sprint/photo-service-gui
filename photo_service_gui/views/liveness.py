"""Resource module for liveness resources."""

from aiohttp import web


class Ping(web.View):

    """Class representing ping resource."""

    @staticmethod
    async def get() -> web.Response:
        """Ping route function."""
        return web.Response(text="OK")
