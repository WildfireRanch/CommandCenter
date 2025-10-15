#!/usr/bin/env python3
"""
Test script to check Victron VRM access and list available installations.
This will help debug why installation 290928 is giving 401 errors.
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
    """Test Victron VRM access."""

    print("=" * 80)
    print("VICTRON VRM ACCESS TEST")
    print("=" * 80)

    # Show current environment variables
    print("\n1. Environment Variables:")
    print(f"   VICTRON_VRM_USERNAME: {os.getenv('VICTRON_VRM_USERNAME')}")
    print(f"   VICTRON_VRM_PASSWORD: {'*' * len(os.getenv('VICTRON_VRM_PASSWORD', ''))}")
    print(f"   VICTRON_INSTALLATION_ID: {os.getenv('VICTRON_INSTALLATION_ID')}")
    print(f"   IDSITE: {os.getenv('IDSITE')}")
    print(f"   VRM_API_TOKEN: {os.getenv('VRM_API_TOKEN', 'Not set')[:20]}...")

    # Create client
    print("\n2. Creating VRM client...")
    client = VictronVRMClient()

    # Authenticate
    print("\n3. Authenticating...")
    try:
        await client.authenticate()
        print(f"   ✅ Authentication successful!")
        print(f"   User ID: {client.user_id}")
        print(f"   Token: {client.token[:20] if client.token else 'None'}...")
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}")
        return

    # List installations
    print("\n4. Fetching installations...")
    try:
        installations = await client.get_installations()
        print(f"   ✅ Found {len(installations)} installation(s)")

        print("\n5. Installation Details:")
        for i, install in enumerate(installations, 1):
            print(f"\n   Installation {i}:")
            print(f"      ID (idSite): {install.get('idSite')}")
            print(f"      Name: {install.get('name')}")
            print(f"      Identifier: {install.get('identifier')}")
            print(f"      Access Level: {install.get('accessLevel')}")

            # Show all keys for debugging
            print(f"      Available keys: {', '.join(install.keys())}")

        # Check if 290928 is in the list
        print("\n6. Checking for installation 290928...")
        target_id = "290928"
        found = False
        for install in installations:
            if str(install.get('idSite')) == target_id:
                print(f"   ✅ Found installation {target_id}!")
                print(f"      Name: {install.get('name')}")
                print(f"      Access Level: {install.get('accessLevel')}")
                found = True
                break

        if not found:
            print(f"   ❌ Installation {target_id} NOT found in user's accessible installations")
            print(f"   Available IDs: {[str(i.get('idSite')) for i in installations]}")

    except Exception as e:
        print(f"   ❌ Failed to fetch installations: {e}")
        import traceback
        traceback.print_exc()
        return

    # Try to fetch battery data from first installation if available
    if installations:
        first_install_id = installations[0].get('idSite')
        print(f"\n7. Testing battery data fetch from installation {first_install_id}...")
        try:
            # Override installation_id temporarily
            original_id = client.installation_id
            client.installation_id = str(first_install_id)

            battery_data = await client.get_battery_data()
            print(f"   ✅ Battery data fetch successful!")
            print(f"      SOC: {battery_data.get('soc')}%")
            print(f"      Voltage: {battery_data.get('voltage')}V")
            print(f"      Current: {battery_data.get('current')}A")
            print(f"      Power: {battery_data.get('power')}W")
            print(f"      Temperature: {battery_data.get('temperature')}°C")

            # Restore original
            client.installation_id = original_id

        except Exception as e:
            print(f"   ❌ Battery data fetch failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
