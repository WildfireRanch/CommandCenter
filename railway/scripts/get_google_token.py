#!/usr/bin/env python3
"""
Get Google OAuth Access Token

This script helps you get a Google OAuth access token for testing.
It will open a browser for you to sign in and authorize access.

Usage:
    python3 scripts/get_google_token.py
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes needed for KB sync
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/documents.readonly'
]

def get_access_token():
    """Get fresh access token using OAuth flow."""

    # Create client config from environment variables
    client_config = {
        "installed": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080"]
        }
    }

    # Run OAuth flow
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=8080)

    print("\n" + "="*80)
    print("✅ Successfully authenticated!")
    print("="*80)
    print(f"\nAccess Token:\n{creds.token}")
    print("\n" + "="*80)
    print("\nTo use this token, run:")
    print(f'export ACCESS_TOKEN="{creds.token}"')
    print("="*80)

    return creds.token

if __name__ == "__main__":
    try:
        token = get_access_token()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set in your environment.")
