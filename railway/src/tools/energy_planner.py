from crewai.tools import tool
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@tool("Energy Planner")
def create_energy_plan(current_soc: float, time_now: int, forecast: str = "typical") -> str:
    """
    Create 24-hour energy action plan based on current state and forecast.

    Use this tool to generate hour-by-hour recommendations for the next 24 hours,
    optimizing battery usage, miner operations, and grid interaction.

    Args:
        current_soc: Current battery state of charge (0-100)
        time_now: Current hour in 24-hour format (0-23)
        forecast: "sunny", "cloudy", "typical", or "rainy"

    Returns:
        str: Formatted 24-hour plan with hourly recommendations

    Planning Logic:
    - Solar production curve: 0W before 6am, peak 10am-2pm, 0W after 6pm
    - Forecast adjusts peak production (sunny=100%, typical=75%, cloudy=50%, rainy=25%)
    - Battery: charge to 60%+ before peak solar, discharge to 40% overnight OK
    - Miners: run during peak solar (10am-4pm) if conditions allow
    - Grid: use for charging only if SOC critical or off-peak hours

    Example output:
        "📅 24-Hour Energy Plan (Starting 18:00)

        Current Status: SOC 52%, Forecast: typical

        NOW (18:00-22:00) - Evening Charge Window
        ├─ Solar: 0W (sunset complete)
        ├─ Battery: Charge from grid if < 40% (currently 52% - OK)
        ├─ Miners: OFF (conserve battery for overnight)
        └─ Action: Minimal discharge, house load only

        22:00-06:00 - Overnight Conservation
        ├─ Solar: 0W
        ├─ Battery: Slow discharge (house load ~1200W)
        ├─ Miners: OFF
        └─ Target SOC at 6am: 45%+ (currently 52%, should end ~48%)

        06:00-10:00 - Morning Solar Ramp
        ├─ Solar: 0W → 4000W (gradual increase)
        ├─ Battery: Begin charging as production exceeds load
        ├─ Miners: OFF (let battery charge first)
        └─ Target: Reach 60%+ by 10am

        10:00-16:00 - Peak Production Window ☀️
        ├─ Solar: 5000-6000W (forecast: typical = 75% of max)
        ├─ Battery: Maintain 60-80% (optimal range)
        ├─ Miners: START if SOC >= 60% and available power > 2500W
        ├─ Load: House (~1200W) + Miners (~2000W) = 3200W
        └─ Action: Profitable mining with excess solar

        16:00-18:00 - Evening Wind-Down
        ├─ Solar: 4000W → 0W (rapid decline)
        ├─ Battery: Stop charging, prepare for evening
        ├─ Miners: STOP by 17:00 latest
        └─ Target: Enter evening at 55%+ SOC"
    """
    try:
        logger.info(f"Energy plan requested: SOC={current_soc}%, hour={time_now}, forecast={forecast}")

        # Solar production multipliers based on forecast
        forecast_multipliers = {
            "sunny": 1.0,
            "typical": 0.75,
            "cloudy": 0.50,
            "rainy": 0.25
        }
        multiplier = forecast_multipliers.get(forecast.lower(), 0.75)

        # Build the plan
        plan = f"📅 24-Hour Energy Plan (Starting {time_now:02d}:00)\n\n"
        plan += f"Current Status: SOC {current_soc}%, Forecast: {forecast}\n"
        plan += f"Solar Production: {int(multiplier * 100)}% of typical\n\n"

        # Current evening (18:00-22:00)
        if 18 <= time_now or time_now < 6:
            plan += "🌙 NOW → Evening/Night Period (18:00-06:00)\n"
            plan += "├─ Solar: 0W (no production overnight)\n"
            if current_soc < 40:
                plan += f"├─ Battery: CHARGE from grid (currently {current_soc}% - below 40%)\n"
                plan += "├─ Miners: OFF (allow battery to charge)\n"
                plan += f"└─ ⚠️ PRIORITY: Bring SOC to 60%+ before morning\n\n"
            else:
                plan += f"├─ Battery: Slow discharge OK (currently {current_soc}% - safe)\n"
                plan += "├─ Miners: OFF (conserve for overnight)\n"
                plan += f"└─ Expected SOC at 6am: ~{max(40, current_soc - 8)}% (normal overnight draw)\n\n"

        # Morning (6:00-10:00)
        plan += "🌅 Morning Solar Ramp (06:00-10:00)\n"
        plan += f"├─ Solar: 0W → {int(4000 * multiplier)}W (gradual increase)\n"
        plan += "├─ Battery: Begin charging as production > load\n"
        plan += "├─ Miners: OFF (let battery charge first)\n"
        plan += "└─ Target: Reach 60%+ SOC by 10am for miner operations\n\n"

        # Peak production (10:00-16:00)
        plan += f"☀️ Peak Production Window (10:00-16:00)\n"
        plan += f"├─ Solar: {int(5000 * multiplier)}-{int(6000 * multiplier)}W (peak hours)\n"

        if multiplier >= 0.6:  # Good solar conditions
            plan += "├─ Battery: Maintain 60-80% (optimal range)\n"
            plan += "├─ Miners: START if SOC >= 60% and power available\n"
            plan += f"├─ Estimated available: {int(5000 * multiplier)} - 1200 (load) = {int(5000 * multiplier - 1200)}W\n"
            plan += "└─ ✅ PROFITABLE mining window - excess solar available\n\n"
        else:  # Poor solar conditions
            plan += "├─ Battery: Charge what you can (limited production)\n"
            plan += "├─ Miners: Likely OFF (insufficient solar)\n"
            plan += f"├─ Estimated available: {int(5000 * multiplier)} - 1200 (load) = {int(5000 * multiplier - 1200)}W\n"
            plan += f"└─ ⚠️ LOW PRODUCTION ({forecast}) - conserve battery\n\n"

        # Evening wind-down (16:00-18:00)
        plan += "🌇 Evening Wind-Down (16:00-18:00)\n"
        plan += f"├─ Solar: {int(4000 * multiplier)}W → 0W (rapid decline)\n"
        plan += "├─ Battery: Stop charging, prepare for night\n"
        plan += "├─ Miners: STOP by 17:00 latest\n"
        plan += "└─ Target: Enter evening at 55%+ SOC\n\n"

        # Summary
        plan += "📊 24-Hour Summary\n"
        plan += f"├─ Expected Solar: {int(20 * multiplier)}kWh (forecast-adjusted)\n"
        plan += f"├─ Miner Potential: {'6 hours' if multiplier >= 0.6 else '0-2 hours'} (10am-4pm window)\n"
        plan += f"├─ Grid Usage: {'Minimal' if current_soc >= 40 else 'Charge tonight required'}\n"
        plan += "└─ Battery Cycles: ~0.3 (healthy, extends battery life)\n"

        return plan

    except Exception as e:
        logger.error(f"Energy planner error: {e}")
        return f"Error creating energy plan: {str(e)}"


# CLI Testing Interface
if __name__ == "__main__":
    """Test the energy planner from command line."""
    import sys

    # Default test cases
    test_cases = [
        (52, 18, "typical"),
        (35, 8, "sunny"),
    ]

    if len(sys.argv) == 4:
        # Custom test: python energy_planner.py <soc> <hour> <forecast>
        soc = float(sys.argv[1])
        hour = int(sys.argv[2])
        forecast = sys.argv[3]
        print(create_energy_plan.func(soc, hour, forecast))
    else:
        # Run all test cases
        for soc, hour, forecast in test_cases:
            print(f"\n{'='*70}")
            print(f"TEST: SOC={soc}%, Hour={hour}, Forecast={forecast}")
            print('='*70)
            print(create_energy_plan.func(soc, hour, forecast))
            print('='*70)
