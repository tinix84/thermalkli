"""Fluid property registry — maps reference strings to property objects.

Ported from ``mfiles/Thermal/Model/fluidPropertyFactory.m``.
"""

from __future__ import annotations

from thermal_cli.fluids.gas import GasProperty
from thermal_cli.fluids.liquid import LiquidProperty

FluidProperty = GasProperty | LiquidProperty

#: Registry of known fluid reference strings → constructors.
_REGISTRY: dict[str, type[GasProperty] | type[LiquidProperty]] = {
    "airDry": GasProperty,
    "H2OGly50": LiquidProperty,
    "SAE30": LiquidProperty,
}


def fluid_registry(fluid_ref: str) -> FluidProperty:
    """Create a fluid property object by reference string.

    Supported fluids: ``'airDry'``, ``'H2OGly50'``, ``'SAE30'``.

    Raises
    ------
    ValueError
        If ``fluid_ref`` is not in the registry.
    """
    cls = _REGISTRY.get(fluid_ref)
    if cls is None:
        known = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown fluid '{fluid_ref}'. Known: {known}")
    return cls(fluid_ref=fluid_ref)
