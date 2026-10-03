"""Tests for thermal_cli.baseplate — FDM solver and comparator.

Absorbed from thermal-layout-analyzer test cases + new physics validation.
"""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.baseplate import (
    BaseplateConfig,
    Device,
    compare_layouts,
    solve_fdm,
)

# --- FDM solver basics ---


def _make_config(**kwargs) -> BaseplateConfig:
    defaults = dict(
        lx=0.1,
        ly=0.08,
        thickness=0.003,
        conductivity=385.0,
        r_sa=0.2,
        t_ambient=300.0,
        nx=21,
        ny=17,
    )
    defaults.update(kwargs)
    return BaseplateConfig(**defaults)


def test_no_sources_uniform() -> None:
    """With no heat sources, temperature field should be uniform at T_ambient."""
    cfg = _make_config(devices=[])
    result = solve_fdm(cfg)
    assert result.t_max == pytest.approx(300.0, abs=0.01)
    assert result.t_mean == pytest.approx(300.0, abs=0.01)


def test_single_source_above_ambient() -> None:
    """Single source: max temperature must exceed ambient."""
    dev = Device(name="Q1", x=0.05, y=0.04, width=0.015, height=0.02, power=50.0)
    cfg = _make_config(devices=[dev])
    result = solve_fdm(cfg)
    assert result.t_max > 300.0
    assert result.t_j_max > 300.0


