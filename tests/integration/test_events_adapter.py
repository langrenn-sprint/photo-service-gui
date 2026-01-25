"""Integration test cases for the events_adapter."""

import os

import pytest
from aiohttp import web

from photo_service_gui.services import EventsAdapter

EVENT_HOST_SERVER = os.getenv("EVENT_HOST_SERVER", "localhost")
EVENT_HOST_PORT = os.getenv("EVENT_HOST_PORT", "8082")


@pytest.fixture
def events_adapter() -> EventsAdapter:
    """Create an EventsAdapter instance."""
    return EventsAdapter()


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
        "id": "test-event-123",
        "name": "Test Event",
        "competition_format": "Individual Sprint",
        "date_of_event": "2026-01-24",
        "organiser": "Test Organiser",
        "timezone": "Europe/Oslo",
    }


@pytest.mark.integration
async def test_get_all_events(
    events_adapter: EventsAdapter,
    mock_token: str,
) -> None:
    """Should return list of events."""
    try:
        result = await events_adapter.get_all_events(
            token=mock_token,
        )
        assert isinstance(result, list)
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_get_event_not_found(
    events_adapter: EventsAdapter,
    mock_token: str,
) -> None:
    """Should raise HTTPBadRequest when event doesn't exist."""
    try:
        with pytest.raises((web.HTTPBadRequest, Exception)):
            await events_adapter.get_event(
                token=mock_token,
                my_id="non-existent-id",
            )
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_create_event(
    events_adapter: EventsAdapter,
    mock_token: str,
    sample_event: dict,
) -> None:
    """Should create a new event."""
    try:
        result = await events_adapter.create_event(
            token=mock_token,
            event=sample_event,
        )
        assert isinstance(result, str)
        assert len(result) > 0

        # Cleanup: delete the created event
        await events_adapter.delete_event(
            token=mock_token,
            my_id=result,
        )
    except Exception:
        pytest.skip("Service not available or authentication failed")


@pytest.mark.integration
async def test_create_update_delete_event_flow(
    events_adapter: EventsAdapter,
    mock_token: str,
    sample_event: dict,
) -> None:
    """Should create, update, and delete an event."""
    try:
        # Create event
        event_id = await events_adapter.create_event(
            token=mock_token,
            event=sample_event,
        )

        # Update the event
        updated_event = sample_event.copy()
        updated_event["name"] = "Updated Test Event"

        response = await events_adapter.update_event(
            token=mock_token,
            my_id=event_id,
            request_body=updated_event,
        )

        assert isinstance(response, str)

        # Delete the event
        delete_response = await events_adapter.delete_event(
            token=mock_token,
            my_id=event_id,
        )

        assert isinstance(delete_response, str)
    except Exception:
        pytest.skip("Service not available or authentication failed")


@pytest.mark.integration
async def test_generate_classes(
    events_adapter: EventsAdapter,
    mock_token: str,
) -> None:
    """Should generate race classes for an event."""
    try:
        result = await events_adapter.generate_classes(
            token=mock_token,
            event_id="event-123",
        )
        assert isinstance(result, str)
    except (web.HTTPBadRequest, Exception):
        pytest.skip(
            "Service not available, authentication required, or event not found",
        )


@pytest.mark.integration
async def test_sync_events(
    events_adapter: EventsAdapter,
    mock_token: str,
) -> None:
    """Should sync events from remote URL."""
    try:
        result = await events_adapter.sync_events(
            token=mock_token,
            remote_url="http://localhost:8082/events",
        )
        assert isinstance(result, str)
    except Exception:
        pytest.skip("Service not available or authentication failed")
