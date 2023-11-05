"""Module for google cloud storage adapter."""
import logging
import os

from google.cloud import storage  # type: ignore[attr-defined]

from .events_adapter import EventsAdapter

GOOGLE_STORAGE_BUCKET = EventsAdapter().get_global_setting("GOOGLE_STORAGE_BUCKET")


class GoogleCloudStorageAdapter:
    """Class representing google cloud storage."""
    def upload_blob(self, source_file_name, folder_name) -> None:
        """Uploads a file to the bucket."""
        servicename = "GoogleCloudStorageAdapter.upload_blob"
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(GOOGLE_STORAGE_BUCKET)
            destination_blob_name = f"{os.path.basename(source_file_name)}"
            blob = bucket.blob(destination_blob_name)

            blob.upload_from_filename(source_file_name)
            logging.info(f"{servicename} File {source_file_name} uploaded to {destination_blob_name}.")
        except Exception as err:
            logging.error(f"{servicename}, file: {source_file_name}. Error: {err}")
            raise err
