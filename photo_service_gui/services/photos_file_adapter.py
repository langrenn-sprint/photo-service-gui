"""Module adapter for photos on file storage."""

import logging
import os
from typing import List

PHOTOS_FILE_PATH = f"{os.getcwd()}/photo_service_gui/files"
PHOTOS_ARCHIVE_PATH = f"{PHOTOS_FILE_PATH}/archive"
PHOTOS_URL_PATH = "files"


class PhotosFileAdapter:
    """Class representing photos."""

    def get_all_photos(self) -> List:
        """Get all path/filename to all photos on file directory."""
        photos = []
        try:
            # loop files in directory
            for f in os.listdir(PHOTOS_FILE_PATH):
                if f.endswith(".jpg") or f.endswith(".png"):
                    # check that filename not contains _config or _crop
                    if "_config" not in f:
                        photos.append(f"{PHOTOS_FILE_PATH}/{f}")
        except Exception as e:
            logging.error(f"Error getting photos: {e}")
        return photos

    def get_all_photo_urls(self) -> List:
        """Get all url to all photos on file directory."""
        photos = []
        try:
            # loop files in directory and find all photos
            for f in os.listdir(PHOTOS_FILE_PATH):
                if f.endswith(".jpg") or f.endswith(".png"):
                    # check that filename not contains _config or _crop
                    if "_config" not in f and "_crop" not in f:
                        photos.append(f"{PHOTOS_URL_PATH}/{f}")
        except Exception as e:
            logging.error(f"Error getting photos: {e}")
        return photos

    def move_photo_to_archive(self, filename: str) -> None:
        """Move photo to archive."""
        source_file = f"{PHOTOS_FILE_PATH}/{filename}"
        destination_file = os.path.join(PHOTOS_ARCHIVE_PATH, os.path.basename(filename))

        try:
            os.rename(source_file, destination_file)
        except FileNotFoundError:
            print("Destination folder not found. Creating...")
            os.makedirs(PHOTOS_ARCHIVE_PATH)
            os.rename(source_file, destination_file)
        except Exception as e:
            logging.error(f"Error moving photo to archive: {e}")
