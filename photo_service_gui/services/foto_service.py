"""Module for foto service."""

import datetime
import json
import logging
import os
from typing import Dict, List

from aiohttp import web
import piexif

from .ai_image_service import AiImageService
from .albums_adapter import Album, AlbumsAdapter
from .config_adapter import ConfigAdapter
from .events_adapter import EventsAdapter
from .google_cloud_storage_adapter import GoogleCloudStorageAdapter
from .google_photos_adapter import GooglePhotosAdapter
from .google_pub_sub_adapter import GooglePubSubAdapter
from .photos_adapter import PhotosAdapter
from .photos_file_adapter import PhotosFileAdapter
from .status_adapter import StatusAdapter


class FotoService:
    """Class representing foto service."""

    async def delete_all_local_albums(self, token: str, event_id: str) -> str:
        """Delete all local copies of album sync information."""
        albums = await AlbumsAdapter().get_all_albums(token, event_id)
        for album in albums:
            result = await AlbumsAdapter().delete_album(token, album.id)
            logging.debug(f"Deleted album with id {album.id}, result {result}")
        return "Alle lokale kopier er slettet."

    async def delete_all_local_photos(self, token: str, event_id: str) -> str:
        """Delete all local copies of photo information."""
        photos = await PhotosAdapter().get_all_photos(token, event_id)
        for photo in photos:
            result = await PhotosAdapter().delete_photo(token, photo["id"])
            logging.debug(f"Deleted photo with id {photo['id']}, result {result}")
        return "Alle lokale kopier er slettet."

    async def star_photo(self, token: str, photo_id: str, starred: bool) -> str:
        """Mark photo as starred, or unstarr."""
        informasjon = ""
        photo = await PhotosAdapter().get_photo(token, photo_id)
        photo["starred"] = starred
        result = await PhotosAdapter().update_photo(token, photo["id"], photo)
        logging.debug(f"Updated photo with id {photo_id} - {result}")
        if starred:
            informasjon = "Foto er stjernemerket."
        else:
            informasjon = "Stjernemerke fjernet."
        return informasjon

    async def add_album_for_synk(
        self, token: str, g_token: str, event: dict, g_album_id: str
    ) -> int:
        """Create album for synk."""
        g_album = await GooglePhotosAdapter().get_album(
            token, event, g_token, g_album_id
        )

        # check if album already has been synced, if not create new
        album = await AlbumsAdapter().get_album_by_g_id(token, g_album_id)
        if album:
            raise web.HTTPBadRequest(reason="Error - album eksisterer allerede.")
        else:
            # create album instance
            album = Album(
                g_album_id,
                False,
                False,
                True,
                event["id"],
                "",
                None,
                g_album["coverPhotoBaseUrl"],
                None,
                None,
                "",
                g_album["title"],
            )
            resC = await AlbumsAdapter().create_album(token, album)
            logging.debug(f"Created album, local copy {resC}")
        return 200

    async def update_race_info(self, token: str, event_id: str, form: dict) -> str:
        """Update race information in phostos, biblist."""
        informasjon = ""
        iCount = 0
        for key in form.keys():
            if key.startswith("biblist_"):
                try:
                    new_biblist = form[key]
                    photo_id = key[8:]
                    old_biblist = form[f"old_biblist_{photo_id}"]
                    if new_biblist != old_biblist:
                        photo = await PhotosAdapter().get_photo(token, photo_id)
                        photo["biblist"] = json.loads(new_biblist)
                        result = await PhotosAdapter().update_photo(
                            token, photo["id"], photo
                        )
                        iCount += 1
                        logging.debug(
                            f"Updated photo with id {photo_id} for event {event_id} - {result}"
                        )
                except Exception as e:
                    logging.error(f"Error reading biblist - {form[key]}: {e}")
                    informasjon += "En Feil oppstod. "
        informasjon = f"Oppdatert {iCount} bilder."
        return informasjon

    async def sync_photos_from_google(
        self,
        user: dict,
        event: dict,
    ) -> str:
        """Get photos from google and sync with local database."""
        informasjon = ""
        i_c = 0
        i_u = 0
        sync_albums = await AlbumsAdapter().get_all_albums(user["token"], event["id"])
        for sync_album in sync_albums:
            album_items = await GooglePhotosAdapter().get_album_items(
                user["token"], event, user["g_photos_token"], sync_album.g_id
            )
            for g_photo in album_items:  # type: ignore
                creation_time = g_photo["mediaMetadata"]["creationTime"]
                # update or create record in db
                try:
                    photo = await PhotosAdapter().get_photo_by_g_id(
                        user["token"], g_photo["id"]
                    )
                except Exception:
                    photo = {}
                if photo:
                    # update existing photo
                    photo["name"] = g_photo["filename"]
                    photo["g_product_url"] = g_photo["productUrl"]
                    photo["g_base_url"] = g_photo["baseUrl"]
                    photo["is_photo_finish"] = sync_album.is_photo_finish
                    photo["is_start_registration"] = sync_album.is_start_registration
                    photo_id = await PhotosAdapter().update_photo(
                        user["token"], photo["id"], photo
                    )
                    logging.debug(f"Created photo with id {photo_id}")
                    i_u += 1
                else:
                    # create new photo
                    request_body = {
                        "name": g_photo["filename"],
                        "is_photo_finish": sync_album.is_photo_finish,
                        "is_start_registration": sync_album.is_start_registration,
                        "starred": False,
                        "event_id": event["id"],
                        "creation_time": format_zulu_time(
                            user["token"], event, creation_time
                        ),
                        "information": sync_album.title,
                        "race_id": "",
                        "raceclass": "",
                        "biblist": [],
                        "clublist": [],
                        "g_id": g_photo["id"],
                        "g_product_url": g_photo["productUrl"],
                        "g_base_url": g_photo["baseUrl"],
                    }

                    # new photo - analyze content
                    request_body[
                        "ai_information"
                    ] = AiImageService().analyze_photo_with_google_for_langrenn(
                        user["token"], event, f"{g_photo['baseUrl']}=w800-h800"
                    )

                    photo_id = await PhotosAdapter().create_photo(
                        user["token"], request_body
                    )
                    logging.debug(f"Created photo with id {photo_id}")
                    i_c += 1

            # update album register
            sync_album.last_sync_time = EventsAdapter().get_local_datetime_now(event)
            resU = await AlbumsAdapter().update_album(
                user["token"], sync_album.id, sync_album
            )
            logging.debug(f"Synked album - {sync_album.g_id}, stored locally {resU}")

        informasjon = (
            f"Synkronisert bilder fra Google. {i_u} oppdatert og {i_c} opprettet."
        )
        return informasjon

    async def push_new_photos_from_file(self, token: str, event: dict) -> str:
        """Push photos to cloud storage, analyze and publish."""
        i_photo_count = 0
        informasjon = ""
        new_photos = PhotosFileAdapter().get_all_photos()

        # loop photos and group crops with main photo - only upload complete pairs
        new_photos_grouped = group_photos(new_photos)
        for x in new_photos_grouped:
            group = new_photos_grouped[x]
            if group["main"] and group["crop"]:
                # upload photo to cloud storage
                url_main = GoogleCloudStorageAdapter().upload_blob(group["main"], "")
                url_crop = GoogleCloudStorageAdapter().upload_blob(group["crop"], "")

                # analyze photo with Vision AI
                ai_information = (
                    AiImageService().analyze_photo_with_google_for_langrenn_v2(
                        token, event, url_main, url_crop
                    )
                )

                pub_message = {
                    "ai_information": ai_information,
                    "crop_url": url_crop,
                    "event_id": event["id"],
                    "photo_info": get_image_description(group["main"]),
                    "photo_url": url_main,
                }
                # archive photos
                PhotosFileAdapter().move_photo_to_archive(
                    os.path.basename(group["main"])
                )
                PhotosFileAdapter().move_photo_to_archive(
                    os.path.basename(group["crop"])
                )

                # publish info to pubsub
                result = await GooglePubSubAdapter().publish_message(
                    json.dumps(pub_message)
                )
                logging.debug(f"Published message {result} to pubsub.")
                informasjon = url_main
                i_photo_count += 1
        if i_photo_count > 0:
            await StatusAdapter().create_status(
                token, event, "video_status", f"Bilder lastet opp: {i_photo_count}"
            )

        return informasjon


