# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/tools/solark.py
# PURPOSE: Fetch real-time data from SolArkCloud API
#
# WHAT IT DOES:
#   - Authenticates with SolArkCloud OAuth API
#   - Fetches current plant status (PV, battery, load, grid)
#   - Returns clean Python dict with key metrics
#
# DEPENDENCIES:
#   - requests (HTTP client)
#   - python-dotenv (for local testing)
#
# ENVIRONMENT VARIABLES:
#   - SOLARK_EMAIL: Your SolArkCloud login email
#   - SOLARK_PASSWORD: Your SolArkCloud password
#   - SOLARK_PLANT_ID: Your plant ID (default: 146453)
#
# USAGE:
#   from tools.solark import get_solark_status
#   
#   status = get_solark_status()
#   print(f"Battery SOC: {status['soc']}%")
#   print(f"PV Power: {status['pv_power']}W")
# ═══════════════════════════════════════════════════════════════════════════

import os
from datetime import date
from pathlib import Path
from typing import Dict, Optional

import requests
from dotenv import load_dotenv

# Load .env from repo root (goes up from src/tools/ to find it)
# This searches up the directory tree for .env file
load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

OAUTH_URL = "https://api.solarkcloud.com/oauth/token"
PLANT_FLOW_URL = "https://api.solarkcloud.com/api/v1/plant/energy/{plant_id}/flow"

# Default plant ID (can be overridden via env var)
DEFAULT_PLANT_ID = "146453"


# ─────────────────────────────────────────────────────────────────────────────
# Authentication
# ─────────────────────────────────────────────────────────────────────────────

