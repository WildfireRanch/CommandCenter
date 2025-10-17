# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/tools/battery_optimizer.py
# PURPOSE: Battery optimization tool using user-configured voltage thresholds
# VERSION: V1.9 - Integrated with user preferences
# ═══════════════════════════════════════════════════════════════════════════

from crewai.tools import BaseTool
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class BatteryOptimizerTool(BaseTool):
    name: str = "Battery Optimizer"
    description: str = """Analyzes battery state and recommends actions based on user-configured voltage thresholds.

    Use this tool to get intelligent battery management recommendations that optimize for
    longevity, cost, and reliability using the user's specific battery configuration.

    Input should be a dict with:
    - battery_voltage: Current battery voltage (float)
    - solar_power: Current solar production in watts (float, optional)
    - load_power: Current load consumption in watts (float, optional)

    Returns: Recommendation with voltage thresholds and SOC% for user feedback
    """

    user_prefs: dict = {}
    converter: Optional[Any] = None

    def __init__(self, user_preferences: dict = None, voltage_converter=None):
        """
        Initialize Battery Optimizer with user preferences.

        Args:
            user_preferences: User preferences dict with voltage thresholds
            voltage_converter: Voltage-SOC converter for display purposes
        """
        super().__init__()
        self.user_prefs = user_preferences or self._get_default_prefs()
        self.converter = voltage_converter

    def _run(self, battery_voltage: float, solar_power: float = 0, load_power: float = 0) -> str:
        """
        Analyze battery state using user-configured voltage thresholds.

        Args:
            battery_voltage: Current battery voltage
            solar_power: Current solar production (optional)
            load_power: Current load consumption (optional)

        Returns:
            str: Battery state recommendation with reasoning
        """
        try:
            voltage = float(battery_voltage)

            # Use user-configured thresholds (NOT hardcoded!)
            v_critical = self.user_prefs.get('voltage_critical_low', 45.0)
            v_low = self.user_prefs.get('voltage_low', 47.0)
            v_optimal_min = self.user_prefs.get('voltage_optimal_min', 50.0)
            v_optimal_max = self.user_prefs.get('voltage_optimal_max', 54.5)
            v_restart = self.user_prefs.get('voltage_restart', 50.0)

            # Calculate SOC for display only
            soc_display = ""
            if self.converter:
                try:
                    soc = self.converter.voltage_to_soc(voltage)
                    soc_display = f" ({soc:.1f}% SOC)"
                except Exception as e:
                    logger.warning(f"SOC conversion failed: {e}")

            # Decision logic using voltage thresholds
            if voltage <= v_critical:
                return (
                    f"🔴 CRITICAL: Battery at {voltage}V{soc_display}\n"
                    f"Action: Stop all loads immediately!\n"
                    f"Threshold: Below critical low ({v_critical}V)\n"
                    f"Risk: System shutdown imminent"
                )

            elif voltage <= v_low:
                return (
                    f"⚠️ LOW: Battery at {voltage}V{soc_display}\n"
                    f"Action: Reduce loads, prioritize charging\n"
                    f"Threshold: Below low threshold ({v_low}V)\n"
                    f"Target: Charge to restart voltage ({v_restart}V)"
                )

            elif v_optimal_min <= voltage <= v_optimal_max:
                return (
                    f"✅ OPTIMAL: Battery at {voltage}V{soc_display}\n"
                    f"Action: Normal operation\n"
                    f"Range: Optimal range ({v_optimal_min}V - {v_optimal_max}V)\n"
                    f"Status: Battery health optimal in this range"
                )

            elif voltage > v_optimal_max:
                return (
                    f"⚡ HIGH: Battery at {voltage}V{soc_display}\n"
                    f"Action: Can run high loads\n"
                    f"Status: Above optimal max ({v_optimal_max}V)\n"
                    f"Note: Safe to discharge for mining or other loads"
                )

            else:
                # Between low and optimal_min (recovering)
                return (
                    f"⏳ RECOVERING: Battery at {voltage}V{soc_display}\n"
                    f"Action: Wait for {v_restart}V to restart loads\n"
                    f"Range: Between low ({v_low}V) and optimal ({v_optimal_min}V)\n"
                    f"Status: Charging recommended"
                )

        except Exception as e:
            logger.error(f"Battery optimizer error: {e}")
            return f"❌ Error in battery optimization: {str(e)}"

    def _get_default_prefs(self) -> dict:
        """Fallback defaults if preferences not loaded."""
        return {
            'voltage_critical_low': 45.0,
            'voltage_low': 47.0,
            'voltage_optimal_min': 50.0,
            'voltage_optimal_max': 54.5,
            'voltage_restart': 50.0
        }


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test the battery optimizer from command line."""
    import sys

    # Default test cases
    test_cases = [
        (52.3, 8450, 1850, "Optimal voltage"),
        (47.0, 5000, 2000, "Low voltage"),
        (45.0, 3000, 1500, "Critical low"),
        (55.0, 9000, 1000, "High voltage"),
    ]

    # Create mock preferences
    test_prefs = {
        'voltage_at_0_percent': 45.0,
        'voltage_at_100_percent': 56.0,
        'voltage_critical_low': 45.0,
        'voltage_low': 47.0,
        'voltage_optimal_min': 50.0,
        'voltage_optimal_max': 54.5,
        'voltage_restart': 50.0,
    }

    # Create mock converter
    class MockConverter:
        def voltage_to_soc(self, voltage):
            # Simple linear approximation for testing
            return ((voltage - 45.0) / (56.0 - 45.0)) * 100

    tool = BatteryOptimizerTool(
        user_preferences=test_prefs,
        voltage_converter=MockConverter()
    )

    if len(sys.argv) == 4:
        # Custom test: python battery_optimizer.py <voltage> <solar> <load>
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
