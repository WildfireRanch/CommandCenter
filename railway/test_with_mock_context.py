#!/usr/bin/env python3
"""
Test Context Fixes with Mock Data

Since we don't have database access in dev environment,
this script mocks the context data to test the full flow.
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Mock context data
MOCK_CONTEXT = """
### System Hardware Specifications

**Inverter:** SolArk 15K Hybrid Inverter
- Model: 15K-2P-N
- Rated Power: 15,000W continuous
- Max PV Input: 600V DC
- Operating Voltage: 180-550V DC

**Battery Bank:** 48V Lithium Iron Phosphate (LiFePO4)
- Total Capacity: 48 kWh
- Configuration: 16S 280Ah cells
- BMS: JBD Smart BMS with RS485
- Operating Range: 40V - 58.4V

**Solar Array:** 12.8 kW PV System
- Panel Count: 32x 400W panels
- Configuration: 2 strings of 16 panels (series)
- Orientation: South-facing, 30° tilt

---

### Energy Management Policies

**Battery State of Charge (SOC) Thresholds:**
- Maximum SOC: 100% (58.4V)
- Target SOC: 80-90% for daily cycling
- Minimum SOC: 30% (critical threshold)
- Emergency Reserve: 20% (grid failure only)

**Charging Policy:**
- Priority 1: Solar charging (free energy)
- Priority 2: Grid charging (off-peak only, if SOC < 40%)
- Maximum charge rate: 100A (5kW)

**Discharging Policy:**
- Allow discharge: SOC > 35%
- Critical discharge limit: 30% SOC
- Emergency reserve: Only for grid outages

---

### Operating Procedures

**Low Battery Procedure (SOC < 30%):**
1. Immediately reduce all non-essential loads
2. Switch to grid power for critical loads
3. Enable grid charging if available
4. Alert user via notification

**Grid Outage Procedure:**
1. Switch to battery backup mode
2. Calculate available runtime based on current SOC
3. Prioritize critical loads (refrigerator, networking)
4. Monitor SOC every 5 minutes
5. If SOC approaches 20%, shut down non-critical loads

**Solar Overproduction Procedure (Battery Full):**
1. If SOC > 95% and solar > consumption:
2. Consider grid export (if net metering available)
3. Or throttle solar inverter
4. Or enable opportunistic loads (water heater, EV charging)
"""


def mock_get_context_files():
    """Mock version of get_context_files that doesn't need database."""
    return MOCK_CONTEXT


# Monkey patch the actual function
import src.tools.kb_search
original_get_context_files = src.tools.kb_search.get_context_files
src.tools.kb_search.get_context_files = mock_get_context_files


