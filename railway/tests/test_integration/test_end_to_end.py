"""
End-to-End Integration Tests

Tests the complete flow from API endpoint through agents and back.
Requires the backend server to be running.
"""

import pytest
import requests
import time

BASE_URL = "http://localhost:8000"


class TestHealthCheck:
    """Test basic API health"""

    def test_health_endpoint(self):
        """Test that the health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAskEndpoint:
    """Test the /ask endpoint with various queries"""

    def test_ask_endpoint_returns_valid_response(self):
        """Test that /ask endpoint returns properly structured response"""
        response = requests.post(
            f"{BASE_URL}/ask", json={"message": "What's my battery level?"}, timeout=60
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "response" in data
        assert "agent_role" in data
        assert "session_id" in data
        assert "query" in data
        assert "duration_ms" in data

        # Verify response content
        assert len(data["response"]) > 0
        assert isinstance(data["duration_ms"], int)

    def test_ask_planning_query(self):
        """Test planning query routes to Energy Orchestrator"""
        response = requests.post(
            f"{BASE_URL}/ask",
            json={"message": "Should we run the miners right now?"},
            timeout=60,
        )

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        # Should mention miners or energy planning
        assert any(
            word in data["response"].lower()
            for word in ["miner", "recommend", "should", "energy"]
        )

    def test_ask_kb_query(self):
        """Test knowledge base search query"""
        response = requests.post(
            f"{BASE_URL}/ask",
            json={"message": "What is the minimum battery SOC threshold?"},
            timeout=60,
        )

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        # Should contain SOC or threshold information
        response_lower = data["response"].lower()
        assert any(word in response_lower for word in ["soc", "threshold", "battery"])

    def test_ask_with_invalid_message(self):
        """Test that empty message is rejected"""
        response = requests.post(f"{BASE_URL}/ask", json={"message": ""}, timeout=10)

        # Should either reject or return error
        assert response.status_code in [200, 400, 422]


class TestConversationPersistence:
    """Test multi-turn conversation handling"""

    def test_conversation_continuity(self):
        """Test that conversations are tracked across multiple messages"""
        # First message
        resp1 = requests.post(
            f"{BASE_URL}/ask", json={"message": "What's my battery level?"}, timeout=60
        )

        assert resp1.status_code == 200
        data1 = resp1.json()
        session_id = data1["session_id"]

        assert session_id is not None
        assert len(session_id) > 0

        # Second message in same conversation
        resp2 = requests.post(
            f"{BASE_URL}/ask",
            json={"message": "Is that good?", "session_id": session_id},
            timeout=60,
        )

        assert resp2.status_code == 200
        data2 = resp2.json()

        # Should use same session ID
        assert data2["session_id"] == session_id

        # Should have a response
        assert len(data2["response"]) > 0

    def test_get_conversation_history(self):
        """Test retrieving conversation history"""
        # Create a conversation
        resp1 = requests.post(
            f"{BASE_URL}/ask", json={"message": "Test query"}, timeout=60
        )

        assert resp1.status_code == 200
        session_id = resp1.json()["session_id"]

        # Retrieve conversation
        resp2 = requests.get(f"{BASE_URL}/conversations/{session_id}", timeout=10)

        assert resp2.status_code == 200
        data = resp2.json()

        assert "messages" in data
        assert len(data["messages"]) >= 2  # At least user + assistant

    def test_list_conversations(self):
        """Test listing recent conversations"""
        # Create a conversation first
        requests.post(
            f"{BASE_URL}/ask", json={"message": "Test query"}, timeout=60
        )

        # List conversations
        response = requests.get(f"{BASE_URL}/conversations?limit=10", timeout=10)

        assert response.status_code == 200
        data = response.json()

        # Should have conversations array
        assert isinstance(data, (list, dict))


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_malformed_request(self):
        """Test that malformed requests are handled gracefully"""
        response = requests.post(
            f"{BASE_URL}/ask", json={"invalid_field": "test"}, timeout=10
        )

        # Should return error
        assert response.status_code in [400, 422]

    def test_very_long_query(self):
        """Test handling of very long queries"""
        long_query = "What is my battery level? " * 100  # Very long query

        response = requests.post(
            f"{BASE_URL}/ask", json={"message": long_query}, timeout=60
        )

        # Should either process or reject gracefully
        assert response.status_code in [200, 400, 413, 422]


if __name__ == "__main__":
    """Run integration tests directly"""
    print("🧪 Running End-to-End Integration Tests")
    print(f"📡 Testing against: {BASE_URL}\n")

    print("=" * 60)
    print("Checking if backend is running...")

    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Backend is running\n")
        else:
            print(
                f"⚠️ Backend returned status {health_response.status_code}, continuing anyway...\n"
            )
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not accessible: {e}")
        print(
            f"\n💡 Make sure to start the backend first:\n   cd railway && uvicorn src.api.main:app --reload\n"
        )
        exit(1)

    print("=" * 60)

    # Run tests
    test_health = TestHealthCheck()
    test_ask = TestAskEndpoint()
    test_conv = TestConversationPersistence()

    tests_run = 0
    tests_passed = 0

    test_cases = [
        ("Health Check", test_health.test_health_endpoint),
        ("Ask Endpoint - Status Query", test_ask.test_ask_endpoint_returns_valid_response),
        ("Ask Endpoint - Planning Query", test_ask.test_ask_planning_query),
        ("Ask Endpoint - KB Query", test_ask.test_ask_kb_query),
        ("Conversation Continuity", test_conv.test_conversation_continuity),
        ("Get Conversation History", test_conv.test_get_conversation_history),
        ("List Conversations", test_conv.test_list_conversations),
    ]

    for test_name, test_func in test_cases:
        tests_run += 1
        print(f"\nTest {tests_run}: {test_name}...")
        try:
            test_func()
            print("✅ PASSED")
            tests_passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"Tests completed: {tests_passed}/{tests_run} passed")

    if tests_passed == tests_run:
        print("🎉 All tests passed!")
        exit(0)
    else:
        print(f"⚠️ {tests_run - tests_passed} tests failed")
        exit(1)