def group_photos(photo_list: List[str]) -> Dict[str, Dict[str, str]]:
    """Create a dictionary where the photos are grouped by main and crop."""
    photo_dict = {}
    for photo_name in photo_list:
        if "_crop" in photo_name:
            main_photo = photo_name.replace("_crop", "")
            if main_photo not in photo_dict:
                photo_dict[main_photo] = {"main": "", "crop": photo_name}
            else:
                photo_dict[main_photo] = {"main": main_photo, "crop": photo_name}
        elif photo_name not in photo_dict:
            photo_dict[photo_name] = {"main": photo_name, "crop": ""}
        else:
            photo_dict[photo_name] = {
                "main": photo_name,
                "crop": photo_dict[photo_name]["crop"],
            }
    return photo_dict


async def format_zulu_time(token: str, event: dict, timez: str) -> str:
    """Convert from zulu time to normalized time - string formats."""
    # TODO: Move to properties
    pattern = "%Y-%m-%dT%H:%M:%SZ"
    TIME_ZONE_OFFSET_G_PHOTOS = await ConfigAdapter().get_config(
        token, event, "TIME_ZONE_OFFSET_G_PHOTOS"
    )
    try:
        t1 = datetime.datetime.strptime(timez, pattern)
        # calculate new time
        delta_seconds = int(TIME_ZONE_OFFSET_G_PHOTOS) * 3600  # type: ignore
        t2 = t1 + datetime.timedelta(seconds=delta_seconds)
    except ValueError:
        logging.debug(f"Got error parsing time {ValueError}")
        return ""

    time = f"{t2.strftime('%Y')}-{t2.strftime('%m')}-{t2.strftime('%d')}T{t2.strftime('%X')}"
    return time


def get_image_description(file_path: str) -> dict:
    """Get image description from EXIF data."""
    try:
        # Load the EXIF data from the image
        exif_dict = piexif.load(file_path)

        # Get the ImageDescription from the '0th' IFD
        image_description = exif_dict["0th"].get(piexif.ImageIFD.ImageDescription)

        # The ImageDescription is a bytes object, so decode it to a string
        image_description = image_description.decode("utf-8")

        # The ImageDescription is a JSON string, so parse it to a dictionary
        image_info = json.loads(image_description)
    except Exception as e:
        logging.error(f"Error reading image description - {file_path}: {e}")
        image_info = {}

    return image_info
