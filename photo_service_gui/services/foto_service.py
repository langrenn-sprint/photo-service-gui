"""Module for foto service."""

import json
import logging

from .albums_adapter import AlbumsAdapter
from .photos_adapter import PhotosAdapter


class FotoService:

    """Class representing foto service."""

    async def delete_all_local_albums(self, token: str, event_id: str) -> str:
        """Delete all local copies of album sync information."""
        albums = await AlbumsAdapter().get_all_albums(token, event_id)
        for album in albums:
            result = await AlbumsAdapter().delete_album(token, album.id)
            logging.info(f"Deleted album with id {album.id}, result {result}")
        return "Alle lokale kopier er slettet."

    async def delete_all_local_photos(self, token: str, event_id: str) -> str:
        """Delete all local copies of photo information."""
        photos = await PhotosAdapter().get_all_photos(token, event_id)
        for photo in photos:
            result = await PhotosAdapter().delete_photo(token, photo["id"])
            logging.info(f"Deleted photo with id {photo['id']}, result {result}")
        return "Alle lokale kopier er slettet."

    async def star_photo(self, token: str, photo_id: str) -> str:
        """Mark photo as starred."""
        photo = await PhotosAdapter().get_photo(token, photo_id)
        photo["starred"] = True
        await PhotosAdapter().update_photo(token, photo["id"], photo)
        return "* Stjerne *"

    async def unstar_photo(self, token: str, photo_id: str) -> str:
        """Unstarr photo."""
        photo = await PhotosAdapter().get_photo(token, photo_id)
        photo["starred"] = False
        await PhotosAdapter().update_photo(token, photo["id"], photo)
        return "* Fjernet *"

    async def update_race_info(self, token: str, event_id: str, form: dict) -> str:
        """Update race information in phostos, biblist."""
        informasjon = ""
        i_count = 0
        for key, value in form.items():
            if key.startswith("biblist_"):
                try:
                    new_biblist = value
                    photo_id = key[8:]
                    old_biblist = form[f"old_biblist_{photo_id}"]
                    if new_biblist != old_biblist:
                        photo = await PhotosAdapter().get_photo(token, photo_id)
                        photo["biblist"] = json.loads(new_biblist)
                        photo["event_id"] = event_id
                        await PhotosAdapter().update_photo(
                            token, photo["id"], photo,
                        )
                        i_count += 1
                except Exception:
                    logging.exception(f"Error reading biblist - {value}.")
                    informasjon += "En Feil oppstod. "
        return f"Oppdatert {i_count} bilder."
