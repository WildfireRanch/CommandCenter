# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/integrations/victron.py
# PURPOSE: Victron VRM Cloud API integration for battery monitoring
#
# WHAT IT DOES:
#   - Authenticates with Victron VRM Cloud API
#   - Fetches battery data from Victron Cerbo GX
#   - Provides accurate SOC, voltage, current, temperature readings
#   - Tracks API rate limits (50 requests/hour)
#
# DEPENDENCIES:
#   - requests (HTTP client)
#   - python-dotenv (environment variables)
#
# ENVIRONMENT VARIABLES:
#   - VICTRON_VRM_USERNAME: VRM account email
#   - VICTRON_VRM_PASSWORD: VRM account password
#   - VICTRON_INSTALLATION_ID: Installation ID from VRM portal
#   - VICTRON_API_URL: Base API URL (default: https://vrmapi.victronenergy.com)
#
# USAGE:
#   from integrations.victron import VictronVRMClient
#
#   client = VictronVRMClient()
#   await client.authenticate()
#   battery_data = await client.get_battery_data()
# ═══════════════════════════════════════════════════════════════════════════

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

VRM_API_BASE_URL = os.getenv("VICTRON_API_URL", "https://vrmapi.victronenergy.com")
VRM_USERNAME = os.getenv("VICTRON_VRM_USERNAME")
VRM_PASSWORD = os.getenv("VICTRON_VRM_PASSWORD")
INSTALLATION_ID = os.getenv("VICTRON_INSTALLATION_ID")

# Rate limiting
MAX_REQUESTS_PER_HOUR = 50
WARNING_THRESHOLD = 40
ERROR_THRESHOLD = 45


# ─────────────────────────────────────────────────────────────────────────────
# VictronVRMClient Class
# ─────────────────────────────────────────────────────────────────────────────

