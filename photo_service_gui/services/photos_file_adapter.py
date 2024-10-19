"""Module adapter for photos on file storage."""

import logging
import os
from typing import List

from .config_adapter import ConfigAdapter

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

    async def get_trigger_line_file_url(self, token: str, event: dict) -> str:
        """Get url to latest trigger line photo."""
        key = "TRIGGER_LINE_CONFIG_FILE"
        file_identifier = await ConfigAdapter().get_config(token, event, key)
        trigger_line_file_name = ""
        try:
            # Lists files in a directory sorted by creation date, newest first."""
            files = os.listdir(PHOTOS_FILE_PATH)
            files_with_ctime = [
                (f, os.path.getctime(os.path.join(PHOTOS_FILE_PATH, f))) for f in files
            ]
            sorted_files = [
                f[0] for f in sorted(files_with_ctime, key=lambda x: x[1], reverse=True)
            ]
            trigger_line_files = []
            for f in sorted_files:
                if f.find(file_identifier) != -1:
                    trigger_line_files.append(f)

            # Return url to newest file, archive
            if len(trigger_line_files) == 0:
                return ""
            else:
                trigger_line_file_name = trigger_line_files[0]
                if len(trigger_line_files) > 1:
                    for f in trigger_line_files[1:]:
                        move_to_archive(f)

        except Exception as e:
            logging.error(f"Error getting photos: {e}")
        trigger_line_file_url = f"{PHOTOS_URL_PATH}/{trigger_line_file_name}"
        return trigger_line_file_url

    def move_photo_to_archive(self, filename: str) -> None:
        """Move photo to archive."""
        source_file = f"{PHOTOS_FILE_PATH}/{filename}"
        destination_file = os.path.join(PHOTOS_ARCHIVE_PATH, os.path.basename(filename))

        try:
            os.rename(source_file, destination_file)
        except FileNotFoundError:
            logging.info("Destination folder not found. Creating...")
            os.makedirs(PHOTOS_ARCHIVE_PATH)
            os.rename(source_file, destination_file)
        except Exception as e:
            logging.error(f"Error moving photo to archive: {e}")


def move_to_archive(filename: str) -> None:
    """Move photo to archive."""
    source_file = f"{PHOTOS_FILE_PATH}/{filename}"
    destination_file = os.path.join(PHOTOS_ARCHIVE_PATH, os.path.basename(filename))

    try:
        os.rename(source_file, destination_file)
    except FileNotFoundError:
        logging.info("Destination folder not found. Creating...")
        os.makedirs(PHOTOS_ARCHIVE_PATH)
        os.rename(source_file, destination_file)
    except Exception as e:
        logging.error(f"Error moving photo to archive: {e}")
