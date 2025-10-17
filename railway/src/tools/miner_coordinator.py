# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/tools/miner_coordinator.py
# PURPOSE: Miner coordination tool with priority-based allocation from database
# VERSION: V1.9 - Integrated with user preferences and miner profiles
# ═══════════════════════════════════════════════════════════════════════════

from crewai.tools import BaseTool
from typing import Any, Optional
import logging
import os
from ..utils.db import get_connection, query_all

logger = logging.getLogger(__name__)
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "a0000000-0000-0000-0000-000000000001")


class MinerCoordinatorTool(BaseTool):
    name: str = "Miner Coordinator"
    description: str = """Manages multiple miners with priority-based allocation using database profiles.

    Use this tool to make intelligent miner control decisions that balance profitability
    with system reliability and battery health, using real miner profiles from the database.

    Input should be a dict with:
    - battery_voltage: Current battery voltage (float)
    - solar_power: Current solar production in watts (float)
    - load_power: Current load consumption in watts (float)

    Returns: Priority-based allocation decisions for all active miners
    """

    user_prefs: dict = {}
    converter: Optional[Any] = None

    def __init__(self, user_preferences: dict = None, voltage_converter=None):
        """
        Initialize Miner Coordinator with user preferences.

        Args:
            user_preferences: User preferences dict with voltage thresholds
            voltage_converter: Voltage-SOC converter for display purposes
        """
        super().__init__()
        self.user_prefs = user_preferences or {}
        self.converter = voltage_converter

    def _run(self, battery_voltage: float, solar_power: float, load_power: float) -> str:
        """
        Coordinate multiple miners based on priority and constraints.

        Args:
            battery_voltage: Current battery voltage
            solar_power: Current solar production in watts
            load_power: Current load consumption in watts

        Returns:
            str: Priority-based allocation decisions
        """
        try:
            voltage = float(battery_voltage)
            solar = float(solar_power)
            load = float(load_power)

            # Load all active miners from database
            miners = self._load_miners()

            if not miners:
                return "📭 No miner profiles configured in database."

            # Calculate available power budget
            available_power = solar - load
            power_budget = available_power

            decisions = []
            soc_display = ""

            # Calculate SOC for display
            if self.converter:
                try:
                    soc = self.converter.voltage_to_soc(voltage)
                    soc_display = f" ({soc:.1f}% SOC)"
                except Exception as e:
                    logger.warning(f"SOC conversion failed: {e}")

            # Header with current state
            decisions.append(f"🔋 Battery: {voltage}V{soc_display}")
            decisions.append(f"☀️ Solar: {solar:,.0f}W | ⚡ Load: {load:,.0f}W")
            decisions.append(f"💰 Available power budget: {available_power:,.0f}W")
            decisions.append("")
            decisions.append("🤖 MINER ALLOCATION (Priority Order):")
            decisions.append("─" * 60)

            # Sort miners by priority (1 = highest)
            sorted_miners = sorted(miners, key=lambda m: m['priority_level'])

            for miner in sorted_miners:
                decision = self._evaluate_miner(miner, voltage, solar, power_budget)
                decisions.append(decision)

                # If miner can start, deduct from budget
                if "✅ START" in decision or "CONTINUE" in decision:
                    power_budget -= miner['power_draw_watts']

            decisions.append("─" * 60)
            decisions.append(f"💡 Final power budget remaining: {power_budget:,.0f}W")

            return "\n".join(decisions)

        except Exception as e:
            logger.error(f"Miner coordinator error: {e}")
            return f"❌ Error in miner coordination: {str(e)}"

    def _load_miners(self) -> list:
        """Load active miners from database."""
        try:
            with get_connection() as conn:
                miners = query_all(
                    conn,
                    """
                    SELECT
                        id, name, model, power_draw_watts, priority_level,
                        start_voltage, stop_voltage, emergency_stop_voltage,
                        require_excess_solar, minimum_excess_watts,
                        minimum_solar_production_watts, enabled
                    FROM miner_profiles
                    WHERE user_id = %s::uuid AND enabled = true
                    ORDER BY priority_level ASC
                    """,
                    (DEFAULT_USER_ID,),
                    as_dict=True
                )
                return list(miners)
        except Exception as e:
            logger.error(f"Failed to load miners from database: {e}")
            return []

    def _evaluate_miner(self, miner: dict, voltage: float, solar: float, budget: float) -> str:
        """
        Evaluate if a miner should start based on all constraints.

        Args:
            miner: Miner profile dict from database
            voltage: Current battery voltage
            solar: Current solar production
            budget: Remaining power budget

        Returns:
            str: Decision string with emoji status
        """
        name = miner['name']
        priority = miner['priority_level']
        power = miner['power_draw_watts']

        # Emergency stop check (highest priority)
        emergency_stop = miner.get('emergency_stop_voltage')
        if emergency_stop and voltage <= emergency_stop:
            return (
                f"🛑 [P{priority}] {name}: EMERGENCY STOP - "
                f"voltage {voltage}V ≤ emergency {emergency_stop}V"
            )

        # Stop voltage check
        stop_voltage = miner.get('stop_voltage')
        if stop_voltage and voltage < stop_voltage:
            return (
                f"❌ [P{priority}] {name}: STOP - "
                f"voltage {voltage}V < stop {stop_voltage}V"
            )

        # Start voltage check (need to be above this to start)
        start_voltage = miner.get('start_voltage')
        if start_voltage and voltage < start_voltage:
            return (
                f"⏸️ [P{priority}] {name}: WAIT - "
                f"voltage {voltage}V < start {start_voltage}V ({power:,}W)"
            )

        # Power budget check
        if budget < power:
            return (
                f"⏳ [P{priority}] {name}: WAIT - "
                f"insufficient power (need {power:,}W, {budget:,.0f}W available)"
            )

        # Check solar requirements (for dump loads)
        if miner.get('require_excess_solar'):
            min_solar = miner.get('minimum_solar_production_watts', 0)
            if solar < min_solar:
                return (
                    f"☀️ [P{priority}] {name}: WAIT - "
                    f"insufficient solar ({solar:,.0f}W, need {min_solar:,}W)"
                )

            min_excess = miner.get('minimum_excess_watts', 0)
            excess = solar - power
            if excess < min_excess:
                return (
                    f"⚡ [P{priority}] {name}: WAIT - "
                    f"insufficient excess ({excess:,.0f}W, need {min_excess:,}W)"
                )

        # All checks passed!
        return (
            f"✅ [P{priority}] {name}: START - "
            f"{power:,}W allocated (budget remaining: {budget - power:,.0f}W)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test the miner coordinator from command line."""
    import sys

    # Default test cases
    test_cases = [
        (52.3, 8450, 1850, "High voltage, good solar"),
        (47.0, 5000, 2000, "Low voltage, moderate solar"),
        (54.0, 12000, 1500, "High voltage, excellent solar"),
    ]

    # Create mock preferences
    test_prefs = {
        'voltage_at_0_percent': 45.0,
        'voltage_at_100_percent': 56.0,
    }

    # Create mock converter
    class MockConverter:
        def voltage_to_soc(self, voltage):
            return ((voltage - 45.0) / (56.0 - 45.0)) * 100

    tool = MinerCoordinatorTool(
        user_preferences=test_prefs,
        voltage_converter=MockConverter()
    )

    if len(sys.argv) == 4:
        # Custom test: python miner_coordinator.py <voltage> <solar> <load>
        voltage = float(sys.argv[1])
        solar = float(sys.argv[2])
        load = float(sys.argv[3])
        print(tool._run(voltage, solar, load))
    else:
        # Run all test cases
        for voltage, solar, load, description in test_cases:
            print(f"\n{'='*70}")
            print(f"TEST: {description}")
            print(f"Voltage={voltage}V, Solar={solar}W, Load={load}W")
            print('='*70)
            print(tool._run(voltage, solar, load))
            print('='*70)
