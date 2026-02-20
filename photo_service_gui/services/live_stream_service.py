"""Service for managing Google Live Stream API operations."""

import asyncio
import logging
import os
from typing import Any

from dotenv import load_dotenv

from .config_adapter import ConfigAdapter
from .events_adapter import EventsAdapter
from .live_stream_adapter import LiveStreamAdapter
from .service_instance_adapter import ServiceInstanceAdapter


class LiveStreamService:

    """Service for capturing video using Google Live Stream API.

    This service provides an alternative to the traditional Python-based
    video capture (cv2.VideoCapture). It uses Google Cloud Live Stream API
    to capture video streams from SRT Push sources and store them directly
    to cloud storage with configurable clip duration.
    """

    def __init__(
        self,
        project_id: str | None = None,
        location: str | None = None,
        bucket_name: str | None = None,
    ) -> None:
        """Initialize the Live Stream Service.

        Args:
            project_id: Google Cloud project ID. If None, uses config or env var.
            location: Google Cloud region. If None, uses config or env var.
            bucket_name: Cloud Storage bucket name. If None, uses config or env var.

        """
        load_dotenv()

        self.project_id = (
            project_id
            or os.getenv("GOOGLE_CLOUD_PROJECT", "")
        )

        self.location = (
            location
            or os.getenv("GOOGLE_CLOUD_REGION", "europe-north1")
        )

        self.bucket_name = (
            bucket_name
            or os.getenv("GOOGLE_STORAGE_BUCKET", "")
        )

        if not self.project_id:
            error_msg = "GOOGLE_CLOUD_PROJECT must be set"
            raise ValueError(error_msg)

        if not self.bucket_name:
            error_msg = "GOOGLE_STORAGE_BUCKET must be set"
            raise ValueError(error_msg)

        self.adapter = LiveStreamAdapter(self.project_id, self.location)

        logging.info(
            "Initialized LiveStreamService for project=%s, location=%s, bucket=%s",
            self.project_id,
            self.location,
            self.bucket_name,
        )

    async def create_and_start_channel(
        self,
        token: str,
        event: dict,
        name: str,
    ) -> str:
        """Create and start a live stream channel for an event.

        This method creates an SRT Push input endpoint and a channel that
        captures the stream and stores it to cloud storage.

        Args:
            token: Authentication token
            event: The event dictionary
            name: The name of the channel

        Returns:
            A string containing information about the created channel and input:
                - srt_push_url: URL for streaming via SRT Push

        """
        information = ""
        clip_duration = await ConfigAdapter().get_config_int(
            token, event["id"], "VIDEO_CLIP_DURATION",
        )

        # Generate resource IDs
        input_prefix = await ConfigAdapter().get_config(
            token, event["id"], "LIVESTREAM_INPUT_PREFIX",
        )
        input_id = f"{input_prefix}-{name}"
        channel_id = name

        # Create output path in cloud storage
        output_path_template = await ConfigAdapter().get_config(
            token, event["id"], "VIDEO_OUTPUT_PATH_TEMPLATE",
        )
        output_path = output_path_template.format(event_id=event["id"])
        output_uri = f"gs://{self.bucket_name}/{output_path}"

        # register new instance in database
        instance_id = await create_service_instance(
            token,
            event,
            name,
        )
        logging.debug("Registered new service instance with ID: %s", instance_id)


        try:
            # Create input endpoint
            logging.info("Creating input endpoint for event: %s", event["id"])
            input_resource = await asyncio.to_thread(
                self.adapter.create_input,
                input_id=input_id,
            )

            # Create channel
            logging.info("Creating channel for event: %s", event["id"])
            adapter = ConfigAdapter()
            video_bitrate = await adapter.get_config_int(
                token, event["id"], "VIDEO_BITRATE_BPS",
            )
            video_width = await adapter.get_config_int(
                token, event["id"], "VIDEO_WIDTH",
            )
            video_height = await adapter.get_config_int(
                token, event["id"], "VIDEO_HEIGHT",
            )
            video_fps = await adapter.get_config_int(
                token, event["id"], "VIDEO_CLIP_FPS",
            )

            await asyncio.to_thread(
                self.adapter.create_channel,
                channel_id=channel_id,
                input_id=input_id,
                output_uri=output_uri,
                segment_duration=clip_duration,
                video_bitrate_bps=video_bitrate,
                video_width=video_width,
                video_height=video_height,
                video_fps=video_fps,
                audio_codec="aac",
                audio_bitrate_bps=128000,
                audio_channels=2,
                audio_sample_rate=48000,
            )

            # Start channel
            logging.info("Starting channel for event: %s", event["id"])
            result = await asyncio.to_thread(
                self.adapter.start_channel,
                channel_id=channel_id,
            )
            logging.info("Started channel: %s", result)

        except Exception:
            logging.exception(
                "Failed to create and start channel for event: %s", event["id"],
            )
            # Cleanup on failure
            try:
                self.cleanup_resources()
            except Exception:
                logging.exception("Failed to cleanup resources after error")
            raise
        else:
            # Get SRT Push URL from input resource
            srt_push_url = input_resource.uri
            information = f"Suksess. Kanal/input er opprettet. Url: {srt_push_url}"
            logging.info(
                "Successfully created and started channel for event: %s, SRT URL: %s",
                event["name"],
                srt_push_url,
            )

        return information

    def cleanup_resources(self) -> str:
        """Delete all channels.

        Args:
            channel_name: Name of the channel to delete

        Returns:
            Confirmation message upon successful deletion

        """
        channels = self.adapter.list_channels()
        for channel in channels:
            self.delete_channel(channel.name)
        return "Suksess. Alle kanaler er slettet."

    def delete_channel(self, channel_name: str) -> str:
        """Delete a live stream channel by name.

        Args:
            channel_name: Name of the channel to delete

        Returns:
            Confirmation message upon successful deletion

        """
        logging.info("Stopping channel: %s", channel_name)
        try:
            self.adapter.stop_channel(channel_name)
        except Exception:
            logging.warning("Channel %s may not be running.", channel_name)
        logging.info("Deleting channel: %s", channel_name)
        self.adapter.delete_channel(channel_name)
        logging.info("Successfully deleted channel: %s", channel_name)
        return f"Suksess. Kanal {channel_name} er slettet."

    def delete_input(self, input_name: str) -> str:
        """Delete a live stream input by name.

        Args:
            input_name: Name of the input to delete

        Returns:
            Confirmation message upon successful deletion

        """
        logging.info("Deleting input: %s", input_name)
        self.adapter.delete_input(input_name)
        logging.info("Successfully deleted input: %s", input_name)
        return f"Suksess. Input {input_name} er slettet."

    async def get_channel_status(self, channel_id: str) -> dict[str, Any]:
        """Get the status of a live stream channel.

        Args:
            channel_id: The ID of the channel to check status for
        Returns:
            Dictionary containing channel status information

        """
        channel = await asyncio.to_thread(
            self.adapter.get_channel,
            channel_id=channel_id,
        )

        return {
            "channel_id": channel_id,
            "state": channel.streaming_state.name,
            "streaming_error": str(channel.streaming_error)
            if channel.streaming_error
            else None,
        }

    async def list_active_channels(self) -> list[Any]:
        """List all active channels.

        Returns:
            List of Channel objects with all information from the adapter

        """
        return await asyncio.to_thread(self.adapter.list_channels)

    async def list_active_inputs(self) -> list[Any]:
        """List all active inputs.

        Returns:
            List of Input objects with all information from the adapter

        """
        return await asyncio.to_thread(self.adapter.list_inputs)

async def create_service_instance(
    token: str,
    event: dict,
    name: str,
) -> None:
    """Create a service instance dictionary for the video srt_service.

    Args:
        token: Authentication token for database access
        event: The event dictionary
        name: Name of the SRT input

    Returns:
        None

    """
    time_now = EventsAdapter().get_local_time(event, "log")
    service_instance = {
        "service_type": "VIDEO_SERVICE_CAPTURE_SRT",
        "instance_name": name,
        "status": "",
        "host_name": "",
        "action": "",
        "event_id": event["id"],
        "started_at": time_now,
        "last_heartbeat": time_now,
        "metadata": {
            "latest_photo_url": "",
            "trigger_line_xyxyn": await ConfigAdapter().get_config(
                token, event["id"], "TRIGGER_LINE_XYXYN",
            ),
        },
    }
    await ServiceInstanceAdapter().create_service_instance(token, service_instance)


