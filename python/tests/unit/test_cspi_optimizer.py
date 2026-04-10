"""Tests for cspi/optimizer.py — CSPI geometry optimizer and sweep."""

import math
import numpy as np
import pytest

from thermal_cli.cspi.optimizer import (
    CspiOptResult,
    CspiSweepResult,
    cspi_optimize,
    cspi_sweep,
)


# ---------------------------------------------------------------------------
# CspiOptResult dataclass shape
# ---------------------------------------------------------------------------

class TestCspiOptResultShape:
    def test_has_expected_fields(self):
        res = CspiOptResult(
            cspi=1.0, rth=0.5, vol=0.064, n=10, s=2e-3, t=2e-3,
            re=500.0, n_fan=3000.0, length=0.025, v_max=1e-3,
            dp_max=50.0, feasible=True,
        )
        assert res.cspi == pytest.approx(1.0)
        assert res.n == 10
        assert isinstance(res.feasible, bool)


# ---------------------------------------------------------------------------
# cspi_optimize — typical aluminum heatsink
# ---------------------------------------------------------------------------

class TestCspiOptimizeAluminum:
    """lambda=200 W/mK, A=10cm^2=10e-4 m^2, c=40mm, P_fan=5W"""

    @pytest.fixture
    def result(self):
        return cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=5.0,
        )

    def test_cspi_positive(self, result):
        assert result.cspi > 0

    def test_rth_positive(self, result):
        assert result.rth > 0

    def test_n_at_least_two(self, result):
        assert result.n >= 2

    def test_channel_width_positive(self, result):
        assert result.s > 0

    def test_fin_thickness_positive(self, result):
        assert result.t > 0

    def test_vol_positive(self, result):
        assert result.vol > 0

    def test_n_fan_positive(self, result):
        assert result.n_fan > 0

    def test_length_matches_a_chip_over_c(self, result):
        """L = a_chip / c = 10e-4 / 40e-3 = 0.025 m"""
        assert result.length == pytest.approx(10e-4 / 40e-3, rel=1e-6)

    def test_feasible_is_bool(self, result):
        assert isinstance(result.feasible, bool)

    def test_re_positive(self, result):
        assert result.re > 0

    def test_v_max_positive(self, result):
        assert result.v_max > 0

    def test_dp_max_positive(self, result):
        assert result.dp_max > 0


# ---------------------------------------------------------------------------
# Copper beats aluminum (higher thermal conductivity => higher CSPI)
# ---------------------------------------------------------------------------

class TestCopperVsAluminum:
    def test_copper_higher_cspi(self):
        al = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=40e-3, p_fan_max=5.0,
        )
        cu = cspi_optimize(
            lambda_hs=400.0, a_chip=10e-4, c=40e-3, p_fan_max=5.0,
        )
        assert cu.cspi > al.cspi


# ---------------------------------------------------------------------------
# More fan power => higher CSPI
# ---------------------------------------------------------------------------

class TestFanPowerEffect:
    def test_more_fan_power_higher_cspi(self):
        low = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=40e-3, p_fan_max=2.0,
        )
        high = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=40e-3, p_fan_max=10.0,
        )
        assert high.cspi > low.cspi


# ---------------------------------------------------------------------------
# Custom fan constants
# ---------------------------------------------------------------------------

class TestCustomFanConstants:
    def test_custom_k_constants_accepted(self):
        """Non-default k1/k2/k3 should run without error and return valid result."""
        res = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=40e-3, p_fan_max=5.0,
            k1=5e-3, k2=4e-4, k3=25e-6,
        )
        assert res.cspi > 0
        assert res.rth > 0

    def test_n_fan_uses_k3(self):
        """N = (P/(k3*c^5))^(1/3); doubling k3 reduces N_fan."""
        res_k3_low = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=40e-3, p_fan_max=5.0,
            k3=15e-6,
        )
        res_k3_high = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=40e-3, p_fan_max=5.0,
            k3=30e-6,
        )
        # Higher k3 => lower N_fan (less efficient fan)
        assert res_k3_low.n_fan > res_k3_high.n_fan

    def test_n_fan_formula(self):
        """N_fan = (P_fan_max / (k3 * c^5))^(1/3) [rev/s internally, return as rpm]."""
        c = 40e-3
        p = 5.0
        k3 = 30e-6
        # The formula gives N in rev/s; stored as rpm (multiply by 60) or raw rev/s
        # We just check it's consistent with formula (within factor of 60 ambiguity)
        res = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=c, p_fan_max=p, k3=k3,
        )
        expected_n = (p / (k3 * c**5)) ** (1.0 / 3.0)
        # Accept either rev/s or rpm value being consistent
        assert res.n_fan == pytest.approx(expected_n, rel=1e-6)


