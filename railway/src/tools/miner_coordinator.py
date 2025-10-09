from crewai.tools import tool
import logging

logger = logging.getLogger(__name__)

@tool("Miner Coordinator")
def coordinate_miners(available_power: float, current_load: float, soc: float) -> str:
    """
    Decide whether to run bitcoin miners based on power availability and battery state.

    Use this tool to make intelligent miner control decisions that balance
    profitability with system reliability and battery health.

    Args:
        available_power: Watts available from solar + battery (after current load)
        current_load: Current house load in watts
        soc: Battery state of charge (0-100)

    Returns:
        str: Decision (START/STOP/MAINTAIN) with reasoning

    Policy (configurable via KB):
    - Miners draw ~2000W
    - Only START if SOC >= 60% (reserve margin)
    - STOP if SOC drops below 40% (protect battery)
    - Need 2500W+ available (miner load + safety buffer)
    - Never start miners if battery critical (<20%)

    Examples:
        >>> coordinate_miners(3500, 1200, 65)
        "START miners. SOC is 65% (above 60% threshold), available power 3500W
        exceeds requirement of 2500W. Profitable to mine with current conditions."

        >>> coordinate_miners(1800, 1200, 55)
        "STOP miners. Available power (1800W) insufficient for safe miner operation
        (need 2500W minimum). SOC is 55% but power constraint takes priority."

        >>> coordinate_miners(3000, 1000, 35)
        "STOP miners. SOC is 35% (below 40% threshold). Battery protection
        takes priority over mining profitability. Will resume when SOC >= 60%."
    """
    try:
        logger.info(f"Miner coordination requested: available={available_power}W, load={current_load}W, SOC={soc}%")

        # Constants (these can be moved to KB later)
        MINER_POWER_DRAW = 2000  # Watts per miner
        MIN_AVAILABLE_POWER = 2500  # Minimum watts needed (miner + buffer)
        MIN_SOC_TO_START = 60  # Don't start unless battery healthy
        MIN_SOC_TO_RUN = 40  # Stop if battery gets low
        CRITICAL_SOC = 20  # Never run if this low

        # Critical battery state - always stop
        if soc < CRITICAL_SOC:
            return (
                f"⛔ STOP miners IMMEDIATELY\n"
                f"SOC: {soc}% (CRITICAL - below {CRITICAL_SOC}%)\n"
                f"Reason: Battery protection is priority #1\n"
                f"Action: Stop all miners immediately\n"
                f"Resume when: SOC >= {MIN_SOC_TO_START}%"
            )

        # Low battery - stop even if power available
        if soc < MIN_SOC_TO_RUN:
            return (
                f"🛑 STOP miners\n"
                f"SOC: {soc}% (below {MIN_SOC_TO_RUN}% threshold)\n"
                f"Available Power: {available_power}W (sufficient but SOC too low)\n"
                f"Reason: Battery protection takes priority over mining\n"
                f"Action: Stop miners, allow battery to charge\n"
                f"Resume when: SOC >= {MIN_SOC_TO_START}%"
            )

        # Insufficient power - stop regardless of SOC
        if available_power < MIN_AVAILABLE_POWER:
            return (
                f"🛑 STOP miners\n"
                f"Available Power: {available_power}W (need {MIN_AVAILABLE_POWER}W minimum)\n"
                f"SOC: {soc}% (adequate but power insufficient)\n"
                f"Reason: Insufficient power for safe miner operation\n"
                f"Miner Draw: ~{MINER_POWER_DRAW}W + {MIN_AVAILABLE_POWER - MINER_POWER_DRAW}W buffer\n"
                f"Action: Stop miners until solar production increases or load decreases"
            )

        # Good conditions but SOC not quite ready to start
        if soc >= MIN_SOC_TO_RUN and soc < MIN_SOC_TO_START and available_power >= MIN_AVAILABLE_POWER:
            return (
                f"⏸️ MAINTAIN (don't start new miners)\n"
                f"SOC: {soc}% (safe to run but below {MIN_SOC_TO_START}% start threshold)\n"
                f"Available Power: {available_power}W (sufficient)\n"
                f"Action: If miners already running, continue. Don't start new ones.\n"
                f"Reason: Build battery reserve before adding more load\n"
                f"Start miners when: SOC >= {MIN_SOC_TO_START}%"
            )

        # Excellent conditions - start or continue miners
        if soc >= MIN_SOC_TO_START and available_power >= MIN_AVAILABLE_POWER:
            return (
                f"✅ START/CONTINUE miners\n"
                f"SOC: {soc}% (above {MIN_SOC_TO_START}% threshold) ✓\n"
                f"Available Power: {available_power}W (exceeds {MIN_AVAILABLE_POWER}W requirement) ✓\n"
                f"Current Load: {current_load}W\n"
                f"Miner Power: ~{MINER_POWER_DRAW}W\n"
                f"Action: Safe to run miners, conditions optimal\n"
                f"Monitor: Stop if SOC drops below {MIN_SOC_TO_RUN}% or available power < {MIN_AVAILABLE_POWER}W"
            )

        # Fallback
        return (
            f"⏸️ MAINTAIN current state\n"
            f"SOC: {soc}%\n"
            f"Available Power: {available_power}W\n"
            f"Action: Continue current operations, monitor conditions"
        )

    except Exception as e:
        logger.error(f"Miner coordinator error: {e}")
        return f"Error in miner coordination: {str(e)}"


# CLI Testing Interface
if __name__ == "__main__":
    """Test the miner coordinator from command line."""
    import sys

    # Default test cases
    test_cases = [
        (3500, 1200, 65),
        (1800, 1200, 55),
        (3000, 1000, 35),
    ]

    if len(sys.argv) == 4:
        # Custom test: python miner_coordinator.py <available_power> <load> <soc>
        available_power = float(sys.argv[1])
        load = float(sys.argv[2])
        soc = float(sys.argv[3])
        print(coordinate_miners.func(available_power, load, soc))
    else:
        # Run all test cases
        for available_power, load, soc in test_cases:
            print(f"\n{'='*70}")
            print(f"TEST: Available={available_power}W, Load={load}W, SOC={soc}%")
            print('='*70)
            print(coordinate_miners.func(available_power, load, soc))
            print('='*70)
