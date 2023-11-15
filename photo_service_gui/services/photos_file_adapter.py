"""Module adapter for photos on file storage."""
import logging
import os
from typing import List

from .events_adapter import EventsAdapter

PHOTOS_FILE_PATH = EventsAdapter().get_global_setting("PHOTOS_FILE_PATH")
PHOTOS_ARCHIVE_PATH = EventsAdapter().get_global_setting("PHOTOS_ARCHIVE_PATH")


class PhotosFileAdapter:
    """Class representing photos."""

    def get_all_photos(self) -> List:
        """Get all path/filename to all photos on file directory."""
        photos = []
        try:
            # loop files in directory
            for filename in os.listdir(PHOTOS_FILE_PATH):
                photos.append(f"{PHOTOS_FILE_PATH}/{filename}")
        except Exception as e:
            logging.error(f"Error getting photos: {e}")
        return photos

    def move_photo_to_archive(self, filename: str) -> None:
        """Move photo to archive."""
        try:
            os.rename(f"{PHOTOS_FILE_PATH}/{filename}", f"{PHOTOS_ARCHIVE_PATH}/{filename}")
        except Exception as e:
            logging.error(f"Error moving photo to archive: {e}")
