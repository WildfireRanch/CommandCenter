from crewai.tools import tool
import logging

logger = logging.getLogger(__name__)

@tool("Battery Optimizer")
def optimize_battery(soc: float, time_of_day: int, weather_forecast: str = "unknown") -> str:
    """
    Recommend battery charge/discharge actions based on current state.

    Use this tool to get intelligent battery management recommendations that
    optimize for longevity, cost, and reliability.

    Args:
        soc: Current battery state of charge (0-100)
        time_of_day: Hour in 24-hour format (0-23)
        weather_forecast: "sunny", "cloudy", "clear", or "unknown"

    Returns:
        str: Recommendation with reasoning

    Decision Logic:
    - If SOC < 20%: CRITICAL - charge immediately from any source
    - If SOC < 40% and time_of_day > 16: Charge tonight (preserve battery for morning)
    - If SOC > 80% and time_of_day < 16 and sunny: Allow discharge (excess solar available)
    - If SOC 40-80%: Maintain (normal operation range)
    - Always include target SOC and reasoning

    Examples:
        >>> optimize_battery(45, 18, "clear")
        "CHARGE recommended. SOC is 45% and solar production will stop soon.
        Target 60%+ for morning operations. Grid charging acceptable tonight."

        >>> optimize_battery(85, 12, "sunny")
        "DISCHARGE OK. SOC is 85%, solar production strong (midday, sunny).
        Can discharge to 60% supporting miners and load. Battery longevity: optimal range is 40-80%."

        >>> optimize_battery(18, 14, "cloudy")
        "CRITICAL CHARGE. SOC is 18% - below minimum safe threshold (20%).
        Charge immediately from any available source. Risk of system shutdown."
    """
    try:
        logger.info(f"Battery optimization requested: SOC={soc}%, hour={time_of_day}, weather={weather_forecast}")

        # Critical low battery
        if soc < 20:
            return (
                f"⚠️ CRITICAL CHARGE IMMEDIATELY\n"
                f"SOC: {soc}% (below minimum 20% threshold)\n"
                f"Action: Charge from any available source NOW\n"
                f"Risk: System shutdown imminent\n"
                f"Target: Bring to 40%+ ASAP"
            )

        # Low battery, approaching evening
        if soc < 40 and time_of_day >= 16:
            return (
                f"🔋 CHARGE recommended\n"
                f"SOC: {soc}% (below optimal 40-80% range)\n"
                f"Time: {time_of_day}:00 (solar production ending soon)\n"
                f"Action: Begin charging tonight\n"
                f"Target: 60%+ for reliable morning operations\n"
                f"Source: Grid charging acceptable during off-peak hours"
            )

        # High battery, strong solar
        if soc > 80 and time_of_day >= 8 and time_of_day <= 16:
            if weather_forecast == "sunny":
                return (
                    f"✅ DISCHARGE OK\n"
                    f"SOC: {soc}% (above optimal range)\n"
                    f"Time: {time_of_day}:00 (peak solar hours)\n"
                    f"Weather: {weather_forecast} (strong production expected)\n"
                    f"Action: Allow discharge to 60% supporting load and miners\n"
                    f"Note: Staying in 40-80% range extends battery life"
                )
            else:
                return (
                    f"⚡ MAINTAIN recommended\n"
                    f"SOC: {soc}% (high but weather uncertain)\n"
                    f"Time: {time_of_day}:00\n"
                    f"Weather: {weather_forecast}\n"
                    f"Action: Hold current level, monitor production\n"
                    f"Reason: Cloudy conditions may reduce solar charging ability"
                )

        # Normal operating range
        if 40 <= soc <= 80:
            return (
                f"✅ MAINTAIN optimal range\n"
                f"SOC: {soc}% (optimal 40-80% for battery longevity)\n"
                f"Time: {time_of_day}:00\n"
                f"Action: No action needed, continue normal operations\n"
                f"Status: Battery health optimal in this range"
            )

        # Edge cases
        return (
            f"📊 MODERATE action suggested\n"
            f"SOC: {soc}%\n"
            f"Time: {time_of_day}:00\n"
            f"Action: Move toward optimal 40-80% range\n"
            f"Target: {'Charge to 60%' if soc < 40 else 'Discharge to 60%'}"
        )

    except Exception as e:
        logger.error(f"Battery optimizer error: {e}")
        return f"Error in battery optimization: {str(e)}"


# CLI Testing Interface
if __name__ == "__main__":
    """Test the battery optimizer from command line."""
    import sys

    # Default test cases
    test_cases = [
        (45, 18, "clear"),
        (85, 12, "sunny"),
        (18, 14, "cloudy"),
    ]

    if len(sys.argv) == 4:
        # Custom test: python battery_optimizer.py <soc> <hour> <weather>
        soc = float(sys.argv[1])
        hour = int(sys.argv[2])
        weather = sys.argv[3]
        print(optimize_battery.func(soc, hour, weather))
    else:
        # Run all test cases
        for soc, hour, weather in test_cases:
            print(f"\n{'='*70}")
            print(f"TEST: SOC={soc}%, Hour={hour}, Weather={weather}")
            print('='*70)
            print(optimize_battery.func(soc, hour, weather))
            print('='*70)