class VictronVRMClient:
    """
    Client for interacting with Victron VRM Cloud API.

    Provides methods to:
    - Authenticate and manage session tokens
    - Fetch battery data from Victron Cerbo GX
    - Track and enforce API rate limits
    - Handle errors and retries
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        installation_id: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize VRM API client.

        Args:
            username: VRM account email (defaults to env var)
            password: VRM account password (defaults to env var)
            installation_id: VRM installation ID (defaults to env var)
            base_url: API base URL (defaults to env var or standard URL)
        """
        self.base_url = base_url or VRM_API_BASE_URL
        self.username = username or VRM_USERNAME
        self.password = password or VRM_PASSWORD
        self.installation_id = installation_id or INSTALLATION_ID

        # Validate credentials
        if not self.username or not self.password:
            raise ValueError(
                "Victron VRM credentials not configured. "
                "Set VICTRON_VRM_USERNAME and VICTRON_VRM_PASSWORD environment variables."
            )

        if not self.installation_id:
            logger.warning(
                "VICTRON_INSTALLATION_ID not set. "
                "You'll need to call get_installations() to find it."
            )

        # Authentication state
        self.token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.token_expires_at: Optional[datetime] = None

        # Rate limiting
        self.request_count = 0
        self.request_window_start = datetime.now()

        # HTTP session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    # ─────────────────────────────────────────────────────────────────────────
    # Authentication
    # ─────────────────────────────────────────────────────────────────────────

    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with VRM API and get access token.

        Returns:
            Dict containing token and user info

        Raises:
            requests.HTTPError: If authentication fails
            ValueError: If credentials are invalid
        """
        logger.info("Authenticating with Victron VRM API...")

        url = f"{self.base_url}/v2/auth/login"
        payload = {
            "username": self.username,
            "password": self.password
        }

        try:
            response = await self._make_request(
                "POST",
                url,
                json=payload,
                skip_auth=True  # Don't add token to login request
            )

            # Extract token and user info
            self.token = response.get("token")
            self.user_id = response.get("idUser")

            # Set token expiration (12 hours from now)
            self.token_expires_at = datetime.now() + timedelta(hours=12)

            logger.info(f"Authentication successful. User ID: {self.user_id}")

            return {
                "token": self.token,
                "user_id": self.user_id,
                "expires_at": self.token_expires_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    async def ensure_authenticated(self):
        """
        Ensure we have a valid authentication token.
        Re-authenticates if token is expired or missing.
        """
        if not self.token or self._is_token_expired():
            await self.authenticate()

    def _is_token_expired(self) -> bool:
        """Check if authentication token is expired."""
        if not self.token_expires_at:
            return True
        return datetime.now() >= self.token_expires_at

    # ─────────────────────────────────────────────────────────────────────────
    # Installation Management
    # ─────────────────────────────────────────────────────────────────────────

    async def get_installations(self) -> List[Dict[str, Any]]:
        """
        Get list of all VRM installations for authenticated user.

        Returns:
            List of installation dictionaries with id, name, etc.
        """
        await self.ensure_authenticated()

        url = f"{self.base_url}/v2/users/{self.user_id}/installations"

        response = await self._make_request("GET", url)

        installations = response.get("records", [])

        logger.info(f"Found {len(installations)} installation(s)")

        return installations

    # ─────────────────────────────────────────────────────────────────────────
    # Battery Data
    # ─────────────────────────────────────────────────────────────────────────

    async def get_battery_data(
        self,
        installation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch battery data from Victron Cerbo GX.

        Args:
            installation_id: VRM installation ID (uses default if not provided)

        Returns:
            Dict containing:
                - timestamp: When data was fetched
                - soc: State of charge (%)
                - voltage: Battery voltage (V)
                - current: Battery current (A, positive = charging)
                - power: Battery power (W)
                - state: charging/discharging/idle
                - temperature: Battery temperature (°C)
        """
        await self.ensure_authenticated()

        install_id = installation_id or self.installation_id

        if not install_id:
            raise ValueError(
                "Installation ID required. Set VICTRON_INSTALLATION_ID or pass as argument."
            )

        url = f"{self.base_url}/v2/installations/{install_id}/widgets/BatterySummary"

        try:
            response = await self._make_request("GET", url)

            # Extract battery data from response
            records = response.get("records", {})

            # Map VRM response to our format
            battery_data = {
                "timestamp": datetime.now().isoformat(),
                "installation_id": install_id,
                "soc": records.get("soc"),
                "voltage": records.get("voltage"),
                "current": records.get("current"),
                "power": records.get("power"),
                "state": records.get("state"),
                "temperature": records.get("temperature")
            }

            logger.debug(f"Battery data: SOC={battery_data['soc']}%, V={battery_data['voltage']}V")

            return battery_data

        except Exception as e:
            logger.error(f"Failed to fetch battery data: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # HTTP Request Handling
    # ─────────────────────────────────────────────────────────────────────────

    async def _make_request(
        self,
        method: str,
        url: str,
        skip_auth: bool = False,
        max_retries: int = 3,
        timeout: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and rate limiting.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            skip_auth: Skip adding authentication header (for login)
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            **kwargs: Additional arguments for requests

        Returns:
            Parsed JSON response

        Raises:
            requests.HTTPError: If request fails after retries
            RateLimitError: If rate limit exceeded
        """
        # Check rate limit
        self._check_rate_limit()

        # Add authentication header if needed
        if not skip_auth and self.token:
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"]["X-Authorization"] = f"Token {self.token}"

        # Retry loop
        for attempt in range(max_retries):
            try:
                # Make request (using asyncio for non-blocking)
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.session.request(
                        method,
                        url,
                        timeout=timeout,
                        **kwargs
                    )
                )

                # Track request for rate limiting
                self._track_request()

                # Check for HTTP errors
                response.raise_for_status()

                # Handle 401 Unauthorized (token expired)
                if response.status_code == 401 and not skip_auth:
                    logger.warning("Token expired, re-authenticating...")
                    await self.authenticate()
                    # Retry with new token
                    continue

                # Parse JSON response
                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"Request failed after {max_retries} attempts")

    # ─────────────────────────────────────────────────────────────────────────
    # Rate Limiting
    # ─────────────────────────────────────────────────────────────────────────

    def _check_rate_limit(self):
        """
        Check if we're within rate limits.
        Resets counter if hour window has passed.

        Raises:
            RateLimitError: If approaching or exceeding limit
        """
        now = datetime.now()

        # Reset counter if hour has passed
        if now - self.request_window_start >= timedelta(hours=1):
            self.request_count = 0
            self.request_window_start = now

        # Check thresholds
        if self.request_count >= ERROR_THRESHOLD:
            raise RateLimitError(
                f"Rate limit exceeded: {self.request_count}/{MAX_REQUESTS_PER_HOUR} requests this hour"
            )

        if self.request_count >= WARNING_THRESHOLD:
            logger.warning(
                f"Approaching rate limit: {self.request_count}/{MAX_REQUESTS_PER_HOUR} requests this hour"
            )

    def _track_request(self):
        """Increment request counter."""
        self.request_count += 1

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            Dict with request count, remaining, and reset time
        """
        now = datetime.now()
        window_elapsed = now - self.request_window_start

        # If window is complete, report as reset
        if window_elapsed >= timedelta(hours=1):
            remaining = MAX_REQUESTS_PER_HOUR
            reset_in = timedelta(hours=1)
        else:
            remaining = MAX_REQUESTS_PER_HOUR - self.request_count
            reset_in = timedelta(hours=1) - window_elapsed

        return {
            "requests_used": self.request_count,
            "requests_remaining": remaining,
            "requests_limit": MAX_REQUESTS_PER_HOUR,
            "resets_in_seconds": int(reset_in.total_seconds()),
            "window_start": self.request_window_start.isoformat()
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────────────────────────────────────

    def close(self):
        """Close HTTP session."""
        self.session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()


# ─────────────────────────────────────────────────────────────────────────────
# Custom Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class RateLimitError(Exception):
    """Raised when VRM API rate limit is exceeded."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

async def get_victron_client() -> VictronVRMClient:
    """
    Get authenticated Victron VRM client.

    Returns:
        Authenticated VictronVRMClient instance
    """
    client = VictronVRMClient()
    await client.authenticate()
    return client


async def fetch_battery_data() -> Dict[str, Any]:
    """
    Convenience function to fetch battery data.

    Returns:
        Battery data dict
    """
    async with VictronVRMClient() as client:
        return await client.get_battery_data()


# ─────────────────────────────────────────────────────────────────────────────
# Module Testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test the client
    import asyncio

    async def test():
        """Test VRM API client."""
        client = VictronVRMClient()

        # Test authentication
        auth = await client.authenticate()
        print(f"Authenticated: {auth}")

        # Test installations
        installations = await client.get_installations()
        print(f"Installations: {installations}")

        # Test battery data
        battery = await client.get_battery_data()
        print(f"Battery: {battery}")

        # Test rate limit status
        rate_limit = client.get_rate_limit_status()
        print(f"Rate limit: {rate_limit}")

        client.close()

    asyncio.run(test())
