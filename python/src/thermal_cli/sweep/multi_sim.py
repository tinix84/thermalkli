"""Baseplate multi-scenario runner.

Iterates a list of ``MultiSimScenario`` specs, runs each through the
M6 FDM baseplate solver, and returns a ``MultiSimResult`` with per-
scenario peak temperatures and per-device junction temperatures.

Ported from ``mfiles/SoftwareTermico/Simulazione_multipla/``. The
Octave source repositioning loop is out of scope for M9.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from thermal_cli.baseplate.fdm_solver import solve_fdm
from thermal_cli.baseplate.types import BaseplateConfig, Device


@dataclass
class MultiSimScenario:
    """One scenario in a multi-sim run.

    ``devices`` is a list of plain dicts with Device fields — this keeps
    YAML deserialisation trivial.
    """

    name: str
    lx: float
    ly: float
    thickness: float
    conductivity: float
    r_sa: float
    t_ambient: float
    devices: list[dict[str, Any]]
    nx: int = 41
    ny: int = 41

    def to_config(self) -> BaseplateConfig:
        devs = [Device(**d) for d in self.devices]
        return BaseplateConfig(
            lx=self.lx,
            ly=self.ly,
            thickness=self.thickness,
            conductivity=self.conductivity,
            r_sa=self.r_sa,
            t_ambient=self.t_ambient,
            devices=devs,
            nx=self.nx,
            ny=self.ny,
        )


@dataclass
class MultiSimRow:
    """Summary of one scenario's baseplate solve."""

    name: str
    t_ambient: float
    t_max: float          # [K] peak baseplate temperature
    t_mean: float         # [K] mean baseplate temperature
    t_j_max: float        # [K] peak junction temperature
    t_j_per_device: dict[str, float] = field(default_factory=dict)


@dataclass
class MultiSimResult:
    rows: list[MultiSimRow]


def run_multi_sim(scenarios: list[MultiSimScenario]) -> MultiSimResult:
    """Run baseplate FDM solver on each scenario."""
    if not scenarios:
        raise ValueError("run_multi_sim needs at least one scenario")

    rows: list[MultiSimRow] = []
    for sc in scenarios:
        cfg = sc.to_config()
        res = solve_fdm(cfg)
        rows.append(
            MultiSimRow(
                name=sc.name,
                t_ambient=sc.t_ambient,
                t_max=res.t_max,
                t_mean=res.t_mean,
                t_j_max=res.t_j_max,
                t_j_per_device={d.name: d.t_junction for d in res.devices},
            )
        )
    return MultiSimResult(rows=rows)


def load_scenarios_from_dict(data: dict[str, Any]) -> list[MultiSimScenario]:
    """Parse a YAML-loaded dict with a top-level ``scenarios`` list."""
    if "scenarios" not in data:
        raise ValueError("multi-sim config requires a 'scenarios' key")
    return [MultiSimScenario(**entry) for entry in data["scenarios"]]
