"""
Railway API Client
Connects to CommandCenter Railway backend
"""

import requests
from typing import Optional, Dict, Any
import os

class RailwayAPIClient:
    """Client for CommandCenter Railway API"""

    def __init__(self):
        self.base_url = os.getenv("RAILWAY_API_URL", "https://api.wildfireranch.us")
        self.api_key = os.getenv("API_KEY", "")
        self.headers = {
            "X-API-Key": self.api_key
        } if self.api_key else {}

    def _get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make GET request to API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make POST request to API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json=data, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        return self._get("/health") or {"status": "error", "error": "Could not connect"}

    def get_latest_energy(self) -> Dict[str, Any]:
        """Get latest energy snapshot"""
        return self._get("/energy/latest") or {"error": "No data"}

    def get_energy_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get energy statistics"""
        return self._get(f"/energy/stats?hours={hours}") or {"error": "No data"}

    def ask_agent(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Send message to agent"""
        payload = {"message": message}
        if session_id:
            payload["session_id"] = session_id
        return self._post("/agent/ask", payload) or {"error": "Failed to contact agent"}

    def get_conversation(self, session_id: str) -> Dict[str, Any]:
        """Get conversation history"""
        return self._get(f"/conversations/{session_id}") or {"error": "Conversation not found"}

    def get_recent_conversations(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent conversations"""
        return self._get(f"/conversations/recent?limit={limit}") or {"error": "No conversations"}


# Singleton instance
api = RailwayAPIClient()
