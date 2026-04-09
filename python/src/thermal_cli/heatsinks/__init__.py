"""Heatsink models: extruded-fin channel, generic, and factory."""

from thermal_cli.heatsinks.extruded_fin import ExtrudedFin
from thermal_cli.heatsinks.factory import heatsink_factory

__all__ = ["ExtrudedFin", "heatsink_factory"]
