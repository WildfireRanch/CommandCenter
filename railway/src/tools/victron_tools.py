# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/tools/victron_tools.py
# PURPOSE: CrewAI tools for accessing Victron Cerbo battery data
#
# WHAT IT DOES:
#   - Provides agent tools to query Victron battery metrics
#   - Returns accurate SOC, voltage, current, temperature from Cerbo GX
#   - Formats data for natural language agent responses
#
# DEPENDENCIES:
#   - crewai (agent framework)
#   - database utils (for querying victron.battery_readings)
#
# USAGE:
#   from tools.victron_tools import get_victron_battery_status
#
#   # In agent configuration:
#   tools=[get_victron_battery_status]
# ═══════════════════════════════════════════════════════════════════════════

from crewai.tools import tool
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@tool("Get Victron Battery Status")
def get_victron_battery_status() -> str:
    """
    Get accurate battery metrics from Victron Cerbo GX battery monitor.

    Use this tool whenever you need precise battery information including:
    - State of charge (SOC) percentage
    - Battery voltage
    - Battery current (charging/discharging)
    - Battery power
    - Battery state (charging, discharging, idle)
    - Battery temperature

    This data comes directly from the battery shunt and is more accurate
    than inverter-based readings.

    Returns:
        str: Formatted battery status report with all metrics

    Example:
        >>> get_victron_battery_status()
        "Victron Battery Status (as of 2025-12-10 14:30:00):

        State of Charge: 67.5%
        Voltage: 26.4V
        Current: 12.5A (charging)
        Power: 330W
        State: charging
        Temperature: 23.5°C (74.3°F)

        Battery is in healthy condition and charging normally."
    """
    try:
        from ..utils.db import get_connection, query_one

        logger.info("Fetching Victron battery status for agent")

        with get_connection() as conn:
            reading = query_one(
                conn,
                """
                SELECT
                    timestamp,
                    installation_id,
                    soc,
                    voltage,
                    current,
                    power,
                    state,
                    temperature
                FROM victron.battery_readings
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                as_dict=True
            )

        if not reading:
            return (
                "⚠️ No Victron battery data available.\n"
                "The Victron Cerbo GX is not reporting data yet.\n"
                "Check if the poller is running and VRM credentials are configured."
            )

        # Extract values
        soc = reading.get("soc")
        voltage = reading.get("voltage")
        current = reading.get("current")
        power = reading.get("power")
        state = reading.get("state", "unknown")
        temperature = reading.get("temperature")
        timestamp = reading.get("timestamp")

        # Format timestamp
        if timestamp:
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            # Calculate age
            age_seconds = (datetime.now() - timestamp.replace(tzinfo=None)).total_seconds()
            if age_seconds > 600:  # More than 10 minutes old
                time_str += f" (⚠️ Data is {int(age_seconds/60)} minutes old)"
        else:
            time_str = "unknown"

        # Build status report
        report = f"🔋 Victron Battery Status (as of {time_str}):\n\n"

        # Core metrics
        if soc is not None:
            report += f"State of Charge: {soc:.1f}%"
            if soc < 20:
                report += " ⚠️ CRITICAL LOW"
            elif soc < 40:
                report += " ⚠️ LOW"
            elif soc > 90:
                report += " (HIGH)"
            report += "\n"

        if voltage is not None:
            report += f"Voltage: {voltage:.1f}V\n"

        if current is not None:
            report += f"Current: {current:.1f}A"
            if current > 0:
                report += " (charging ⚡)"
            elif current < 0:
                report += " (discharging 🔻)"
            else:
                report += " (idle)"
            report += "\n"

        if power is not None:
            report += f"Power: {abs(power):.0f}W"
            if power > 0:
                report += " (charging)"
            elif power < 0:
                report += " (discharging)"
            report += "\n"

        if state:
            report += f"State: {state}\n"

        if temperature is not None:
            temp_f = (temperature * 9/5) + 32
            report += f"Temperature: {temperature:.1f}°C ({temp_f:.1f}°F)"
            if temperature > 35:
                report += " ⚠️ HIGH"
            elif temperature < 5:
                report += " ⚠️ COLD"
            report += "\n"

        # Add health assessment
        report += "\n"
        if soc is not None:
            if soc < 20:
                report += "⚠️ CRITICAL: Battery needs charging immediately!\n"
            elif soc < 40:
                report += "⚠️ Battery level is low. Consider charging soon.\n"
            elif 40 <= soc <= 80:
                report += "✅ Battery is in optimal operating range (40-80%).\n"
            elif soc > 90:
                report += "Battery is highly charged. Can support heavy loads.\n"

        if temperature is not None and temperature > 35:
            report += "⚠️ WARNING: Battery temperature is high. Monitor closely.\n"

        logger.info(f"Victron battery status retrieved: SOC={soc}%, V={voltage}V")
        return report

    except Exception as e:
        logger.error(f"Error fetching Victron battery status: {e}")
        return f"❌ Error fetching Victron battery data: {str(e)}"


@tool("Get Victron Battery History")
def get_victron_battery_history(hours: int = 24) -> str:
    """
    Get historical battery data from Victron Cerbo GX.

    Use this tool to analyze battery trends over time, including:
    - SOC trends (charging/discharging patterns)
    - Voltage stability
    - Temperature variations
    - Charging/discharging cycles

    Args:
        hours: Number of hours to look back (default: 24, max: 72)

    Returns:
        str: Summary of battery trends and statistics

    Example:
        >>> get_victron_battery_history(24)
        "Victron Battery History (Last 24 hours):

        Data Points: 480 readings

        State of Charge:
          Current: 67.5%
          Min: 42.0% (at 03:15 AM)
          Max: 89.5% (at 01:30 PM)
          Average: 68.2%

        Charging Cycles: 2 full cycles detected
        Temperature Range: 18.5°C - 28.3°C

        Trend: Battery has been stable with normal daily charging cycle."
    """
    try:
        from ..utils.db import get_connection, query_all

        logger.info(f"Fetching Victron battery history for {hours} hours")

        # Limit hours to retention policy (72 hours max)
        hours = min(hours, 72)

        with get_connection() as conn:
            readings = query_all(
                conn,
                """
                SELECT
                    timestamp,
                    soc,
                    voltage,
                    current,
                    power,
                    state,
                    temperature
                FROM victron.battery_readings
                WHERE timestamp >= NOW() - INTERVAL '%s hours'
                ORDER BY timestamp DESC
                """,
                (hours,),
                as_dict=True
            )

        if not readings or len(readings) == 0:
            return (
                f"⚠️ No Victron battery history available for the last {hours} hours.\n"
                "Data may not be flowing from Victron Cerbo GX yet."
            )

        # Calculate statistics
        socs = [r["soc"] for r in readings if r.get("soc") is not None]
        voltages = [r["voltage"] for r in readings if r.get("voltage") is not None]
        temps = [r["temperature"] for r in readings if r.get("temperature") is not None]

        report = f"🔋 Victron Battery History (Last {hours} hours):\n\n"
        report += f"Data Points: {len(readings)} readings\n\n"

        # SOC statistics
        if socs:
            current_soc = readings[0]["soc"]
            min_soc = min(socs)
            max_soc = max(socs)
            avg_soc = sum(socs) / len(socs)

            report += "State of Charge:\n"
            report += f"  Current: {current_soc:.1f}%\n"
            report += f"  Min: {min_soc:.1f}%\n"
            report += f"  Max: {max_soc:.1f}%\n"
            report += f"  Average: {avg_soc:.1f}%\n"
            report += f"  Range: {max_soc - min_soc:.1f}% variation\n\n"

        # Voltage statistics
        if voltages:
            min_v = min(voltages)
            max_v = max(voltages)
            avg_v = sum(voltages) / len(voltages)

            report += "Voltage:\n"
            report += f"  Average: {avg_v:.1f}V\n"
            report += f"  Range: {min_v:.1f}V - {max_v:.1f}V\n\n"

        # Temperature statistics
        if temps:
            min_temp = min(temps)
            max_temp = max(temps)
            avg_temp = sum(temps) / len(temps)

            report += "Temperature:\n"
            report += f"  Average: {avg_temp:.1f}°C\n"
            report += f"  Range: {min_temp:.1f}°C - {max_temp:.1f}°C\n"

            if max_temp > 35:
                report += "  ⚠️ High temperature detected during this period\n"
            report += "\n"

        # Trend analysis
        if socs and len(socs) >= 10:
            # Simple trend: compare first half to second half
            mid = len(socs) // 2
            early_avg = sum(socs[:mid]) / mid
            recent_avg = sum(socs[mid:]) / (len(socs) - mid)

            report += "Trend Analysis:\n"
            if recent_avg > early_avg + 5:
                report += "  📈 Battery has been charging overall\n"
            elif recent_avg < early_avg - 5:
                report += "  📉 Battery has been discharging overall\n"
            else:
                report += "  📊 Battery level has been relatively stable\n"

        logger.info(f"Victron battery history retrieved: {len(readings)} readings over {hours}h")
        return report

    except Exception as e:
        logger.error(f"Error fetching Victron battery history: {e}")
        return f"❌ Error fetching Victron battery history: {str(e)}"


# CLI Testing Interface
if __name__ == "__main__":
    """Test Victron tools from command line."""
    print("=" * 70)
    print("Testing Victron Battery Status")
    print("=" * 70)
    print(get_victron_battery_status.func())

    print("\n" + "=" * 70)
    print("Testing Victron Battery History (24 hours)")
    print("=" * 70)
    print(get_victron_battery_history.func(24))
