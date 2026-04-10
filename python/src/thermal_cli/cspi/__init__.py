"""CSPI (Cooling System Performance Index) module — Drofenik & Kolar CIPS06."""

from thermal_cli.cspi.formulas import (
    FluidProps,
    air_properties,
    channel_rth,
    cspi_calc,
    fan_scaling_fit,
)

__all__ = ["FluidProps", "air_properties", "channel_rth", "cspi_calc", "fan_scaling_fit"]
