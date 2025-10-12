#!/usr/bin/env python3
"""
Test Redis connection from Railway environment
"""
import os
import sys

def test_redis_connection():
    """Test if Redis is accessible"""
    print("=" * 60)
    print("Redis Connection Test")
    print("=" * 60)

    # Check for Redis URL
    redis_url = os.getenv('REDIS_URL')
    print(f"\n1. Environment Check:")
    print(f"   REDIS_URL: {redis_url if redis_url else '❌ NOT SET'}")

    if not redis_url:
        print("\n⚠️  REDIS_URL not found in environment variables")
        print("\nPossible reasons:")
        print("  1. Redis service exists but not linked to CommandCenter service")
        print("  2. Missing service reference variable")
        print("\n📋 Next Steps:")
        print("  1. In Railway dashboard, go to CommandCenter service")
        print("  2. Go to 'Variables' tab")
        print("  3. Click 'Add Reference'")
        print("  4. Select Redis service → REDIS_URL")
        print("  5. Or add manually: REDIS_URL=${{Redis.REDIS_URL}}")
        return False

    # Try to connect
    print(f"\n2. Connection Test:")
    try:
        import redis
        print(f"   ✅ redis library installed")
    except ImportError:
        print(f"   ❌ redis library not installed")
        print(f"   Run: pip install redis")
        return False

    try:
        # Parse URL
        print(f"   Connecting to: {redis_url[:30]}...")
        client = redis.from_url(redis_url, decode_responses=True)

        # Test ping
        response = client.ping()
        if response:
            print(f"   ✅ Redis connection successful!")

        # Test set/get
        client.set("test_key", "Hello from CommandCenter!")
        value = client.get("test_key")
        print(f"   ✅ Test write/read successful")
        print(f"   Value: {value}")

        # Get info
        info = client.info()
        print(f"\n3. Redis Info:")
        print(f"   Version: {info.get('redis_version')}")
        print(f"   Uptime: {info.get('uptime_in_seconds')} seconds")
        print(f"   Connected clients: {info.get('connected_clients')}")
        print(f"   Used memory: {info.get('used_memory_human')}")

        # Clean up
        client.delete("test_key")
        client.close()

        print(f"\n✅ Redis is fully operational!")
        return True

    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)
