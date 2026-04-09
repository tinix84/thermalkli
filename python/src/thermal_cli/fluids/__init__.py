"""Fluid property models (gas and liquid) with temperature-dependent interpolation."""

from thermal_cli.fluids.gas import GasProperty
from thermal_cli.fluids.liquid import LiquidProperty
from thermal_cli.fluids.registry import fluid_registry

__all__ = ["GasProperty", "LiquidProperty", "fluid_registry"]