def test_single_source_symmetry() -> None:
    """Centered source on symmetric domain: max temp at center."""
    dev = Device(name="Q1", x=0.05, y=0.04, width=0.01, height=0.01, power=50.0)
    cfg = _make_config(devices=[dev])
    result = solve_fdm(cfg)
    t = result.t_field
    ny, nx = t.shape
    # Max should be near center
    j_max, i_max = np.unravel_index(np.argmax(t), t.shape)
    assert abs(i_max - nx // 2) <= 2
    assert abs(j_max - ny // 2) <= 2


def test_higher_power_higher_temp() -> None:
    """Doubling power should increase temperature."""
    dev1 = Device(name="Q1", x=0.05, y=0.04, width=0.015, height=0.02, power=25.0)
    dev2 = Device(name="Q1", x=0.05, y=0.04, width=0.015, height=0.02, power=50.0)
    r1 = solve_fdm(_make_config(devices=[dev1]))
    r2 = solve_fdm(_make_config(devices=[dev2]))
    assert r2.t_max > r1.t_max


def test_multiple_sources() -> None:
    """Two sources: both device results populated."""
    devs = [
        Device(name="Q1", x=0.03, y=0.04, width=0.01, height=0.01, power=30.0),
        Device(name="Q2", x=0.07, y=0.04, width=0.01, height=0.01, power=30.0),
    ]
    cfg = _make_config(devices=devs)
    result = solve_fdm(cfg)
    assert len(result.devices) == 2
    assert all(d.t_junction > 300.0 for d in result.devices)


def test_junction_includes_rjc() -> None:
    """Junction temp includes R_jc thermal rise."""
    dev = Device(
        name="Q1",
        x=0.05,
        y=0.04,
        width=0.015,
        height=0.02,
        power=50.0,
        r_jc=1.0,
        r_interface=0.5,
    )
    cfg = _make_config(devices=[dev])
    result = solve_fdm(cfg)
    dr = result.devices[0]
    assert dr.t_junction > dr.t_case > dr.t_base
    assert dr.t_junction == pytest.approx(dr.t_base + 50.0 * 0.5 + 50.0 * 1.0, rel=1e-10)


def test_energy_balance() -> None:
    """Conservative assembly diagnostics close the positive-power heat balance."""
    dev = Device(name="Q1", x=0.05, y=0.04, width=0.015, height=0.02, power=50.0)
    result = solve_fdm(_make_config(devices=[dev], nx=41, ny=33))
    assert result.heat_input_W == pytest.approx(50.0, abs=1e-12)
    assert result.heat_rejected_W == pytest.approx(50.0, rel=1e-12)
    assert result.heat_balance_relative_error <= 1e-6
    assert result.linear_residual_norm <= 1e-8


def test_result_grid_shapes() -> None:
    cfg = _make_config(nx=21, ny=17, devices=[])
    result = solve_fdm(cfg)
    assert result.t_field.shape == (17, 21)
    assert len(result.x_grid) == 21
    assert len(result.y_grid) == 17


# --- Comparator ---


def test_compare_two_layouts() -> None:
    """Compare two device placements: centered vs edge."""
    dev_center = Device(name="Q1", x=0.05, y=0.04, width=0.01, height=0.01, power=50.0, r_jc=0.5)
    dev_edge = Device(name="Q1", x=0.01, y=0.01, width=0.01, height=0.01, power=50.0, r_jc=0.5)

    configs = {
        "centered": _make_config(devices=[dev_center]),
        "edge": _make_config(devices=[dev_edge]),
    }
    ranked = compare_layouts(configs)
    assert len(ranked) == 2
    # Centered should have lower T_j_max (better spreading)
    assert ranked[0].name == "centered"
    assert ranked[0].t_j_max < ranked[1].t_j_max


def test_compare_returns_sorted() -> None:
    dev = Device(name="Q1", x=0.05, y=0.04, width=0.01, height=0.01, power=50.0)
    configs = {
        "high_rsa": _make_config(devices=[dev], r_sa=0.5),
        "low_rsa": _make_config(devices=[dev], r_sa=0.1),
    }
    ranked = compare_layouts(configs)
    assert ranked[0].t_j_max <= ranked[1].t_j_max


def _assert_solver_diagnostics(result, expected_input_W: float) -> None:
    assert result.heat_input_W == pytest.approx(expected_input_W, rel=1e-12, abs=1e-14)
    assert result.linear_residual_norm <= 1e-8
    if expected_input_W > 0.0:
        assert result.heat_balance_relative_error <= 1e-6
        assert result.heat_rejected_W == pytest.approx(expected_input_W, rel=1e-6)
    else:
        assert result.heat_rejected_W == pytest.approx(0.0, abs=1e-12)
        assert result.heat_balance_relative_error == pytest.approx(0.0, abs=1e-12)


def test_uniform_full_plate_heating_matches_total_rsa() -> None:
    power_W = 64.0
    r_sa = 0.37
    config = _make_config(
        lx=0.1,
        ly=0.08,
        r_sa=r_sa,
        nx=12,
        ny=10,
        devices=[
            Device(
                name="uniform",
                x=0.05,
                y=0.04,
                width=0.1,
                height=0.08,
                power=power_W,
            )
        ],
    )

    result = solve_fdm(config)
    expected_temperature = config.t_ambient + power_W * r_sa

    assert np.allclose(result.t_field, expected_temperature, rtol=0.0, atol=1e-10)
    assert result.t_max == pytest.approx(expected_temperature, abs=1e-10)
    assert result.devices[0].t_base == pytest.approx(expected_temperature, abs=1e-10)
    _assert_solver_diagnostics(result, power_W)


def test_zero_power_equilibrium_and_diagnostics() -> None:
    result = solve_fdm(
        _make_config(
            devices=[Device(name="zero", x=0.05, y=0.04, width=0.02, height=0.02, power=0.0)]
        )
    )

    assert np.allclose(result.t_field, 300.0, rtol=0.0, atol=1e-12)
    assert result.t_max == pytest.approx(300.0, abs=1e-12)
    _assert_solver_diagnostics(result, 0.0)


def test_subcell_edge_and_overlapping_sources_conserve_power_additively() -> None:
    devices = [
        Device(name="edge", x=0.003, y=0.003, width=0.006, height=0.006, power=7.25),
        Device(name="overlap", x=0.006, y=0.005, width=0.008, height=0.010, power=11.5),
        Device(name="subcell", x=0.007, y=0.008, width=0.001, height=0.001, power=2.25),
    ]
    result = solve_fdm(_make_config(nx=7, ny=5, devices=devices))

    assert result.heat_input_W == pytest.approx(sum(device.power for device in devices), abs=1e-12)
    assert result.heat_rejected_W == pytest.approx(21.0, rel=1e-12)
    _assert_solver_diagnostics(result, 21.0)


def test_out_of_bounds_footprint_is_rejected_without_clipping() -> None:
    device = Device(name="outside", x=0.003, y=0.02, width=0.008, height=0.01, power=10.0)

    with pytest.raises(ValueError, match=r"fully inside.*not clipped or renormalized"):
        solve_fdm(_make_config(devices=[device]))


@pytest.mark.parametrize("width", [0.0002, 0.0001])
def test_tiny_in_bounds_square_source_conserves_power(width: float) -> None:
    config = _make_config(
        nx=7,
        ny=5,
        devices=[
            Device(
                name="tiny-square",
                x=0.07,
                y=0.03,
                width=width,
                height=width,
                power=1.0,
            )
        ],
    )

    result = solve_fdm(config)

    assert result.heat_input_W == pytest.approx(1.0, abs=1e-12)
    assert result.heat_rejected_W == pytest.approx(1.0, rel=1e-6)
    assert result.heat_balance_relative_error <= 1e-6
    assert result.linear_residual_norm <= 1e-8


def test_tiny_out_of_bounds_footprint_is_still_rejected() -> None:
    device = Device(
        name="tiny-outside",
        x=0.09995,
        y=0.03,
        width=0.0002,
        height=0.0002,
        power=1.0,
    )

    with pytest.raises(ValueError, match=r"fully inside.*not clipped or renormalized"):
        solve_fdm(_make_config(nx=7, ny=5, devices=[device]))


def test_device_base_temperature_is_area_weighted_and_grid_max_is_separate() -> None:
    config = _make_config(
        nx=13,
        ny=11,
        devices=[
            Device(
                name="offset",
                x=0.033,
                y=0.030,
                width=0.027,
                height=0.019,
                power=42.0,
            )
        ],
    )
    result = solve_fdm(config)

    x_bounds = np.concatenate(([0.0], 0.5 * (result.x_grid[:-1] + result.x_grid[1:]), [config.lx]))
    y_bounds = np.concatenate(([0.0], 0.5 * (result.y_grid[:-1] + result.y_grid[1:]), [config.ly]))
    device = config.devices[0]
    x_min, x_max = device.x - device.width / 2.0, device.x + device.width / 2.0
    y_min, y_max = device.y - device.height / 2.0, device.y + device.height / 2.0
    overlap_x = np.maximum(0.0, np.minimum(x_bounds[1:], x_max) - np.maximum(x_bounds[:-1], x_min))
    overlap_y = np.maximum(0.0, np.minimum(y_bounds[1:], y_max) - np.maximum(y_bounds[:-1], y_min))
    expected_base_temperature = float(
        np.sum(result.t_field * np.outer(overlap_y, overlap_x)) / (device.width * device.height)
    )

    assert result.devices[0].t_base == pytest.approx(expected_base_temperature, abs=1e-12)
    assert result.t_max == pytest.approx(float(np.max(result.t_field)), abs=1e-12)
    assert result.t_max >= result.devices[0].t_base


def test_nonuniform_device_temperature_converges_under_three_refinements() -> None:
    devices = [
        Device(
            name="Q1",
            x=0.03,
            y=0.04,
            width=0.015,
            height=0.02,
            power=50.0,
            r_jc=0.4,
            r_interface=0.05,
        ),
        Device(
            name="Q2",
            x=0.074,
            y=0.025,
            width=0.012,
            height=0.014,
            power=22.0,
            r_jc=0.6,
            r_interface=0.08,
        ),
    ]
    resolutions = [(17, 13), (33, 25), (65, 49), (129, 97)]
    results = [solve_fdm(_make_config(nx=nx, ny=ny, devices=devices)) for nx, ny in resolutions]

    for result in results:
        _assert_solver_diagnostics(result, 72.0)
    final_changes = [
        abs(fine.t_junction - coarse.t_junction)
        for coarse, fine in zip(results[-2].devices, results[-1].devices, strict=True)
    ]
    assert max(final_changes) <= 0.2


def test_two_by_two_control_volumes_match_independent_edge_network() -> None:
    config = _make_config(
        lx=1.0,
        ly=1.0,
        thickness=1.0,
        conductivity=1.0,
        r_sa=1.0,
        t_ambient=0.0,
        nx=2,
        ny=2,
        devices=[
            Device(
                name="left-half",
                x=0.25,
                y=0.5,
                width=0.5,
                height=1.0,
                power=1.0,
            )
        ],
    )

    result = solve_fdm(config)

    # Each half-width control volume has sink conductance 0.25 W/K. The
    # shared x-face conductance is 0.5 W/K in each half-height row. Symmetry
    # in y reduces the independent four-volume network to:
    # 0.75*T_left - 0.5*T_right = 0.5 W; -0.5*T_left + 0.75*T_right = 0.
    assert np.allclose(result.t_field, [[1.2, 0.8], [1.2, 0.8]], rtol=0.0, atol=1e-12)
    _assert_solver_diagnostics(result, 1.0)
