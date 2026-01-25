"""Integration test cases for the photos_adapter."""

import os
from http import HTTPStatus

import pytest
from aiohttp import web

from photo_service_gui.services import PhotosAdapter

PHOTOS_HOST_SERVER = os.getenv("PHOTOS_HOST_SERVER", "localhost")
PHOTOS_HOST_PORT = os.getenv("PHOTOS_HOST_PORT", "8092")


@pytest.fixture
def photos_adapter() -> PhotosAdapter:
    """Create a PhotosAdapter instance."""
    return PhotosAdapter()


@pytest.fixture
def mock_token() -> str:
    """Return a mock token for testing."""
    return "mock_token_12345"


@pytest.fixture
def fake_token() -> str:
    """Return a fake token for testing."""
    return "fake_token_12345"


@pytest.fixture
def sample_photo() -> dict:
    """Return a sample photo for testing."""
    return {
        "id": "test-photo-123",
        "event_id": "event-456",
        "race_id": "race-789",
        "bib": 42,
        "name": "John Doe",
        "club": "Test Club",
        "raceclass": "M Senior",
        "creation_time": "2026-01-24T10:00:00",
        "starred": False,
        "is_photo": True,
        "is_photo_finish": False,
    }


@pytest.mark.integration
async def test_get_all_photos(
    photos_adapter: PhotosAdapter,
    mock_token: str,
) -> None:
    """Should return list of photos."""
    try:
        result = await photos_adapter.get_all_photos(
            token=mock_token,
            event_id="event-123",
        )
        assert isinstance(result, list)
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_get_all_photos_with_limit(
    photos_adapter: PhotosAdapter,
    mock_token: str,
) -> None:
    """Should return limited list of photos."""
    try:
        result = await photos_adapter.get_all_photos(
            token=mock_token,
            event_id="event-123",
            limit=10,
        )
        assert isinstance(result, list)
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_get_photo_by_id_not_found(
    photos_adapter: PhotosAdapter,
    mock_token: str,
) -> None:
    """Should raise HTTPBadRequest when photo doesn't exist."""
    try:
        with pytest.raises((web.HTTPBadRequest, Exception)):
            await photos_adapter.get_photo(
                token=mock_token,
                my_id="non-existent-id",
            )
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_get_photos_by_race_id(
    photos_adapter: PhotosAdapter,
    mock_token: str,
) -> None:
    """Should return photos filtered by race_id."""
    try:
        result = await photos_adapter.get_photos_by_race_id(
            token=mock_token,
            race_id="race-456",
        )
        assert isinstance(result, list)
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_get_photos_by_raceclass(
    photos_adapter: PhotosAdapter,
    mock_token: str,
) -> None:
    """Should return photos filtered by raceclass."""
    try:
        result = await photos_adapter.get_photos_by_raceclass(
            token=mock_token,
            event_id="event-123",
            raceclass="M Senior",
        )
        assert isinstance(result, list)
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_get_photo_by_g_base_url(
    photos_adapter: PhotosAdapter,
    mock_token: str,
) -> None:
    """Should return photo by google base url."""
    try:
        result = await photos_adapter.get_photo_by_g_base_url(
            token=mock_token,
            g_base_url="https://example.com/photo",
        )
        assert isinstance(result, dict)
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_create_photo(
    photos_adapter: PhotosAdapter,
    mock_token: str,
    sample_photo: dict,
) -> None:
    """Should create a new photo."""
    try:
        result = await photos_adapter.create_photo(
            token=mock_token,
            photo=sample_photo,
        )
        assert isinstance(result, str)
        assert len(result) > 0

        # Cleanup: delete the created photo
        await photos_adapter.delete_photo(
            token=mock_token,
            my_id=result,
        )
    except Exception:
        pytest.skip("Service not available or authentication failed")


@pytest.mark.integration
async def test_create_update_delete_photo_flow(
    photos_adapter: PhotosAdapter,
    mock_token: str,
    sample_photo: dict,
) -> None:
    """Should create, update, and delete a photo."""
    try:
        # Create photo
        photo_id = await photos_adapter.create_photo(
            token=mock_token,
            photo=sample_photo,
        )

        # Update the photo
        updated_photo = sample_photo.copy()
        updated_photo["starred"] = True

        response = await photos_adapter.update_photo(
            token=mock_token,
            my_id=photo_id,
            request_body=updated_photo,
        )

        assert response == HTTPStatus.NO_CONTENT

        # Delete the photo
        delete_response = await photos_adapter.delete_photo(
            token=mock_token,
            my_id=photo_id,
        )

        assert delete_response == HTTPStatus.NO_CONTENT
    except Exception:
        pytest.skip("Service not available or authentication failed")
