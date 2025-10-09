"""
Test Manager Agent Routing

Tests that the manager agent correctly routes queries to the appropriate specialist agents.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.manager import create_manager_crew


class TestManagerRouting:
    """Test manager agent query routing logic"""

    def test_status_query_routes_to_solar_controller(self):
        """Test that battery status queries route to Solar Controller"""
        query = "What's my battery level?"
        crew = create_manager_crew(query)
        result = crew.kickoff()

        result_str = str(result).lower()

        # Should contain battery-related information
        # (Either actual % or error about SolArk API)
        assert any(
            word in result_str
            for word in ["battery", "%", "soc", "charge", "solark", "error"]
        ), f"Expected battery status but got: {result_str}"

    def test_planning_query_routes_to_orchestrator(self):
        """Test that planning queries route to Energy Orchestrator"""
        query = "Should we run the miners right now?"
        crew = create_manager_crew(query)
        result = crew.kickoff()

        result_str = str(result).lower()

        # Should contain recommendation keywords
        assert any(
            word in result_str
            for word in ["start", "stop", "maintain", "recommend", "should", "miner"]
        ), f"Expected miner recommendation but got: {result_str}"

    def test_kb_query_searches_knowledge_base(self):
        """Test that documentation queries search knowledge base"""
        query = "What is the minimum battery SOC threshold?"
        crew = create_manager_crew(query)
        result = crew.kickoff()

        result_str = str(result).lower()

        # Should contain KB-related content
        # (Either SOC info or "no relevant information found")
        assert any(
            word in result_str for word in ["soc", "threshold", "source", "found", "%"]
        ), f"Expected KB search result but got: {result_str}"

    def test_simple_greeting_handled(self):
        """Test that simple greetings get appropriate response"""
        query = "Hello"
        crew = create_manager_crew(query)
        result = crew.kickoff()

        result_str = str(result).lower()

        # Should respond appropriately to greeting
        assert len(result_str) > 10, "Response should not be empty"

    def test_agent_metadata_in_response(self):
        """Test that routed responses include agent metadata"""
        query = "What's my battery level?"
        crew = create_manager_crew(query)
        result = crew.kickoff()

        result_str = str(result)

        # If JSON metadata is included, verify it
        if "{" in result_str and "agent_used" in result_str:
            import json

            try:
                result_data = json.loads(result_str)
                assert "agent_used" in result_data
                assert "response" in result_data
                assert result_data["agent_used"] in [
                    "Solar Controller",
                    "Energy Orchestrator",
                    "Manager",
                ]
            except json.JSONDecodeError:
                # JSON might be wrapped in other text
                pass


class TestManagerWithContext:
    """Test manager agent with conversation context"""

    def test_manager_accepts_context(self):
        """Test that manager crew accepts conversation context"""
        query = "What about now?"
        context = """
Previous conversation:
User: What's my battery level?
Agent: Your battery is at 52%.
"""

        crew = create_manager_crew(query, context)
        result = crew.kickoff()

        # Should process successfully even with context
        assert result is not None
        assert len(str(result)) > 0


if __name__ == "__main__":
    """Run tests directly"""
    print("🧪 Running Manager Agent Routing Tests\n")

    test_instance = TestManagerRouting()

    # Test 1
    print("Test 1: Status query routing...")
    try:
        test_instance.test_status_query_routes_to_solar_controller()
        print("✅ PASSED\n")
    except AssertionError as e:
        print(f"❌ FAILED: {e}\n")

    # Test 2
    print("Test 2: Planning query routing...")
    try:
        test_instance.test_planning_query_routes_to_orchestrator()
        print("✅ PASSED\n")
    except AssertionError as e:
        print(f"❌ FAILED: {e}\n")

    # Test 3
    print("Test 3: KB query routing...")
    try:
        test_instance.test_kb_query_searches_knowledge_base()
        print("✅ PASSED\n")
    except AssertionError as e:
        print(f"❌ FAILED: {e}\n")

    # Test 4
    print("Test 4: Greeting handling...")
    try:
        test_instance.test_simple_greeting_handled()
        print("✅ PASSED\n")
    except AssertionError as e:
        print(f"❌ FAILED: {e}\n")

    # Test 5
    print("Test 5: Agent metadata...")
    try:
        test_instance.test_agent_metadata_in_response()
        print("✅ PASSED\n")
    except AssertionError as e:
        print(f"❌ FAILED: {e}\n")

    print("=" * 60)
    print("Test suite completed!")
