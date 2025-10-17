"""
Voltage-SOC Converter Service

WHAT: Bidirectional voltage <-> SOC% conversion using user calibration
WHY: Agents make decisions on voltage, but users want to see SOC%
HOW: Linear interpolation or custom curve-based interpolation

Usage:
    converter = VoltageSocConverter(user_preferences)
    soc = converter.voltage_to_soc(52.3)  # Returns: 65.5
    voltage = converter.soc_to_voltage(50.0)  # Returns: 50.5
"""

from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class VoltageSocConverter:
    """
    Bidirectional voltage <-> SOC% conversion using user calibration.

    WHAT: Converts battery voltage to SOC% and vice versa
    WHY: Agents make decisions on voltage, but users want to see SOC%
    HOW: Linear interpolation or custom curve-based interpolation

    Usage:
        converter = VoltageSocConverter(user_preferences)
        soc = converter.voltage_to_soc(52.3)  # Returns: 65.5
        voltage = converter.soc_to_voltage(50.0)  # Returns: 50.5
    """

    def __init__(self, preferences: Dict[str, Any]):
        """
        Initialize converter with user preferences.

        Args:
            preferences: User preferences dict from database
                - voltage_at_0_percent: Minimum voltage (e.g., 45.0V)
                - voltage_at_100_percent: Maximum voltage (e.g., 56.0V)
                - voltage_curve: Optional list of calibration points
        """
        self.v_min = float(preferences['voltage_at_0_percent'])
        self.v_max = float(preferences['voltage_at_100_percent'])
        self.curve = preferences.get('voltage_curve')

        logger.debug(f"Initialized converter: {self.v_min}V-{self.v_max}V")

    def voltage_to_soc(self, voltage: float) -> float:
        """
        Convert voltage to SOC percentage.

        Args:
            voltage: Battery voltage in volts

        Returns:
            SOC percentage (0-100)

        Example:
            >>> converter.voltage_to_soc(52.3)
            65.5
        """
        # Clamp to valid range
        if voltage <= self.v_min:
            return 0.0
        if voltage >= self.v_max:
            return 100.0

        # Use custom curve if available
        if self.curve and isinstance(self.curve, list) and len(self.curve) > 0:
            return self._interpolate_from_curve(voltage, self.curve)

        # Linear interpolation (fallback)
        return 100.0 * (voltage - self.v_min) / (self.v_max - self.v_min)

    def soc_to_voltage(self, soc: float) -> float:
        """
        Convert SOC percentage to voltage.

        Args:
            soc: State of charge percentage (0-100)

        Returns:
            Battery voltage in volts

        Example:
            >>> converter.soc_to_voltage(50.0)
            50.5
        """
        # Clamp to valid range
        if soc <= 0:
            return self.v_min
        if soc >= 100:
            return self.v_max

        # Use custom curve if available
        if self.curve and isinstance(self.curve, list) and len(self.curve) > 0:
            return self._reverse_interpolate_from_curve(soc, self.curve)

        # Linear interpolation (fallback)
        return self.v_min + (soc / 100.0) * (self.v_max - self.v_min)

    def _interpolate_from_curve(self, voltage: float, curve: List[Dict]) -> float:
        """
        Interpolate SOC from voltage using calibration curve.

        Curve format: [{"soc": 0, "voltage": 45.0}, {"soc": 15, "voltage": 47.0}, ...]
        """
        # Sort curve by voltage
        sorted_curve = sorted(curve, key=lambda x: x['voltage'])

        # Find bracketing points
        for i in range(len(sorted_curve) - 1):
            v1, soc1 = sorted_curve[i]['voltage'], sorted_curve[i]['soc']
            v2, soc2 = sorted_curve[i + 1]['voltage'], sorted_curve[i + 1]['soc']

            if v1 <= voltage <= v2:
                # Linear interpolation between points
                ratio = (voltage - v1) / (v2 - v1)
                return soc1 + ratio * (soc2 - soc1)

        # Shouldn't reach here due to clamping, but fallback to linear
        return 100.0 * (voltage - self.v_min) / (self.v_max - self.v_min)

    def _reverse_interpolate_from_curve(self, soc: float, curve: List[Dict]) -> float:
        """
        Interpolate voltage from SOC using calibration curve.
        """
        # Sort curve by SOC
        sorted_curve = sorted(curve, key=lambda x: x['soc'])

        # Find bracketing points
        for i in range(len(sorted_curve) - 1):
            soc1, v1 = sorted_curve[i]['soc'], sorted_curve[i]['voltage']
            soc2, v2 = sorted_curve[i + 1]['soc'], sorted_curve[i + 1]['voltage']

            if soc1 <= soc <= soc2:
                # Linear interpolation between points
                ratio = (soc - soc1) / (soc2 - soc1)
                return v1 + ratio * (v2 - v1)

        # Fallback to linear
        return self.v_min + (soc / 100.0) * (self.v_max - self.v_min)


def get_converter(preferences: Dict[str, Any]) -> VoltageSocConverter:
    """
    Factory function to create converter from preferences.

    Usage:
        prefs = get_user_preferences()
        converter = get_converter(prefs)
        soc = converter.voltage_to_soc(52.3)
    """
    return VoltageSocConverter(preferences)
