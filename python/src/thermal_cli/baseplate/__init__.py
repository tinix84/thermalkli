"""2D multi-source baseplate thermal analysis (FDM + analytical backends)."""

from thermal_cli.baseplate.compare import compare_layouts
from thermal_cli.baseplate.fdm_solver import solve_fdm
from thermal_cli.baseplate.types import BaseplateConfig, BaseplateResult, Device

__all__ = [
    "BaseplateConfig",
    "BaseplateResult",
    "Device",
    "compare_layouts",
    "solve_fdm",
]
