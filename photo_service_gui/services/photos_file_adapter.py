"""Module adapter for photos on file storage."""

import logging
from pathlib import Path

from .config_adapter import ConfigAdapter

VISION_ROOT_PATH = f"{Path.cwd()}/photo_service_gui/files"
PHOTOS_FILE_PATH = f"{Path.cwd()}/photo_service_gui/files/DETECT"
PHOTOS_ARCHIVE_PATH = f"{PHOTOS_FILE_PATH}/archive"
PHOTOS_URL_PATH = "files"


class PhotosFileAdapter:

    """Class representing photos."""

    def get_photos_folder_path(self) -> str:
        """Get path to photo folder."""
        if not Path(PHOTOS_FILE_PATH).exists():
            try:
                Path(PHOTOS_FILE_PATH).mkdir(parents=True, exist_ok=True)
            except Exception:
                logging.exception(f"Error creating folder: {PHOTOS_FILE_PATH}")
        # Return the path to the photos folder
        return PHOTOS_FILE_PATH

    def get_photos_archive_folder_path(self) -> str:
        """Get path to photo archive folder."""
        return PHOTOS_ARCHIVE_PATH

    def get_all_photos(self) -> list:
        """Get all path/filename to all photos on file directory."""
        photos = []
        try:
            files = list(Path(PHOTOS_FILE_PATH).iterdir())
            photos = [
                f"{PHOTOS_FILE_PATH}/{f.name}"
                for f in files
                if f.suffix in [".jpg", ".png"] and "_config" not in f.name
            ]
        except FileNotFoundError:
            Path(PHOTOS_FILE_PATH).mkdir(parents=True, exist_ok=True)
        except Exception:
            logging.exception("Error getting photos")
        return photos

    def get_all_photo_urls(self) -> list:
        """Get all url to all photos on file directory."""
        photos = []
        try:
            # loop files in directory and find all photos
            photos.extend(
                f"{PHOTOS_URL_PATH}/CAPTURE/{f.name}"
                for f in Path(PHOTOS_FILE_PATH).iterdir()
                if (
                    f.is_file()
                    and f.suffix in [".jpg", ".png"]
                    and "_config" not in f.name
                    and "_crop" not in f.name
                )
            )
        except FileNotFoundError:
            Path(PHOTOS_FILE_PATH).mkdir(parents=True, exist_ok=True)
        except Exception:
            logging.exception("Error getting photos")
        return photos
    async def get_trigger_line_file_url(self, token: str, event: dict) -> str:
        """Get url to latest trigger line photo."""
        key = "TRIGGER_LINE_CONFIG_FILE"
        file_identifier = await ConfigAdapter().get_config(token, event["id"], key)
        trigger_line_file_name = ""
        try:
            # Lists files in a directory sorted by creation date, newest first."""
            files = list(Path(VISION_ROOT_PATH).iterdir())
            files_with_ctime = [
                (f, (Path(VISION_ROOT_PATH) / f).stat().st_ctime) for f in files
            ]
            sorted_files = [
                f[0] for f in sorted(files_with_ctime, key=lambda x: x[1], reverse=True)
            ]
            trigger_line_files = [
                f for f in sorted_files if file_identifier in f.name
            ]
            # Return url to newest file, archive
            if len(trigger_line_files) == 0:
                return ""
            trigger_line_file_name = trigger_line_files[0].name
            if len(trigger_line_files) > 1:
                for f in trigger_line_files[1:]:
                    move_to_archive(f.name)

        except Exception:
            logging.exception("Error getting photos")
        return f"{PHOTOS_URL_PATH}/{trigger_line_file_name}"

    def get_clip_queue_length(self) -> tuple:
        """Get length of capture and enhance queue."""
        capture_folder = Path(self.get_video_folder_path("CAPTURE"))
        enhance_folder = Path(self.get_video_folder_path("ENHANCE"))

        capture_count = sum(1 for f in capture_folder.iterdir() if f.is_file())
        enhance_count = sum(1 for f in enhance_folder.iterdir() if f.is_file())

        return capture_count, enhance_count

    def get_video_folder_path(self, mode: str) -> str:
        """Get path to video folder."""
        my_folder = Path(f"{VISION_ROOT_PATH}/{mode}")
        if not my_folder.exists():
            my_folder.mkdir(parents=True, exist_ok=True)
        return f"{VISION_ROOT_PATH}/{mode}"


def move_to_archive(filename: str) -> None:
    """Move photo to archive."""
    source_file = Path(PHOTOS_FILE_PATH) / filename
    destination_file = Path(PHOTOS_ARCHIVE_PATH) / source_file.name

    try:
        source_file.rename(destination_file)
    except FileNotFoundError:
        logging.info("Destination folder not found. Creating...")
        Path(PHOTOS_ARCHIVE_PATH).mkdir(parents=True, exist_ok=True)
        source_file.rename(destination_file)
    except Exception:
        logging.exception("Error moving photo to archive.")