def authenticate() -> str:
    """
    Authenticate with SolArkCloud and get access token.
    
    WHAT: Calls OAuth endpoint to get bearer token
    WHY: Required for all subsequent API calls
    HOW: POST credentials, extract access_token from response
    
    Returns:
        str: Bearer token for API authentication
        
    Raises:
        ValueError: If credentials are missing
        requests.RequestException: If authentication fails
        
    Environment Variables:
        SOLARK_EMAIL: Your SolArkCloud login email
        SOLARK_PASSWORD: Your SolArkCloud password
    """
    email = os.getenv("SOLARK_EMAIL")
    password = os.getenv("SOLARK_PASSWORD")
    
    if not email or not password:
        raise ValueError(
            "Missing SolArk credentials. Set SOLARK_EMAIL and SOLARK_PASSWORD "
            "environment variables."
        )
    
    # Prepare OAuth request
    payload = {
        "grant_type": "password",
        "username": email,
        "password": password,
        "scope": "all",
    }
    
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://www.solarkcloud.com",
        "Referer": "https://www.solarkcloud.com/",
    }
    
    try:
        response = requests.post(OAUTH_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        token = data.get("data", {}).get("access_token")
        
        if not token:
            raise ValueError("No access_token in OAuth response")
        
        return token
        
    except requests.RequestException as e:
        raise requests.RequestException(f"SolArk authentication failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Data Fetching
# ─────────────────────────────────────────────────────────────────────────────

def fetch_plant_flow(token: str, plant_id: str, date_str: Optional[str] = None) -> Dict:
    """
    Fetch current plant flow data (snapshot of system status).
    
    WHAT: Gets real-time metrics from SolArkCloud API
    WHY: Provides current PV, battery, load, and grid power data
    HOW: GET request with bearer token to plant flow endpoint
    
    Args:
        token: OAuth bearer token from authenticate()
        plant_id: Your SolArk plant ID
        date_str: Date in YYYY-MM-DD format (defaults to today)
        
    Returns:
        dict: Plant flow data with keys:
            - pvPower: Solar production (W)
            - battPower: Battery charge/discharge (W)
            - gridOrMeterPower: Grid power (W)
            - loadOrEpsPower: Load consumption (W)
            - soc: Battery state of charge (%)
            - plus many boolean flags for flow direction
            
    Raises:
        requests.RequestException: If API call fails
    """
    if date_str is None:
        date_str = date.today().isoformat()
    
    url = PLANT_FLOW_URL.format(plant_id=plant_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "https://www.solarkcloud.com",
        "Referer": f"https://www.solarkcloud.com/plants/overview/{plant_id}/2",
    }
    
    params = {"date": date_str}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        snapshot = data.get("data")
        
        if not snapshot or not isinstance(snapshot, dict):
            raise ValueError("No snapshot data in API response")
        
        return snapshot
        
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch plant flow: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# High-Level Interface (This is what agents use)
# ─────────────────────────────────────────────────────────────────────────────

def get_solark_status() -> Dict[str, any]:
    """
    Get current SolArk system status (high-level interface).
    
    WHAT: One-stop function to get current system metrics
    WHY: Agents need simple interface without handling auth/APIs
    HOW: Authenticates, fetches data, returns clean dict
    
    Returns:
        dict: Cleaned system status with keys:
            - soc: Battery state of charge (%)
            - pv_power: Solar production (W)
            - battery_power: Battery charge/discharge (W, positive = charging)
            - load_power: House load consumption (W)
            - grid_power: Grid import/export (W, positive = importing)
            - charging: Boolean, is battery charging?
            - discharging: Boolean, is battery discharging?
            - exporting: Boolean, exporting to grid?
            - importing: Boolean, importing from grid?
            - raw: Full API response for debugging
            
    Example:
        >>> status = get_solark_status()
        >>> print(f"Battery: {status['soc']}%")
        Battery: 37%
        >>> print(f"Solar: {status['pv_power']}W")
        Solar: 9878W
        
    Raises:
        ValueError: If credentials are missing
        requests.RequestException: If API calls fail
    """
    # Get plant ID from environment or use default
    plant_id = os.getenv("SOLARK_PLANT_ID", DEFAULT_PLANT_ID)
    
    # Step 1: Authenticate
    token = authenticate()
    
    # Step 2: Fetch current data
    raw_data = fetch_plant_flow(token, plant_id)
    
    # Step 3: Extract and clean key metrics
    status = {
        # Core metrics
        "soc": raw_data.get("soc", 0),
        "pv_power": raw_data.get("pvPower", 0),
        "battery_power": raw_data.get("battPower", 0),
        "load_power": raw_data.get("loadOrEpsPower", 0),
        "grid_power": raw_data.get("gridOrMeterPower", 0),
        
        # Flow indicators (easier to read than raw booleans)
        "charging": raw_data.get("toBat", False),
        "discharging": raw_data.get("batTo", False),
        "exporting": raw_data.get("toGrid", False),
        "importing": raw_data.get("gridTo", False),
        
        # Keep raw data for debugging
        "raw": raw_data,
    }
    
    return status


def format_status_summary(status: Dict) -> str:
    """
    Format status dict into human-readable summary.
    
    WHAT: Converts status dict into friendly text
    WHY: Agents need to present data to users naturally
    HOW: Template string with key metrics
    
    Args:
        status: Dict from get_solark_status()
        
    Returns:
        str: Formatted summary like:
            "Battery: 37% (charging at 4906W)
             Solar: 9878W | Load: 4566W | Grid: 0W"
             
    Example:
        >>> status = get_solark_status()
        >>> print(format_status_summary(status))
    """
    # Battery status with charge/discharge indicator
    battery_action = ""
    if status["charging"]:
        battery_action = f" (charging at {status['battery_power']}W)"
    elif status["discharging"]:
        battery_action = f" (discharging at {abs(status['battery_power'])}W)"
    
    # Grid status
    grid_action = ""
    if status["exporting"]:
        grid_action = " (exporting)"
    elif status["importing"]:
        grid_action = " (importing)"
    
    summary = (
        f"🔋 Battery: {status['soc']}%{battery_action}\n"
        f"☀️ Solar: {status['pv_power']}W | "
        f"⚡ Load: {status['load_power']}W | "
        f"🔌 Grid: {status['grid_power']}W{grid_action}"
    )
    
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Test the tool from command line.
    
    Usage:
        python -m tools.solark
        
    Requires SOLARK_EMAIL and SOLARK_PASSWORD environment variables.
    """
    print("🔍 Fetching SolArk status...\n")
    
    try:
        status = get_solark_status()
        print(format_status_summary(status))
        print("\n📊 Full data:")
        print(f"  SOC: {status['soc']}%")
        print(f"  PV: {status['pv_power']}W")
        print(f"  Battery: {status['battery_power']}W")
        print(f"  Load: {status['load_power']}W")
        print(f"  Grid: {status['grid_power']}W")
        print(f"\n✅ Success!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import sys
        sys.exit(1)