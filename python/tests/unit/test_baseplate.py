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
    """Total heat in ≈ total heat out through vertical sink coupling."""
    dev = Device(name="Q1", x=0.05, y=0.04, width=0.015, height=0.02, power=50.0)
    cfg = _make_config(devices=[dev], nx=41, ny=33)
    result = solve_fdm(cfg)
    t = result.t_field
    dx = cfg.lx / (cfg.nx - 1)
    dy = cfg.ly / (cfg.ny - 1)
    a_base = cfg.lx * cfg.ly
    r_vert = cfg.r_sa / a_base
    # Heat out = integral of (T - T_inf) / R''_vert over area
    q_out = np.sum(t - cfg.t_ambient) * dx * dy / r_vert
    assert q_out == pytest.approx(50.0, rel=0.5)  # coarse grid: ~40% discretization error


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
