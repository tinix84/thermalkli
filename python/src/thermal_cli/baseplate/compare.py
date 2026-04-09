"""Layout comparator for baseplate thermal analysis.

Ported from thermal-layout-analyzer/src/thermal_analyzer/app/comparator.py.
Compares N alternative device placements by T_j_max, T_j_mean, T_j_spread.
"""

from __future__ import annotations

from dataclasses import dataclass

from thermal_cli.baseplate.fdm_solver import solve_fdm
from thermal_cli.baseplate.types import BaseplateConfig, BaseplateResult


@dataclass
class ComparisonEntry:
    """Result of a single layout in a comparison."""

    name: str
    result: BaseplateResult
    t_j_max: float
    t_j_mean: float
    t_j_spread: float


def compare_layouts(
    configs: dict[str, BaseplateConfig],
) -> list[ComparisonEntry]:
    """Compare multiple baseplate layouts, ranked by T_j_max (ascending).

    Parameters
    ----------
    configs : dict[str, BaseplateConfig]
        Named configurations to compare.

    Returns
    -------
    list[ComparisonEntry]
        Results sorted by T_j_max (best first).
    """
    entries = []
    for name, cfg in configs.items():
        result = solve_fdm(cfg)
        entries.append(
            ComparisonEntry(
                name=name,
                result=result,
                t_j_max=result.t_j_max,
                t_j_mean=result.t_j_mean,
                t_j_spread=result.t_j_spread,
            )
        )
    return sorted(entries, key=lambda e: e.t_j_max)
