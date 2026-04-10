"""Heatsink models: extruded-fin channel, generic, and factory."""

from thermal_cli.heatsinks.channel_flow import (
    FinRthResult,
    HydraulicResult,
    fin_thermal_resistance,
    hydraulic_operating_point,
)
from thermal_cli.heatsinks.extruded_fin import ExtrudedFin
from thermal_cli.heatsinks.factory import heatsink_factory
from thermal_cli.heatsinks.natural_conv import NaturalConvHsResult, natural_conv_hs

__all__ = [
    "ExtrudedFin",
    "FinRthResult",
    "HydraulicResult",
    "NaturalConvHsResult",
    "fin_thermal_resistance",
    "heatsink_factory",
    "hydraulic_operating_point",
    "natural_conv_hs",
]
