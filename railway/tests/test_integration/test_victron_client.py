# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/tests/test_integration/test_victron_client.py
# PURPOSE: Unit tests for Victron VRM API client
# ═══════════════════════════════════════════════════════════════════════════

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import asyncio

from src.integrations.victron import (
    VictronVRMClient,
    RateLimitError,
    AuthenticationError
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("VICTRON_VRM_USERNAME", "test@example.com")
    monkeypatch.setenv("VICTRON_VRM_PASSWORD", "test-password")
    monkeypatch.setenv("VICTRON_INSTALLATION_ID", "123456")
    monkeypatch.setenv("VICTRON_API_URL", "https://test-api.victron.com")


@pytest.fixture
def client(mock_env_vars):
    """Create VictronVRMClient instance for testing."""
    return VictronVRMClient()


@pytest.fixture
def mock_auth_response():
    """Mock successful authentication response."""
    return {
        "token": "test-token-12345",
        "idUser": 999
    }


@pytest.fixture
def mock_battery_response():
    """Mock successful battery data response."""
    return {
        "success": True,
        "records": {
            "soc": 67.5,
            "voltage": 26.4,
            "current": 12.5,
            "power": 330,
            "state": "charging",
            "temperature": 23.5
        }
    }


@pytest.fixture
def mock_installations_response():
    """Mock installations list response."""
    return {
        "success": True,
        "records": [
            {
                "idSite": 123456,
                "name": "Test Ranch",
                "identifier": "test-installation"
            }
        ]
    }


# ─────────────────────────────────────────────────────────────────────────────
# Initialization Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_client_initialization(mock_env_vars):
    """Test client initializes with environment variables."""
    client = VictronVRMClient()

    assert client.username == "test@example.com"
    assert client.password == "test-password"
    assert client.installation_id == "123456"
    assert client.base_url == "https://test-api.victron.com"
    assert client.token is None
    assert client.user_id is None


def test_client_initialization_without_credentials(monkeypatch):
    """Test client raises error without credentials."""
    monkeypatch.delenv("VICTRON_VRM_USERNAME", raising=False)
    monkeypatch.delenv("VICTRON_VRM_PASSWORD", raising=False)

    with pytest.raises(ValueError, match="Victron VRM credentials not configured"):
        VictronVRMClient()


def test_client_custom_credentials():
    """Test client accepts custom credentials."""
    client = VictronVRMClient(
        username="custom@example.com",
        password="custom-pass",
        installation_id="999",
        base_url="https://custom-api.com"
    )

    assert client.username == "custom@example.com"
    assert client.password == "custom-pass"
    assert client.installation_id == "999"
    assert client.base_url == "https://custom-api.com"


# ─────────────────────────────────────────────────────────────────────────────
# Authentication Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_authenticate_success(client, mock_auth_response):
    """Test successful authentication."""
    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_auth_response

        result = await client.authenticate()

        # Verify request was made correctly
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert "auth/login" in call_args[0][1]
        assert call_args[1]["skip_auth"] is True

        # Verify client state updated
        assert client.token == "test-token-12345"
        assert client.user_id == 999
        assert client.token_expires_at is not None

        # Verify return value
        assert result["token"] == "test-token-12345"
        assert result["user_id"] == 999


@pytest.mark.asyncio
async def test_authenticate_failure(client):
    """Test authentication failure handling."""
    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await client.authenticate()

        assert client.token is None
        assert client.user_id is None


@pytest.mark.asyncio
async def test_ensure_authenticated_when_no_token(client, mock_auth_response):
    """Test ensure_authenticated re-authenticates when no token."""
    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_auth_response

        await client.ensure_authenticated()

        mock_request.assert_called_once()
        assert client.token == "test-token-12345"


@pytest.mark.asyncio
async def test_ensure_authenticated_when_token_expired(client, mock_auth_response):
    """Test ensure_authenticated re-authenticates when token expired."""
    # Set expired token
    client.token = "old-token"
    client.token_expires_at = datetime.now() - timedelta(hours=1)

    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_auth_response

        await client.ensure_authenticated()

        mock_request.assert_called_once()
        assert client.token == "test-token-12345"


@pytest.mark.asyncio
async def test_ensure_authenticated_when_valid_token(client):
    """Test ensure_authenticated skips re-auth when token valid."""
    # Set valid token
    client.token = "valid-token"
    client.token_expires_at = datetime.now() + timedelta(hours=6)

    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        await client.ensure_authenticated()

        mock_request.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Installation Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_installations(client, mock_installations_response):
    """Test fetching installations list."""
    client.token = "test-token"
    client.user_id = 999
    client.token_expires_at = datetime.now() + timedelta(hours=6)

    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_installations_response

        result = await client.get_installations()

        # Verify request
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"
        assert f"users/{client.user_id}/installations" in call_args[0][1]

        # Verify result
        assert len(result) == 1
        assert result[0]["idSite"] == 123456
        assert result[0]["name"] == "Test Ranch"


# ─────────────────────────────────────────────────────────────────────────────
# Battery Data Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_battery_data_success(client, mock_battery_response):
    """Test fetching battery data successfully."""
    client.token = "test-token"
    client.token_expires_at = datetime.now() + timedelta(hours=6)

    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_battery_response

        result = await client.get_battery_data()

        # Verify request
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"
        assert "installations/123456/widgets/BatterySummary" in call_args[0][1]

        # Verify result structure
        assert result["soc"] == 67.5
        assert result["voltage"] == 26.4
        assert result["current"] == 12.5
        assert result["power"] == 330
        assert result["state"] == "charging"
        assert result["temperature"] == 23.5
        assert "timestamp" in result
        assert result["installation_id"] == "123456"


@pytest.mark.asyncio
async def test_get_battery_data_custom_installation(client, mock_battery_response):
    """Test fetching battery data for custom installation ID."""
    client.token = "test-token"
    client.token_expires_at = datetime.now() + timedelta(hours=6)

    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_battery_response

        result = await client.get_battery_data(installation_id="999999")

        # Verify correct installation ID used
        call_args = mock_request.call_args
        assert "installations/999999/widgets/BatterySummary" in call_args[0][1]
        assert result["installation_id"] == "999999"


@pytest.mark.asyncio
async def test_get_battery_data_no_installation_id(mock_env_vars, monkeypatch):
    """Test battery data fetch fails without installation ID."""
    monkeypatch.delenv("VICTRON_INSTALLATION_ID", raising=False)

    client = VictronVRMClient()
    client.token = "test-token"
    client.token_expires_at = datetime.now() + timedelta(hours=6)

    with pytest.raises(ValueError, match="Installation ID required"):
        await client.get_battery_data()


# ─────────────────────────────────────────────────────────────────────────────
# Rate Limiting Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_rate_limit_tracking(client):
    """Test rate limit counter increments."""
    initial_count = client.request_count

    client._track_request()
    assert client.request_count == initial_count + 1

    client._track_request()
    assert client.request_count == initial_count + 2


def test_rate_limit_check_under_limit(client):
    """Test rate limit check passes when under limit."""
    client.request_count = 30

    # Should not raise
    client._check_rate_limit()


def test_rate_limit_check_at_warning(client):
    """Test rate limit warning at threshold."""
    client.request_count = 40

    # Should log warning but not raise
    client._check_rate_limit()


def test_rate_limit_check_exceeds_limit(client):
    """Test rate limit error when exceeded."""
    client.request_count = 45

    with pytest.raises(RateLimitError, match="Rate limit exceeded"):
        client._check_rate_limit()


def test_rate_limit_reset_after_hour(client):
    """Test rate limit resets after hour window."""
    client.request_count = 40
    client.request_window_start = datetime.now() - timedelta(hours=2)

    client._check_rate_limit()

    # Should have reset
    assert client.request_count == 0
    assert (datetime.now() - client.request_window_start).total_seconds() < 1


def test_get_rate_limit_status(client):
    """Test rate limit status reporting."""
    client.request_count = 15

    status = client.get_rate_limit_status()

    assert status["requests_used"] == 15
    assert status["requests_remaining"] == 35
    assert status["requests_limit"] == 50
    assert "resets_in_seconds" in status
    assert "window_start" in status


# ─────────────────────────────────────────────────────────────────────────────
# HTTP Request Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_make_request_retry_on_timeout(client):
    """Test request retries on timeout."""
    import requests

    with patch.object(client.session, 'request') as mock_request:
        # First two attempts timeout, third succeeds
        mock_request.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            Mock(status_code=200, json=lambda: {"success": True})
        ]

        result = await client._make_request("GET", "http://test.com", skip_auth=True)

        assert result["success"] is True
        assert mock_request.call_count == 3


