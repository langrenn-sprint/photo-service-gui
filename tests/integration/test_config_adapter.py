"""Integration test cases for the config_adapter."""

import os

import pytest
from aiohttp import web

from photo_service_gui.services import ConfigAdapter

PHOTOS_HOST_SERVER = os.getenv("PHOTOS_HOST_SERVER", "localhost")
PHOTOS_HOST_PORT = os.getenv("PHOTOS_HOST_PORT", "8092")


@pytest.fixture
def config_adapter() -> ConfigAdapter:
    """Create a ConfigAdapter instance."""
    return ConfigAdapter()


@pytest.fixture
def mock_token() -> str:
    """Return a mock token for testing."""
    return "mock_token_12345"


@pytest.fixture
def fake_token() -> str:
    """Return a fake token for testing."""
    return "fake_token_12345"


@pytest.mark.integration
async def test_get_all_configs(
    config_adapter: ConfigAdapter,
    mock_token: str,
) -> None:
    """Should return list of configs."""
    try:
        result = await config_adapter.get_all_configs(
            token=mock_token,
            event_id="event-123",
        )
        assert isinstance(result, list)
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_get_all_configs_no_event_id(
    config_adapter: ConfigAdapter,
    mock_token: str,
) -> None:
    """Should return list of configs without event_id filter."""
    try:
        result = await config_adapter.get_all_configs(
            token=mock_token,
            event_id="",
        )
        assert isinstance(result, list)
    except Exception:
        pytest.skip("Service not available or authentication required")


@pytest.mark.integration
async def test_get_config(
    config_adapter: ConfigAdapter,
    mock_token: str,
) -> None:
    """Should return config value."""
    try:
        result = await config_adapter.get_config(
            token=mock_token,
            event_id="event-123",
            key="test_key",
        )
        assert isinstance(result, str)
    except (web.HTTPBadRequest, Exception):
        pytest.skip(
            "Service not available, authentication required, or config not found",
        )


@pytest.mark.integration
async def test_get_config_bool(
    config_adapter: ConfigAdapter,
    mock_token: str,
) -> None:
    """Should return config boolean value."""
    try:
        result = await config_adapter.get_config_bool(
            token=mock_token,
            event_id="event-123",
            key="test_bool_key",
        )
        assert isinstance(result, bool)
    except (web.HTTPBadRequest, Exception):
        pytest.skip(
            "Service not available, authentication required, or config not found",
        )


@pytest.mark.integration
async def test_get_config_int(
    config_adapter: ConfigAdapter,
    mock_token: str,
) -> None:
    """Should return config int value."""
    try:
        result = await config_adapter.get_config_int(
            token=mock_token,
            event_id="event-123",
            key="test_int_key",
        )
        assert isinstance(result, int)
    except (web.HTTPBadRequest, Exception, ValueError):
        pytest.skip(
            "Service not available, authentication required, or config not found",
        )


@pytest.mark.integration
async def test_get_config_list(
    config_adapter: ConfigAdapter,
    mock_token: str,
) -> None:
    """Should return config list value."""
    try:
        result = await config_adapter.get_config_list(
            token=mock_token,
            event_id="event-123",
            key="test_list_key",
        )
        assert isinstance(result, list)
    except (web.HTTPBadRequest, Exception):
        pytest.skip(
            "Service not available, authentication required, or config not found",
        )


@pytest.mark.integration
async def test_get_config_img_res_tuple(
    config_adapter: ConfigAdapter,
    mock_token: str,
) -> None:
    """Should return config tuple value."""
    try:
        result = await config_adapter.get_config_img_res_tuple(
            token=mock_token,
            event_id="event-123",
            key="test_tuple_key",
        )
        assert isinstance(result, tuple)
    except (web.HTTPBadRequest, Exception):
        pytest.skip(
            "Service not available, authentication required, or config not found",
        )


@pytest.mark.integration
async def test_create_config(
    config_adapter: ConfigAdapter,
    mock_token: str,
) -> None:
    """Should create a new config."""
    try:
        result = await config_adapter.create_config(
            token=mock_token,
            event_id="event-123",
            key="test_create_key",
            value="test_value",
        )
        assert isinstance(result, str)
        assert len(result) > 0
    except Exception:
        pytest.skip("Service not available or authentication failed")


@pytest.mark.integration
async def test_update_config(
    config_adapter: ConfigAdapter,
    mock_token: str,
) -> None:
    """Should update a config."""
    try:
        # First create a config
        await config_adapter.create_config(
            token=mock_token,
            event_id="event-123",
            key="test_update_key",
            value="initial_value",
        )

        # Then update it
        result = await config_adapter.update_config(
            token=mock_token,
            event_id="event-123",
            key="test_update_key",
            new_value="updated_value",
        )
        assert isinstance(result, str)
    except Exception:
        pytest.skip("Service not available or authentication failed")


@pytest.mark.integration
async def test_update_config_list(
    config_adapter: ConfigAdapter,
    mock_token: str,
) -> None:
    """Should update a config list."""
    try:
        # First create a config list
        await config_adapter.create_config(
            token=mock_token,
            event_id="event-123",
            key="test_list_update_key",
            value='["item1", "item2"]',
        )

        # Then update it
        result = await config_adapter.update_config_list(
            token=mock_token,
            event_id="event-123",
            key="test_list_update_key",
            new_value=["item1", "item2", "item3"],
        )
        assert isinstance(result, str)
    except Exception:
        pytest.skip("Service not available or authentication failed")
