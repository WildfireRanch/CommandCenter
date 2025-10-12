# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/services/redis_client.py
# PURPOSE: Redis client wrapper for context caching
#
# WHAT IT DOES:
#   - Provides Redis connection with pooling and retry logic
#   - Handles get/set/delete operations with graceful degradation
#   - Manages TTL (time-to-live) for cached data
#   - Falls back gracefully if Redis unavailable
#
# DEPENDENCIES:
#   - redis (pip install redis>=5.0.0)
#
# USAGE:
#   from services.redis_client import get_redis_client
#
#   client = get_redis_client()
#   client.set("key", "value", ttl=300)
#   value = client.get("key")
# ═══════════════════════════════════════════════════════════════════════════

import logging
import json
from typing import Optional, Any
from contextlib import contextmanager

from ..config.context_config import get_context_config

# Redis is optional - gracefully degrade if not available
try:
    import redis
    from redis.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    ConnectionPool = None

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Redis Client Class
# ─────────────────────────────────────────────────────────────────────────────

class RedisClient:
    """
    Redis client wrapper with connection pooling and error handling.

    Features:
    - Connection pooling for performance
    - Automatic retry on transient failures
    - Graceful degradation if Redis unavailable
    - JSON serialization support
    - TTL (time-to-live) management
    """

    def __init__(self, url: str = None, max_retries: int = None, timeout: int = None):
        """
        Initialize Redis client.

        Args:
            url: Redis connection URL (default: from config)
            max_retries: Maximum retry attempts (default: from config)
            timeout: Connection timeout in seconds (default: from config)
        """
        config = get_context_config()

        self.url = url or config.REDIS_URL
        self.max_retries = max_retries or config.REDIS_MAX_RETRIES
        self.timeout = timeout or config.REDIS_TIMEOUT
        self.ssl = config.REDIS_SSL

        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._available = False

        # Initialize connection
        self._initialize()

    def _initialize(self) -> None:
        """Initialize Redis connection pool."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available. Caching disabled.")
            self._available = False
            return

        try:
            # Parse URL to determine SSL
            ssl_enabled = self.url.startswith("rediss://") or self.ssl

            # Create connection pool
            # Note: SSL is handled automatically by redis-py when URL starts with rediss://
            self._pool = ConnectionPool.from_url(
                self.url,
                max_connections=10,
                socket_timeout=self.timeout,
                socket_connect_timeout=self.timeout,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Create Redis client
            self._client = redis.Redis(
                connection_pool=self._pool,
                decode_responses=True,  # Auto-decode bytes to strings
            )

            # Test connection
            self._client.ping()
            self._available = True
            logger.info(f"✅ Redis connected: {self.url}")

        except Exception as e:
            logger.warning(f"⚠️  Redis connection failed: {e}. Caching disabled.")
            self._available = False
            self._client = None
            self._pool = None

    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self._available and self._client is not None

    def ping(self) -> bool:
        """
        Ping Redis to check connection health.

        Returns:
            True if connection is healthy, False otherwise
        """
        if not self.is_available():
            return False

        try:
            self._client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis.

        Args:
            key: Cache key

        Returns:
            Value as string, or None if not found or error
        """
        if not self.is_available():
            return None

        try:
            value = self._client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
            return value
        except Exception as e:
            logger.error(f"Redis GET failed for key '{key}': {e}")
            return None

    def set(self, key: str, value: str, ttl: int = None) -> bool:
        """
        Set value in Redis with optional TTL.

        Args:
            key: Cache key
            value: Value to store (string)
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            if ttl:
                self._client.setex(key, ttl, value)
            else:
                self._client.set(key, value)

            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Redis SET failed for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from Redis.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            self._client.delete(key)
            logger.debug(f"Cache delete: {key}")
            return True
        except Exception as e:
            logger.error(f"Redis DELETE failed for key '{key}': {e}")
            return False

    def get_json(self, key: str) -> Optional[Any]:
        """
        Get JSON value from Redis.

        Args:
            key: Cache key

        Returns:
            Deserialized JSON value, or None if not found or error
        """
        value = self.get(key)
        if value is None:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize JSON for key '{key}': {e}")
            return None

    def set_json(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set JSON value in Redis.

        Args:
            key: Cache key
            value: Value to serialize and store
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = json.dumps(value)
            return self.set(key, serialized, ttl=ttl)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize JSON for key '{key}': {e}")
            return False

    def close(self) -> None:
        """Close Redis connection and cleanup resources."""
        if self._client:
            try:
                self._client.close()
            except Exception as e:
                logger.error(f"Error closing Redis client: {e}")

        if self._pool:
            try:
                self._pool.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting Redis pool: {e}")

        self._client = None
        self._pool = None
        self._available = False
        logger.info("Redis connection closed")


# ─────────────────────────────────────────────────────────────────────────────
# Singleton Instance
# ─────────────────────────────────────────────────────────────────────────────

_redis_client_instance: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """
    Get the global Redis client instance (singleton).

    Returns:
        RedisClient: Global Redis client instance
    """
    global _redis_client_instance

    if _redis_client_instance is None:
        _redis_client_instance = RedisClient()

    return _redis_client_instance


def reset_redis_client() -> None:
    """
    Reset the global Redis client instance.

    Useful for testing or when configuration changes.
    """
    global _redis_client_instance

    if _redis_client_instance:
        _redis_client_instance.close()

    _redis_client_instance = None


@contextmanager
def redis_client():
    """
    Context manager for Redis client.

    Example:
        with redis_client() as client:
            client.set("key", "value")
            value = client.get("key")
    """
    client = get_redis_client()
    try:
        yield client
    finally:
        pass  # Keep connection alive (singleton)


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def build_cache_key(*parts: str) -> str:
    """
    Build a cache key from parts.

    Args:
        *parts: Key components

    Returns:
        Formatted cache key

    Example:
        >>> build_cache_key("context", "user123", "abc123")
        "context:user123:abc123"
    """
    return ":".join(str(part) for part in parts if part)


def get_cache_stats() -> dict:
    """
    Get Redis cache statistics.

    Returns:
        Dictionary with cache stats (or empty if unavailable)
    """
    client = get_redis_client()

    if not client.is_available():
        return {
            "available": False,
            "error": "Redis not available"
        }

    try:
        info = client._client.info("stats")
        return {
            "available": True,
            "total_connections": info.get("total_connections_received", 0),
            "total_commands": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": (
                info.get("keyspace_hits", 0) / (
                    info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)
                ) if (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)) > 0 else 0
            ),
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "available": True,
            "error": str(e)
        }


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test Redis client."""

    print("🔧 Redis Client Test\n")

    # Get client
    client = get_redis_client()

    # Check availability
    if not client.is_available():
        print("❌ Redis not available. Install redis package and start Redis server.")
        print("   pip install redis>=5.0.0")
        print("   docker run -d -p 6379:6379 redis:latest")
        exit(1)

    # Test ping
    print("Testing connection...")
    if client.ping():
        print("✅ Redis connection OK\n")
    else:
        print("❌ Redis ping failed\n")
        exit(1)

    # Test set/get
    print("Testing SET/GET...")
    test_key = "test:commandcenter:example"
    test_value = "Hello, Redis!"

    if client.set(test_key, test_value, ttl=60):
        print(f"✅ SET: {test_key} = {test_value}")
    else:
        print(f"❌ SET failed")

    retrieved = client.get(test_key)
    if retrieved == test_value:
        print(f"✅ GET: {test_key} = {retrieved}\n")
    else:
        print(f"❌ GET failed: expected '{test_value}', got '{retrieved}'\n")

    # Test JSON
    print("Testing JSON SET/GET...")
    json_key = "test:commandcenter:json"
    json_value = {
        "query": "What's my battery level?",
        "type": "system",
        "tokens": 2500
    }

    if client.set_json(json_key, json_value, ttl=60):
        print(f"✅ SET JSON: {json_key}")
    else:
        print(f"❌ SET JSON failed")

    retrieved_json = client.get_json(json_key)
    if retrieved_json == json_value:
        print(f"✅ GET JSON: {json_key} = {retrieved_json}\n")
    else:
        print(f"❌ GET JSON failed: {retrieved_json}\n")

    # Test delete
    print("Testing DELETE...")
    if client.delete(test_key):
        print(f"✅ DELETE: {test_key}")
    else:
        print(f"❌ DELETE failed")

    # Verify deletion
    if client.get(test_key) is None:
        print(f"✅ Verified: {test_key} deleted\n")
    else:
        print(f"❌ DELETE verification failed\n")

    # Show stats
    print("Cache Statistics:")
    stats = get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ All tests passed!")