@pytest.mark.asyncio
async def test_make_request_max_retries_exceeded(client):
    """Test request fails after max retries."""
    import requests

    with patch.object(client.session, 'request') as mock_request:
        mock_request.side_effect = requests.exceptions.Timeout()

        with pytest.raises(requests.exceptions.Timeout):
            await client._make_request("GET", "http://test.com", skip_auth=True, max_retries=3)

        assert mock_request.call_count == 3


@pytest.mark.asyncio
async def test_make_request_adds_auth_header(client):
    """Test request adds authentication header."""
    client.token = "test-token"

    with patch.object(client.session, 'request') as mock_request:
        mock_request.return_value = Mock(
            status_code=200,
            json=lambda: {"success": True}
        )

        await client._make_request("GET", "http://test.com")

        # Check headers were added
        call_args = mock_request.call_args
        assert "headers" in call_args[1]
        assert call_args[1]["headers"]["X-Authorization"] == "Token test-token"


# ─────────────────────────────────────────────────────────────────────────────
# Context Manager Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_async_context_manager(mock_env_vars, mock_auth_response):
    """Test client works as async context manager."""
    with patch.object(VictronVRMClient, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_auth_response

        async with VictronVRMClient() as client:
            assert client.token == "test-token-12345"

        # Session should be closed after context exit
        # (We can't directly test this without accessing internals)


def test_close_closes_session(client):
    """Test close method closes HTTP session."""
    with patch.object(client.session, 'close') as mock_close:
        client.close()
        mock_close.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# Integration Test
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_workflow(client, mock_auth_response, mock_installations_response, mock_battery_response):
    """Test complete workflow: auth -> get installations -> get battery data."""
    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        # Set up mock responses in order
        mock_request.side_effect = [
            mock_auth_response,
            mock_installations_response,
            mock_battery_response
        ]

        # Authenticate
        auth = await client.authenticate()
        assert auth["token"] == "test-token-12345"

        # Get installations
        installations = await client.get_installations()
        assert len(installations) == 1

        # Get battery data
        battery = await client.get_battery_data()
        assert battery["soc"] == 67.5

        # Verify all requests were made
        assert mock_request.call_count == 3
