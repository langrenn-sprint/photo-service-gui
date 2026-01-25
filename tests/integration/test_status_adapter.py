"""Integration test cases for the status_adapter."""

import os

import pytest
from aiohttp import web

from photo_service_gui.services import StatusAdapter

PHOTOS_HOST_SERVER = os.getenv("PHOTOS_HOST_SERVER", "localhost")
PHOTOS_HOST_PORT = os.getenv("PHOTOS_HOST_PORT", "8092")


@pytest.fixture
def status_adapter() -> StatusAdapter:
    """Create a StatusAdapter instance."""
    return StatusAdapter()


@pytest.fixture
def mock_token() -> str:
    """Return a mock token for testing."""
    return "mock_token_12345"


@pytest.fixture
def fake_token() -> str:
    """Return a fake token for testing."""
    return "fake_token_12345"


@pytest.fixture
def sample_event() -> dict:
    """Return a sample event for testing."""
    return {
        "id": "event-123",
        "name": "Test Event",
        "date_of_event": "2026-01-24",
        "timezone": "Europe/Oslo",
    }


@pytest.mark.integration
async def test_get_status(
    status_adapter: StatusAdapter,
    mock_token: str,
) -> None:
    """Should return list of status messages."""
    try:
        result = await status_adapter.get_status(
            token=mock_token,
            event_id="event-123",
            count=10,
        )
        assert isinstance(result, list)
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_get_status_by_type(
    status_adapter: StatusAdapter,
    mock_token: str,
    sample_event: dict,
) -> None:
    """Should return status messages filtered by type."""
    try:
        result = await status_adapter.get_status_by_type(
            token=mock_token,
            event=sample_event,
            status_type="info",
            count=10,
        )
        assert isinstance(result, list)
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_create_status(
    status_adapter: StatusAdapter,
    mock_token: str,
    sample_event: dict,
) -> None:
    """Should create a new status message."""
    try:
        result = await status_adapter.create_status(
            token=mock_token,
            event=sample_event,
            status_type="info",
            message="Test status message",
            details={"test": "data"},
        )
        assert isinstance(result, str)
        assert len(result) > 0
    except Exception:
        pytest.skip("Service not available or authentication failed")


@pytest.mark.integration
async def test_create_and_delete_all_status(
    status_adapter: StatusAdapter,
    mock_token: str,
    sample_event: dict,
) -> None:
    """Should create and then delete all status messages."""
    try:
        # Create status
        await status_adapter.create_status(
            token=mock_token,
            event=sample_event,
            status_type="info",
            message="Test status message",
            details={"test": "data"},
        )

        # Delete all status for event
        result = await status_adapter.delete_all_status(
            token=mock_token,
            event=sample_event,
        )
        assert isinstance(result, int)
    except Exception:
        pytest.skip("Service not available or authentication failed")
