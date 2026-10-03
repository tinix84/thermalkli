"""Waffler §4.4.2 literal-correlation and B03 source fixtures."""

from __future__ import annotations

import math

import pytest

from thermal_cli.benchmarks.waffler import WAFFLER_B03
from thermal_cli.formula.waffler import (
    waffler_heat_transfer_coefficient,
    waffler_laminar_nusselt,
    waffler_nusselt,
    waffler_turbulent_nusselt,
)


@pytest.mark.parametrize(
    ("reynolds", "expected"),
    ((2300.0, 17.398181405846), (5568.0, 39.988090323818), (10000.0, 70.624098991031)),
)
def test_printed_equations_4_146_to_4_150_fixture(reynolds: float, expected: float) -> None:
    """Literal formula fixture, using the printed example's Pr and d/L."""
    assert math.isclose(
        waffler_nusselt(reynolds, 1.98, 0.002, 0.010), expected, rel_tol=1e-12
    )


def test_reported_nu_28_remains_distinct_from_literal_printed_equation() -> None:
    """Printed p.272 reports 28; its report is not substituted into eqs.4.146–4.150."""
    nu_printed = waffler_nusselt(5568.0, 1.98, 0.002, 0.010)
    h_printed = waffler_heat_transfer_coefficient(5568.0, 1.98, 0.002, 0.010, 0.674)
    h_from_reported_nu = 28.0 * 0.674 / 0.002
    assert math.isclose(nu_printed, 39.988090323818, rel_tol=1e-12)
    assert math.isclose(h_printed, 13_475.986439126686, rel_tol=1e-12)
    assert math.isclose(h_from_reported_nu, 9_436.0, rel_tol=1e-12)
    assert not math.isclose(nu_printed, 28.0, rel_tol=1e-3)


def test_laminar_and_turbulent_functions_are_the_transition_endpoints() -> None:
    pr, diameter, length = 1.98, 0.002, 0.010
    assert waffler_nusselt(2300.0, pr, diameter, length) == waffler_laminar_nusselt(
        2300.0, pr, diameter, length
    )
    assert waffler_nusselt(10000.0, pr, diameter, length) == waffler_turbulent_nusselt(
        10000.0, pr, diameter, length
    )


def test_b03_source_geometry_power_and_eq_4_154_estimate() -> None:
    case = WAFFLER_B03
    assert case.channel_pitch_m == 0.006
    assert case.plate_height_m == 0.004
    assert case.channel_diameter_m == 0.002
    assert case.extrusion_depth_m == 0.010
    assert case.top_heat_flux_W_m2 == 40_000.0
    assert case.channel_center_xy_m == (0.003, 0.002)
    assert case.channel_wall_temperature_K == 363.15
    assert case.applied_power_W == 2.4
    assert math.isclose(case.effective_metal_path_m, 0.001599284449, rel_tol=1e-9)
    assert math.isclose(case.analytic_metal_temperature_rise_K, 0.399821112314, rel_tol=1e-9)
    assert len(case.top_sample_points_xy_m) == 3
    assert all(0.0 < x < case.channel_pitch_m and 0.0 < y < case.plate_height_m for x, y in case.top_sample_points_xy_m)


def test_positive_inputs_and_singular_friction_expression_are_checked() -> None:
    with pytest.raises(ValueError, match="reynolds_number"):
        waffler_nusselt(0.0, 1.98, 0.002, 0.010)
    with pytest.raises(ValueError, match="hydraulic_diameter_m"):
        waffler_nusselt(5568.0, 1.98, 0.0, 0.010)