#!/usr/bin/env python3
"""
Test script to validate context fixes implementation.

Tests:
1. System context is loaded into agent backstories
2. Routing tools return decisions (not execute crews)
3. Context flows properly through routing
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 70)
print("CONTEXT FIXES VALIDATION TESTS")
print("=" * 70)

# Test 1: Verify context loading in Solar Controller
print("\n📋 Test 1: Check Solar Controller loads context")
print("-" * 70)

try:
    from agents.solar_controller import create_energy_monitor_agent
    from tools.kb_search import get_context_files

    # Mock get_context_files to return test data
    original_get_context_files = get_context_files

    def mock_get_context_files():
        return """## System: CommandCenter V1.5

**Hardware:**
- SolArk 15K Inverter (15kW continuous)
- 48kWh LiFePO4 Battery Bank
- 14.6kW Solar Array (36x 405W panels)
- 5x Antminer S19 Bitcoin Miners (16.25kW total)

**Policies:**
- Minimum Battery SOC: 30% (critical)
- Safe Operating Range: 40-80% SOC
- Grid Import: Avoid except emergencies"""

    # Patch the function
    import tools.kb_search
    tools.kb_search.get_context_files = mock_get_context_files

    # Create agent
    agent = create_energy_monitor_agent()

    # Check backstory contains context
    if "SolArk 15K" in agent.backstory:
        print("✅ PASS: Agent backstory contains 'SolArk 15K'")
    else:
        print("❌ FAIL: Agent backstory missing hardware specs")

    if "48kWh" in agent.backstory:
        print("✅ PASS: Agent backstory contains '48kWh'")
    else:
        print("❌ FAIL: Agent backstory missing battery capacity")

    if "SYSTEM CONTEXT" in agent.backstory:
        print("✅ PASS: Agent backstory has context section header")
    else:
        print("❌ FAIL: Agent backstory missing context section")

    if "Minimum Battery SOC: 30%" in agent.backstory:
        print("✅ PASS: Agent backstory contains policy information")
    else:
        print("❌ FAIL: Agent backstory missing policies")

    # Restore original
    tools.kb_search.get_context_files = original_get_context_files

    print("\n📊 Agent backstory length:", len(agent.backstory), "characters")

except Exception as e:
    print(f"❌ FAIL: Error in Test 1: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Verify Energy Orchestrator loads context
print("\n📋 Test 2: Check Energy Orchestrator loads context")
print("-" * 70)

try:
    from agents.energy_orchestrator import create_energy_orchestrator

    # Patch again
    import tools.kb_search
    tools.kb_search.get_context_files = mock_get_context_files

    agent = create_energy_orchestrator()

    if "SolArk 15K" in agent.backstory:
        print("✅ PASS: Orchestrator backstory contains 'SolArk 15K'")
    else:
        print("❌ FAIL: Orchestrator backstory missing hardware specs")

    if "SYSTEM CONTEXT" in agent.backstory:
        print("✅ PASS: Orchestrator backstory has context section")
    else:
        print("❌ FAIL: Orchestrator backstory missing context section")

    print("\n📊 Orchestrator backstory length:", len(agent.backstory), "characters")

    # Restore
    tools.kb_search.get_context_files = original_get_context_files

except Exception as e:
    print(f"❌ FAIL: Error in Test 2: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Verify routing tools return decisions (not execute)
print("\n📋 Test 3: Check routing tools return decisions")
print("-" * 70)

try:
    from agents.manager import route_to_solar_controller, route_to_energy_orchestrator
    import json

    # Test Solar Controller routing
    result = route_to_solar_controller.func("What's my battery level?")
    result_data = json.loads(result)

    if result_data.get("action") == "route":
        print("✅ PASS: Solar Controller tool returns 'route' action")
    else:
        print(f"❌ FAIL: Expected action='route', got: {result_data.get('action')}")

    if result_data.get("agent") == "Solar Controller":
        print("✅ PASS: Routes to correct agent name")
    else:
        print(f"❌ FAIL: Expected agent='Solar Controller', got: {result_data.get('agent')}")

    if "response" not in result_data:
        print("✅ PASS: Tool does NOT execute crew (no 'response' key)")
    else:
        print("❌ FAIL: Tool appears to execute crew (has 'response' key)")

    # Test Energy Orchestrator routing
    result = route_to_energy_orchestrator.func("Should we run miners?")
    result_data = json.loads(result)

    if result_data.get("action") == "route":
        print("✅ PASS: Orchestrator tool returns 'route' action")
    else:
        print(f"❌ FAIL: Expected action='route', got: {result_data.get('action')}")

    if result_data.get("agent") == "Energy Orchestrator":
        print("✅ PASS: Routes to correct agent name")
    else:
        print(f"❌ FAIL: Expected agent='Energy Orchestrator', got: {result_data.get('agent')}")

except Exception as e:
    print(f"❌ FAIL: Error in Test 3: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Verify specialist crew functions accept context parameter
print("\n📋 Test 4: Check specialist crews accept context parameter")
print("-" * 70)

try:
    from agents.solar_controller import create_energy_crew
    from agents.energy_orchestrator import create_orchestrator_crew
    import inspect

    # Check Solar Controller signature
    sig = inspect.signature(create_energy_crew)
    params = list(sig.parameters.keys())

    if "conversation_context" in params:
        print("✅ PASS: create_energy_crew has 'conversation_context' parameter")
    else:
        print(f"❌ FAIL: create_energy_crew missing context param. Has: {params}")

    # Check Energy Orchestrator signature
    sig = inspect.signature(create_orchestrator_crew)
    params = list(sig.parameters.keys())

    if "context" in params:
        print("✅ PASS: create_orchestrator_crew has 'context' parameter")
    else:
        print(f"❌ FAIL: create_orchestrator_crew missing context param. Has: {params}")

except Exception as e:
    print(f"❌ FAIL: Error in Test 4: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("""
If all tests passed:
✅ Agents load system context into backstories
✅ Routing tools return decisions (not execute crews)
✅ Specialist crews accept context parameters
✅ Architecture ready for proper context flow

Next steps:
1. Deploy to environment with database access
2. Ensure KB has context files (is_context_file=TRUE)
3. Run end-to-end tests with real API calls
4. Monitor token usage and response quality
""")
