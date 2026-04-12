"""Extruded-fin geometry grid sweep.

Wraps ``ExtrudedFin.thermal_resistance`` in a scalar adapter and feeds
it through ``run_sweep`` to find the geometry that minimises total
thermal resistance.

Ported from ``mfiles/Thermal/Optimizer/extrudedFinHeatsinkCalculations.m``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from thermal_cli.fluids import fluid_registry
from thermal_cli.heatsinks.extruded_fin import ExtrudedFin
from thermal_cli.sweep.engine import SweepResult, run_sweep


@dataclass
class FinGeometrySweepConfig:
    """Configuration for ``optimize_fin_geometry``.

    ``axes`` entries can be any parameter accepted by
    ``evaluate_extruded_fin_rth``; ``fixed`` supplies the rest.
    """

    axes: Mapping[str, Sequence[float]]
    fixed: Mapping[str, Any] = field(default_factory=dict)


def evaluate_extruded_fin_rth(
    *,
    thick_heatsink: float,
    thick_wall: float,
    width_channel: float,
    k_sink: float,
    rho_sink: float,
    l_heated: float,
    a_hot: float,
    flowrate_lpm: float,
    fluid_ref: str,
    t_fluid_in: float,
    num_channel: int,
    num_heated_sides: int = 1,
) -> float:
    """Build an ``ExtrudedFin`` and return total thermal resistance [K/W].

    Parameters mirror ``ExtrudedFin.__init__`` plus the runtime inputs
    ``thermal_resistance`` needs. Returns ``r_th_total`` as a scalar,
    which is what ``run_sweep`` expects.

    ``flowrate_lpm`` is litres per minute (matches the Octave CLI); the
    adapter converts to m^3/s internally.
    """
    hs = ExtrudedFin(
        num_channel=int(num_channel),
        thick_heatsink=thick_heatsink,
        thick_wall=thick_wall,
        width_channel=width_channel,
        k_sink=k_sink,
        rho_sink=rho_sink,
    )
    fluid = fluid_registry(fluid_ref)
    flowrate_m3s = flowrate_lpm / 1000.0 / 60.0
    result = hs.thermal_resistance(
        fluid=fluid,
        flowrate=flowrate_m3s,
        l_heated=l_heated,
        a_hot=a_hot,
        num_heated_sides=num_heated_sides,
    )
    return float(result["r_th_total"])


def optimize_fin_geometry(cfg: FinGeometrySweepConfig) -> SweepResult:
    """Run a grid sweep over fin geometry and return a SweepResult."""
    return run_sweep(
        func=evaluate_extruded_fin_rth,
        axes=cfg.axes,
        fixed=dict(cfg.fixed),
    )
