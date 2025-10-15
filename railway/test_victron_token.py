#!/usr/bin/env python3
"""
Test Victron VRM API access using the pre-generated VRM_API_TOKEN.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from integrations.victron import VictronVRMClient
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def main():
    """Test Victron VRM with API token."""

    print("=" * 80)
    print("VICTRON VRM TOKEN TEST")
    print("=" * 80)

    # Get token from env
    api_token = os.getenv('VRM_API_TOKEN')
    install_id = os.getenv('IDSITE')

    print(f"\nUsing VRM_API_TOKEN: {api_token[:20]}...")
    print(f"Installation ID: {install_id}")

    # Create client with token (skip username/password)
    print("\nCreating client with pre-generated token...")
    client = VictronVRMClient(
        api_token=api_token,
        installation_id=install_id
    )

    # Skip authenticate() since we're using pre-generated token
    # The token is already set in __init__
    print(f"Token set: {client.token[:20] if client.token else 'None'}...")

    # Try to fetch installations
    print("\nFetching installations...")
    try:
        # We need to set user_id for the installations endpoint
        # Try to get it from the whoami or users/current endpoint first
        print("Getting user info...")

        base = client.base_url.rstrip('/')
        if base.endswith('/v2'):
            whoami_url = f"{base}/users/me"
        else:
            whoami_url = f"{base}/v2/users/me"

        try:
            me = await client._make_request("GET", whoami_url)
            client.user_id = me.get("id") or me.get("idUser")
            print(f"✅ Got user ID: {client.user_id}")
        except Exception as e:
            print(f"⚠️  Could not get user info: {e}")
            # Try a different approach - installations by token
            print("Trying to list installations directly...")

        installations = await client.get_installations()
        print(f"✅ Found {len(installations)} installation(s)")

        for i, install in enumerate(installations, 1):
            print(f"\nInstallation {i}:")
            print(f"   ID: {install.get('idSite')}")
            print(f"   Name: {install.get('name')}")

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()

    # Try fetching battery data
    print(f"\nTesting battery data from installation {install_id}...")
    try:
        battery = await client.get_battery_data()
        print(f"✅ Battery data:")
        print(f"   SOC: {battery.get('soc')}%")
        print(f"   Voltage: {battery.get('voltage')}V")
        print(f"   Power: {battery.get('power')}W")
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
