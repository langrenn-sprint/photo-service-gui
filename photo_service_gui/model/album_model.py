"""Album data class module."""

from dataclasses import dataclass

from marshmallow import Schema, fields, post_load

from .changelog import Changelog


@dataclass
class Album:

    """Basic model class."""

    g_id: str
    is_photo_finish: bool
    is_start_registration: bool
    sync_on: bool
    event_id: str
    camera_position: str | None
    changelog: list[Changelog] | None
    cover_photo_url: str | None
    id: str
    last_sync_time: str | None
    place: str | None
    title: str | None

class AlbumSchema(Schema):

    """Album data class."""

    camera_position = fields.String(allow_none=True)
    g_id = fields.String(
        required=True, error_messages={"required": "Google album id is required."},
    )
    is_photo_finish = fields.Boolean(load_default=False)
    is_start_registration = fields.Boolean(load_default=False)
    sync_on = fields.Boolean(load_default=True)
    event_id = fields.String()
    changelog = fields.Nested(Changelog(many=True), allow_none=True)
    cover_photo_url = fields.String(allow_none=True)
    id = fields.String()
    last_sync_time = fields.DateTime(allow_none=True)
    place = fields.String(allow_none=True)
    title = fields.String(allow_none=True)

    @post_load
    def make_user(self, data) -> Album:
        """Post load to return model class."""
        return Album(**data)