def test_agent_with_mock_context():
    """Test that agent properly loads and uses mock context."""
    print("\n" + "="*70)
    print("TEST: Agent Creation with Mock Context")
    print("="*70)

    try:
        from src.agents.solar_controller import create_energy_monitor_agent

        agent = create_energy_monitor_agent()

        # Check backstory contains context
        if "SYSTEM CONTEXT" not in agent.backstory:
            print("❌ FAIL: Agent backstory missing SYSTEM CONTEXT section")
            return False

        if "SolArk 15K" not in agent.backstory:
            print("❌ FAIL: Agent backstory missing hardware details")
            return False

        if "30%" not in agent.backstory:
            print("❌ FAIL: Agent backstory missing policy details")
            return False

        print("✅ PASS: Agent backstory contains system context")
        print(f"\nBackstory length: {len(agent.backstory)} characters")
        print("\nContext preview:")

        # Find and show the SYSTEM CONTEXT section
        lines = agent.backstory.split('\n')
        in_context = False
        line_count = 0
        for line in lines:
            if "SYSTEM CONTEXT" in line:
                in_context = True
            if in_context:
                print(f"  {line}")
                line_count += 1
                if line_count > 20:  # Show first 20 lines of context
                    print("  ...")
                    break

        return True

    except Exception as e:
        print(f"❌ FAIL: Error creating agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_routing_with_context():
    """Test that routing preserves context."""
    print("\n" + "="*70)
    print("TEST: Routing Decision with Context Preservation")
    print("="*70)

    try:
        from src.agents.manager import route_to_solar_controller, route_to_energy_orchestrator

        # Test Solar Controller routing
        result = route_to_solar_controller.func("What's my battery level?")
        decision = json.loads(result)

        if decision.get("action") != "route":
            print(f"❌ FAIL: Wrong action: {decision}")
            return False

        if decision.get("agent") != "Solar Controller":
            print(f"❌ FAIL: Wrong agent: {decision}")
            return False

        print("✅ PASS: Solar Controller routing returns correct decision")
        print(f"  Decision: {json.dumps(decision, indent=2)}")

        # Test Energy Orchestrator routing
        result = route_to_energy_orchestrator.func("Should I charge from grid?")
        decision = json.loads(result)

        if decision.get("action") != "route":
            print(f"❌ FAIL: Wrong action: {decision}")
            return False

        if decision.get("agent") != "Energy Orchestrator":
            print(f"❌ FAIL: Wrong agent: {decision}")
            return False

        print("✅ PASS: Energy Orchestrator routing returns correct decision")
        print(f"  Decision: {json.dumps(decision, indent=2)}")

        return True

    except Exception as e:
        print(f"❌ FAIL: Error testing routing: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crew_creation_with_context():
    """Test that crews can be created with context parameter."""
    print("\n" + "="*70)
    print("TEST: Crew Creation with Context Parameter")
    print("="*70)

    try:
        from src.agents.solar_controller import create_energy_crew
        from src.agents.energy_orchestrator import create_orchestrator_crew

        mock_conversation_context = """
Previous conversation:
User: What's my battery level?
Agent: Your battery is at 65% State of Charge.
"""

        # Test Solar Controller crew
        crew = create_energy_crew(
            query="Is that a good battery level?",
            conversation_context=mock_conversation_context
        )

        print("✅ PASS: create_energy_crew accepts conversation_context parameter")
        print(f"  Crew created with {len(crew.tasks)} task(s)")

        # Check if context is in task description
        task_desc = str(crew.tasks[0].description)
        if "Previous conversation" in task_desc or "65%" in task_desc:
            print("✅ PASS: Context included in task description")
        else:
            print("⚠️  WARNING: Context may not be included in task")

        # Test Energy Orchestrator crew
        crew = create_orchestrator_crew(
            query="Should I charge from grid now?",
            context=mock_conversation_context
        )

        print("✅ PASS: create_orchestrator_crew accepts context parameter")
        print(f"  Crew created with {len(crew.tasks)} task(s)")

        return True

    except Exception as e:
        print(f"❌ FAIL: Error creating crews: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_format_and_size():
    """Test context format and token estimation."""
    print("\n" + "="*70)
    print("TEST: Context Format and Size")
    print("="*70)

    try:
        context = mock_get_context_files()

        char_count = len(context)
        word_count = len(context.split())
        token_estimate = char_count / 4  # Rough estimate

        print(f"✅ Context loaded successfully")
        print(f"  Characters: {char_count:,}")
        print(f"  Words: {word_count:,}")
        print(f"  Estimated tokens: {token_estimate:,.0f}")

        if token_estimate > 10000:
            print("⚠️  WARNING: Context is very large (>10k tokens)")
            print("   Consider reducing context file size")
            return False
        elif token_estimate > 6000:
            print("⚠️  NOTE: Context is moderate (>6k tokens)")
            print("   Monitor token usage in production")
        else:
            print("✅ Context size is reasonable (<6k tokens)")

        # Check format
        if "###" in context or "**" in context:
            print("✅ Context uses markdown formatting")
        else:
            print("⚠️  WARNING: Context may not be well-formatted")

        return True

    except Exception as e:
        print(f"❌ FAIL: Error checking context: {e}")
        return False


def main():
    """Run all mock tests."""
    print("="*70)
    print("CONTEXT FIXES TESTING WITH MOCK DATA")
    print("="*70)
    print("\nSince database is not available in dev environment,")
    print("this script uses mock context data to test the integration.")
    print()

    results = []

    # Run tests
    results.append(("Context Format & Size", test_context_format_and_size()))
    results.append(("Agent Creation with Context", test_agent_with_mock_context()))
    results.append(("Routing Decisions", test_routing_with_context()))
    results.append(("Crew Creation with Context", test_crew_creation_with_context()))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 SUCCESS: All mock tests passed!")
        print("\nThis validates the code structure is correct.")
        print("Next step: Deploy to production and run end-to-end tests with real database.")
        return 0
    else:
        print("\n⚠️  WARNING: Some tests failed")
        print("\nReview failures and fix issues before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
