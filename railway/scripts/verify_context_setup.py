#!/usr/bin/env python3
"""
Verify Context Fixes Setup - Production Deployment Check

This script validates that the context fixes are properly configured
in a production environment with database access.

Run this AFTER deploying to ensure everything is ready for testing.

Usage:
    cd railway
    python scripts/verify_context_setup.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def check_database_connection():
    """Check database connection is working."""
    print("\n" + "="*70)
    print("1. DATABASE CONNECTION")
    print("="*70)

    try:
        from src.utils.db import get_connection, query_all

        with get_connection() as conn:
            result = query_all(conn, "SELECT 1 as test", as_dict=True)
            print("✅ PASS: Database connection successful")
            return True
    except Exception as e:
        print(f"❌ FAIL: Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("- Check DATABASE_URL environment variable")
        print("- Verify network connectivity to database")
        print("- Check database credentials")
        return False


def check_context_files_exist():
    """Check if context files exist in knowledge base."""
    print("\n" + "="*70)
    print("2. CONTEXT FILES IN KNOWLEDGE BASE")
    print("="*70)

    try:
        from src.utils.db import get_connection, query_all

        with get_connection() as conn:
            context_docs = query_all(
                conn,
                "SELECT id, title, is_context_file, LENGTH(full_content) as content_length FROM kb_documents WHERE is_context_file = TRUE ORDER BY title",
                as_dict=True
            )

        if not context_docs:
            print("❌ FAIL: No context files found in knowledge base")
            print("\nTroubleshooting:")
            print("- Run: python -m src.kb.sync (to sync from Google Drive)")
            print("- Or manually mark docs as context files:")
            print("  UPDATE kb_documents SET is_context_file = TRUE WHERE title IN ('...');")
            return False

        print(f"✅ PASS: Found {len(context_docs)} context file(s)")
        print("\nContext files:")
        for doc in context_docs:
            print(f"  - {doc['title']} ({doc['content_length']:,} characters)")

        # Check total size
        total_chars = sum(doc['content_length'] for doc in context_docs)
        total_tokens_estimate = total_chars / 4  # Rough estimate: 1 token ≈ 4 chars

        print(f"\nTotal context size: {total_chars:,} characters (~{total_tokens_estimate:,.0f} tokens)")

        if total_tokens_estimate > 10000:
            print("⚠️  WARNING: Context size is large (>10k tokens)")
            print("   Consider splitting or reducing context files")
        elif total_tokens_estimate > 6000:
            print("⚠️  NOTE: Context size is moderate (>6k tokens)")
            print("   Monitor token usage in production")
        else:
            print("✅ Context size is reasonable (<6k tokens)")

        return True

    except Exception as e:
        print(f"❌ FAIL: Error checking context files: {e}")
        return False


def check_get_context_files_function():
    """Check get_context_files() function returns data."""
    print("\n" + "="*70)
    print("3. GET_CONTEXT_FILES() FUNCTION")
    print("="*70)

    try:
        from src.tools.kb_search import get_context_files

        context = get_context_files()

        if not context:
            print("❌ FAIL: get_context_files() returned empty string")
            print("\nTroubleshooting:")
            print("- Check context files exist (see test #2)")
            print("- Check database connection")
            return False

        print("✅ PASS: get_context_files() returned content")

        # Show preview
        lines = context.split('\n')
        print(f"\nContent preview (first 10 lines of {len(lines)} total):")
        for line in lines[:10]:
            print(f"  {line}")

        if len(lines) > 10:
            print("  ...")

        return True

    except Exception as e:
        print(f"❌ FAIL: Error calling get_context_files(): {e}")
        import traceback
        traceback.print_exc()
        return False


def check_agent_loads_context():
    """Check that creating an agent loads context into backstory."""
    print("\n" + "="*70)
    print("4. AGENT CONTEXT LOADING")
    print("="*70)

    try:
        from src.agents.solar_controller import create_energy_monitor_agent

        agent = create_energy_monitor_agent()

        if "SYSTEM CONTEXT" not in agent.backstory:
            print("❌ FAIL: Agent backstory does not contain 'SYSTEM CONTEXT' section")
            print("\nTroubleshooting:")
            print("- Check get_context_files() returns data (see test #3)")
            print("- Verify create_energy_monitor_agent() code includes context embedding")
            return False

        print("✅ PASS: Agent backstory contains SYSTEM CONTEXT section")

        # Show preview
        lines = agent.backstory.split('\n')
        print(f"\nBackstory preview (first 15 lines of {len(lines)} total):")
        for i, line in enumerate(lines[:15]):
            print(f"  {line}")

        if len(lines) > 15:
            print("  ...")

        return True

    except Exception as e:
        print(f"❌ FAIL: Error creating agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_routing_returns_decisions():
    """Check that routing tools return JSON decisions."""
    print("\n" + "="*70)
    print("5. ROUTING TOOLS RETURN DECISIONS")
    print("="*70)

    try:
        from src.agents.manager import route_to_solar_controller
        import json

        # Test routing tool
        result = route_to_solar_controller.func("What's my battery level?")

        # Parse as JSON
        decision = json.loads(result)

        if decision.get("action") != "route":
            print(f"❌ FAIL: Routing tool did not return action='route'")
            print(f"   Got: {decision}")
            return False

        if decision.get("agent") != "Solar Controller":
            print(f"❌ FAIL: Routing tool did not return correct agent")
            print(f"   Got: {decision}")
            return False

        print("✅ PASS: Routing tool returns correct JSON decision")
        print(f"\nExample routing decision:")
        print(f"  {json.dumps(decision, indent=2)}")

        return True

    except Exception as e:
        print(f"❌ FAIL: Error testing routing tool: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_crew_functions_accept_context():
    """Check that crew creation functions accept context parameters."""
    print("\n" + "="*70)
    print("6. CREW FUNCTIONS ACCEPT CONTEXT")
    print("="*70)

    try:
        from src.agents.solar_controller import create_energy_crew
        from src.agents.energy_orchestrator import create_orchestrator_crew
        import inspect

        # Check create_energy_crew signature
        sig = inspect.signature(create_energy_crew)
        params = list(sig.parameters.keys())

        if "conversation_context" not in params:
            print("❌ FAIL: create_energy_crew missing 'conversation_context' parameter")
            print(f"   Parameters: {params}")
            return False

        print("✅ PASS: create_energy_crew has 'conversation_context' parameter")

        # Check create_orchestrator_crew signature
        sig = inspect.signature(create_orchestrator_crew)
        params = list(sig.parameters.keys())

        if "context" not in params:
            print("❌ FAIL: create_orchestrator_crew missing 'context' parameter")
            print(f"   Parameters: {params}")
            return False

        print("✅ PASS: create_orchestrator_crew has 'context' parameter")

        # Test creating crew with context
        test_context = "Previous conversation: The battery was at 50%."

        crew = create_energy_crew(
            query="What's my battery level?",
            conversation_context=test_context
        )

        print("\n✅ PASS: Successfully created crew with context parameter")

        return True

    except Exception as e:
        print(f"❌ FAIL: Error checking crew functions: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification checks."""
    print("="*70)
    print("CONTEXT FIXES VERIFICATION")
    print("="*70)
    print("\nThis script validates that context fixes are properly configured.")
    print("Run this after deploying to production environment.")
    print()

    results = []

    # Run checks
    results.append(("Database Connection", check_database_connection()))
    results.append(("Context Files Exist", check_context_files_exist()))
    results.append(("get_context_files()", check_get_context_files_function()))
    results.append(("Agent Loads Context", check_agent_loads_context()))
    results.append(("Routing Returns Decisions", check_routing_returns_decisions()))
    results.append(("Crew Functions Accept Context", check_crew_functions_accept_context()))

    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Results: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 SUCCESS: All verification checks passed!")
        print("\nNext steps:")
        print("1. Run end-to-end tests (see docs/QUICK_REFERENCE_DEPLOYMENT.md)")
        print("2. Monitor performance metrics")
        print("3. Check agent responses for quality")
        return 0
    else:
        print("\n⚠️  WARNING: Some checks failed")
        print("\nReview the failures above and follow troubleshooting steps.")
        print("Do not proceed to end-to-end testing until all checks pass.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
