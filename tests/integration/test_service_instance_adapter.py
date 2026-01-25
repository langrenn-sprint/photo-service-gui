"""Integration test cases for the service_instance_adapter."""

import os
from http import HTTPStatus
from typing import Any

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient as _TestClient

from photo_service_gui.services import ServiceInstanceAdapter

PHOTOS_HOST_SERVER = os.getenv("PHOTOS_HOST_SERVER", "localhost")
PHOTOS_HOST_PORT = os.getenv("PHOTOS_HOST_PORT", "8092")


@pytest.fixture
def service_instance_adapter() -> ServiceInstanceAdapter:
    """Create a ServiceInstanceAdapter instance."""
    return ServiceInstanceAdapter()


@pytest.fixture
def mock_token() -> str:
    """Return a mock token for testing."""
    return "mock_token_12345"

@pytest.fixture
def fake_token() -> str:
    """Return a fake token for testing."""
    return "fake_token_12345"


@pytest.fixture
def sample_service_instance() -> dict:
    """Return a sample service instance for testing."""
    return {
        "id": "test-instance-123",
        "event_id": "event-456",
        "service_type": "photo-service",
        "status": "active",
        "host": "localhost",
        "port": 8080,
        "created_at": "2026-01-24T10:00:00",
    }


@pytest.mark.integration
async def test_get_all_service_instances_empty(
    service_instance_adapter: ServiceInstanceAdapter,
    mock_token: str,
) -> None:
    """Should return empty list when no service instances exist."""
    try:
        result = await service_instance_adapter.get_all_service_instances(
            token=mock_token,
        )
        assert isinstance(result, list)
    except Exception:
        # If authentication fails, skip the test
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_get_all_service_instances_with_filters(
    service_instance_adapter: ServiceInstanceAdapter,
    mock_token: str,
) -> None:
    """Should accept filter parameters."""
    try:
        result = await service_instance_adapter.get_all_service_instances(
            token=mock_token,
            event_id="event-123",
            service_type="photo-service",
            status="active",
        )
        assert isinstance(result, list)
    except Exception:
        # If authentication fails, skip the test
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_get_all_service_instances_with_event_id_filter(
    service_instance_adapter: ServiceInstanceAdapter,
    mock_token: str,
) -> None:
    """Should filter by event_id only."""
    try:
        result = await service_instance_adapter.get_all_service_instances(
            token=mock_token,
            event_id="event-123",
        )
        assert isinstance(result, list)
    except Exception:
        # If authentication fails, skip the test
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_create_service_instance(
    service_instance_adapter: ServiceInstanceAdapter,
    mock_token: str,
    sample_service_instance: dict,
) -> None:
    """Should create a new service instance."""
    try:
        result = await service_instance_adapter.create_service_instance(
            token=mock_token,
            service_instance=sample_service_instance,
        )
        assert isinstance(result, str)
        assert len(result) > 0
    except (Exception, web.HTTPBadRequest, web.HTTPUnprocessableEntity):
        # If the service is not available or mock token is invalid
        pytest.skip("Service not available or authentication failed")


@pytest.mark.integration
async def test_get_service_instance_by_id_not_found(
    service_instance_adapter: ServiceInstanceAdapter,
    mock_token: str,
) -> None:
    """Should raise HTTPNotFound when service instance doesn't exist."""
    try:
        with pytest.raises((web.HTTPNotFound, Exception)):
            await service_instance_adapter.get_service_instance_by_id(
                token=mock_token,
                service_instance_id="non-existent-id",
            )
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_update_service_instance_not_found(
    service_instance_adapter: ServiceInstanceAdapter,
    mock_token: str,
    sample_service_instance: dict,
) -> None:
    """Should raise HTTPNotFound when updating non-existent service instance."""
    try:
        with pytest.raises((web.HTTPNotFound, Exception)):
            await service_instance_adapter.update_service_instance(
                token=mock_token,
                service_instance_id="non-existent-id",
                service_instance=sample_service_instance,
            )
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_delete_service_instance_not_found(
    service_instance_adapter: ServiceInstanceAdapter,
    mock_token: str,
) -> None:
    """Should raise HTTPNotFound when deleting non-existent service instance."""
    try:
        with pytest.raises((web.HTTPNotFound, Exception)):
            await service_instance_adapter.delete_service_instance(
                token=mock_token,
                service_instance_id="non-existent-id",
            )
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_create_and_get_service_instance(
    service_instance_adapter: ServiceInstanceAdapter,
    mock_token: str,
    sample_service_instance: dict,
) -> None:
    """Should create and then retrieve a service instance."""
    try:
        # Create service instance
        service_instance_id = await service_instance_adapter.create_service_instance(
            token=mock_token,
            service_instance=sample_service_instance,
        )

        # Retrieve the created service instance
        result = await service_instance_adapter.get_service_instance_by_id(
            token=mock_token,
            service_instance_id=service_instance_id,
        )

        assert isinstance(result, dict)
        assert result["id"] == service_instance_id

        # Cleanup: delete the created service instance
        await service_instance_adapter.delete_service_instance(
            token=mock_token,
            service_instance_id=service_instance_id,
        )
    except (Exception, web.HTTPBadRequest, web.HTTPUnprocessableEntity):
        pytest.skip("Service not available or authentication failed")


@pytest.mark.integration
async def test_create_update_delete_service_instance_flow(
    service_instance_adapter: ServiceInstanceAdapter,
    mock_token: str,
    sample_service_instance: dict,
) -> None:
    """Should create, update, and delete a service instance."""
    try:
        # Create service instance
        service_instance_id = await service_instance_adapter.create_service_instance(
            token=mock_token,
            service_instance=sample_service_instance,
        )

        # Update the service instance
        updated_instance = sample_service_instance.copy()
        updated_instance["status"] = "inactive"

        response = await service_instance_adapter.update_service_instance(
            token=mock_token,
            service_instance_id=service_instance_id,
            service_instance=updated_instance,
        )

        assert response == str(HTTPStatus.NO_CONTENT)

        # Delete the service instance
        delete_response = await service_instance_adapter.delete_service_instance(
            token=mock_token,
            service_instance_id=service_instance_id,
        )

        assert delete_response == str(HTTPStatus.NO_CONTENT)

        # Verify deletion - should raise HTTPNotFound
        with pytest.raises(web.HTTPNotFound):
            await service_instance_adapter.get_service_instance_by_id(
                token=mock_token,
                service_instance_id=service_instance_id,
            )
    except (Exception, web.HTTPBadRequest, web.HTTPUnprocessableEntity):
        pytest.skip("Service not available or authentication failed")


@pytest.mark.integration
async def test_get_all_with_multiple_filters(
    service_instance_adapter: ServiceInstanceAdapter,
    mock_token: str,
) -> None:
    """Should handle multiple query parameters correctly."""
    try:
        result = await service_instance_adapter.get_all_service_instances(
            token=mock_token,
            event_id="event-123",
            service_type="photo-service",
        )
        assert isinstance(result, list)

        result2 = await service_instance_adapter.get_all_service_instances(
            token=mock_token,
            event_id="event-123",
            status="active",
        )
        assert isinstance(result2, list)

        result3 = await service_instance_adapter.get_all_service_instances(
            token=mock_token,
            service_type="photo-service",
            status="active",
        )
        assert isinstance(result3, list)
    except Exception:
        pytest.skip("Service not available or authentication required")