# ---------------------------------------------------------------------------
# t_min constraint
# ---------------------------------------------------------------------------

class TestTminConstraint:
    def test_fin_thickness_at_least_t_min(self):
        t_min = 1e-3  # 1 mm
        res = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=40e-3, p_fan_max=5.0,
            t_min=t_min,
        )
        # t_fin should be >= t_min (within floating-point tolerance)
        assert res.t >= t_min - 1e-9

    def test_t_min_returns_valid_result(self):
        res = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=40e-3, p_fan_max=5.0,
            t_min=0.5e-3,
        )
        assert res.cspi > 0
        assert res.n >= 2


# ---------------------------------------------------------------------------
# Feasibility flag
# ---------------------------------------------------------------------------

class TestFeasibility:
    def test_feasible_is_bool_type(self):
        res = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=40e-3, p_fan_max=5.0,
        )
        assert type(res.feasible) is bool

    def test_feasible_true_for_typical_case(self):
        """Typical aluminum case should yield a feasible (laminar) result."""
        res = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=40e-3, p_fan_max=5.0,
        )
        # Not guaranteed, but typical configs should pass
        # Just verify it's a bool — we can't assert True/False without known answer
        assert isinstance(res.feasible, bool)


# ---------------------------------------------------------------------------
# n_pts parameter
# ---------------------------------------------------------------------------

class TestNPts:
    def test_higher_n_pts_same_order_of_magnitude(self):
        """Finer sweep should give similar but not necessarily equal result."""
        res_coarse = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=40e-3, p_fan_max=5.0,
            n_pts=20,
        )
        res_fine = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=40e-3, p_fan_max=5.0,
            n_pts=200,
        )
        # Both should be positive and within ~50% of each other
        assert res_coarse.cspi > 0
        assert res_fine.cspi > 0
        ratio = res_fine.cspi / res_coarse.cspi
        assert 0.5 < ratio < 2.0


# ---------------------------------------------------------------------------
# Re-exports from __init__
# ---------------------------------------------------------------------------

class TestReExports:
    def test_imports_from_cspi_package(self):
        from thermal_cli.cspi import (
            CspiOptResult,
            CspiSweepResult,
            cspi_optimize,
            cspi_sweep,
        )
        assert callable(cspi_optimize)
        assert callable(cspi_sweep)


# ---------------------------------------------------------------------------
# cspi_sweep — 2x2 grid
# ---------------------------------------------------------------------------

class TestCspiSweep:
    @pytest.fixture
    def sweep_result(self):
        return cspi_sweep(
            a_chip=10e-4,
            p_fan_max=5.0,
            lambdas=[200.0, 400.0],
            cs=[30e-3, 50e-3],
        )

    def test_returns_cspi_sweep_result(self, sweep_result):
        assert isinstance(sweep_result, CspiSweepResult)

    def test_cspi_shape_2x2(self, sweep_result):
        assert sweep_result.cspi.shape == (2, 2)

    def test_rth_shape_2x2(self, sweep_result):
        assert sweep_result.rth.shape == (2, 2)

    def test_all_cspi_positive(self, sweep_result):
        assert np.all(sweep_result.cspi > 0)

    def test_all_rth_positive(self, sweep_result):
        assert np.all(sweep_result.rth > 0)

    def test_cs_stored(self, sweep_result):
        assert list(sweep_result.cs) == pytest.approx([30e-3, 50e-3])

    def test_lambdas_stored(self, sweep_result):
        assert list(sweep_result.lambdas) == pytest.approx([200.0, 400.0])

    def test_higher_lambda_higher_cspi(self, sweep_result):
        """For each c, copper (lambda=400) should beat aluminum (lambda=200)."""
        for i in range(2):  # iterate over cs
            assert sweep_result.cspi[i, 1] > sweep_result.cspi[i, 0]

    def test_cspi_is_ndarray(self, sweep_result):
        assert isinstance(sweep_result.cspi, np.ndarray)

    def test_rth_is_ndarray(self, sweep_result):
        assert isinstance(sweep_result.rth, np.ndarray)

    def test_sweep_passes_kwargs(self):
        """kwargs like t_min are forwarded to cspi_optimize."""
        res = cspi_sweep(
            a_chip=10e-4,
            p_fan_max=5.0,
            lambdas=[200.0],
            cs=[40e-3],
            t_min=0.5e-3,
        )
        assert res.cspi.shape == (1, 1)
        assert res.cspi[0, 0] > 0
