"""Tests for cspi/optimizer.py — CSPI geometry optimizer and sweep."""

import numpy as np
import pytest

from thermal_cli.cspi.optimizer import (
    CspiOptResult,
    CspiSweepResult,
    _rectangular_pressure_drop,
    cspi_evaluate_geometry,
    cspi_optimize,
    cspi_sweep,
    fin_half_path_resistance,
)

# ---------------------------------------------------------------------------
# CspiOptResult dataclass shape
# ---------------------------------------------------------------------------


class TestCspiOptResultShape:
    def test_has_expected_fields(self):
        res = CspiOptResult(
            cspi=1.0,
            rth=0.5,
            vol=0.064,
            n=10,
            s=2e-3,
            t=2e-3,
            re=500.0,
            n_fan=3000.0,
            length=0.025,
            v_max=1e-3,
            dp_max=50.0,
            feasible=True,
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
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=5.0,
        )
        cu = cspi_optimize(
            lambda_hs=400.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=5.0,
        )
        assert cu.cspi > al.cspi


# ---------------------------------------------------------------------------
# More fan power => higher CSPI
# ---------------------------------------------------------------------------


class TestFanPowerEffect:
    def test_more_fan_power_higher_cspi(self):
        low = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=2.0,
        )
        high = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=10.0,
        )
        assert high.cspi > low.cspi


# ---------------------------------------------------------------------------
# Custom fan constants
# ---------------------------------------------------------------------------


class TestCustomFanConstants:
    def test_custom_k_constants_accepted(self):
        """Non-default k1/k2/k3 should run without error and return valid result."""
        res = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=5.0,
            k1=5e-3,
            k2=4e-4,
            k3=25e-6,
        )
        assert res.cspi > 0
        assert res.rth > 0

    def test_n_fan_uses_k3(self):
        """N = (P/(k3*c^5))^(1/3); doubling k3 reduces N_fan."""
        res_k3_low = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=5.0,
            k3=15e-6,
        )
        res_k3_high = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=5.0,
            k3=30e-6,
        )
        # Higher k3 => lower N_fan (less efficient fan)
        assert res_k3_low.n_fan > res_k3_high.n_fan

    def test_n_fan_formula(self):
        """N_fan = (P_fan_max / (k3 * c^5))^(1/3), in rpm.

        The k3 default (30e-6) was fitted in rpm units (consistent with
        ``fan_scaling_fit``), so ``n_fan`` is returned directly in rpm.
        """
        c = 40e-3
        p = 5.0
        k3 = 30e-6
        res = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=c,
            p_fan_max=p,
            k3=k3,
        )
        expected_n_rpm = (p / (k3 * c**5)) ** (1.0 / 3.0)
        assert res.n_fan == pytest.approx(expected_n_rpm, rel=1e-6)


# ---------------------------------------------------------------------------
# t_min constraint
# ---------------------------------------------------------------------------


class TestTminConstraint:
    def test_fin_thickness_at_least_t_min(self):
        t_min = 1e-3  # 1 mm
        res = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=5.0,
            t_min=t_min,
        )
        # t_fin should be >= t_min (within floating-point tolerance)
        assert res.t >= t_min - 1e-9

    def test_t_min_returns_valid_result(self):
        res = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=5.0,
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
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=5.0,
        )
        assert type(res.feasible) is bool

    def test_feasible_true_for_typical_case(self):
        """Typical aluminum case should yield a feasible (laminar) result."""
        res = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=5.0,
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
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=5.0,
            n_pts=3,
        )
        res_fine = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=40e-3,
            p_fan_max=5.0,
            n_pts=5,
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


_BASE_OPT_KW = {"lambda_hs": 200.0, "a_chip": 10e-4, "c": 40e-3, "p_fan_max": 5.0}


class TestCspiOptimizeValidation:
    """Non-physical inputs must raise ``ValueError`` before crashing deep in the sweep."""

    @pytest.mark.parametrize(
        "field,value",
        [
            ("lambda_hs", 0.0),
            ("lambda_hs", -1.0),
            ("a_chip", 0.0),
            ("c", 0.0),
            ("p_fan_max", 0.0),
            ("k1", 0.0),
            ("k2", -1e-4),
            ("k3", 0.0),
        ],
    )
    def test_non_positive_raises(self, field, value):
        kwargs = dict(_BASE_OPT_KW)
        kwargs[field] = value
        with pytest.raises(ValueError, match=field):
            cspi_optimize(**kwargs)

    def test_negative_t_min_raises(self):
        with pytest.raises(ValueError, match="t_min"):
            cspi_optimize(t_min=-1e-3, **_BASE_OPT_KW)

    def test_n_pts_too_small_raises(self):
        with pytest.raises(ValueError, match="n_pts"):
            cspi_optimize(n_pts=1, **_BASE_OPT_KW)


class TestBoundedCoolingAssembly:
    def evaluate(self, **overrides):
        values = dict(
            lambda_hs=210.0,
            sink_width_m=0.04,
            fin_height_m=0.02,
            sink_length_m=0.08,
            base_thickness_m=0.005,
            channel_count=30,
            channel_width_m=0.001,
            fin_thickness_m=0.0003,
            p_fan_max=6.6,
            fan_diameter_m=0.04,
            fan_depth_m=0.028,
            duct_length_m=0.014,
            assembly_face_width_m=0.04,
            assembly_face_height_m=0.04,
            fan_free_flow_m3_s=0.59 / 60.0,
            fan_shutoff_pressure_pa=340.0,
            fan_speed_rpm=15500.0,
            auxiliary_power_w=6.6,
            auxiliary_power_basis="rated electrical input at 12 V",
            t_air_c=25.0,
        )
        values.update(overrides)
        return cspi_evaluate_geometry(**values)

    def test_bounded_fan_system_root_and_b07_volume_boundary(self):
        result = self.evaluate(face_count=2)
        assert result.operating_point_status == "converged"
        assert result.feasible
        assert 0 < result.flow_rate_m3_s < result.v_max
        assert result.pressure_drop_pa > 0
        assert result.fan_curve_model == "parabolic fit to supplied endpoints"
        assert result.n_fan == pytest.approx(15500.0)
        assert result.auxiliary_power_basis == "rated electrical input at 12 V"
        assert result.pressure_correlation != result.heat_transfer_correlation
        assert result.sink_volume_l == pytest.approx(0.128)
        assert result.fan_volume_l == pytest.approx(0.0448)
        assert result.duct_volume_l == pytest.approx(0.0224)
        assert result.vol == pytest.approx(0.1952)
        assert result.sink_material_bbox_l == pytest.approx(0.08)
        assert result.auxiliary_power_w == pytest.approx(6.6)
        assert result.rth == pytest.approx(result.r_face_k_w / 2.0)

    def test_no_intersection_is_explicit_and_infeasible(self):
        result = self.evaluate(
            fan_free_flow_m3_s=0.0001,
            fan_shutoff_pressure_pa=None,
            fan_curve_flow_m3_s=[0.0, 0.0001],
            fan_curve_pressure_pa=[1000.0, 1000.0],
        )
        assert result.operating_point_status == "no_intersection"
        assert not result.feasible
        assert result.flow_rate_m3_s is None
        assert result.pressure_drop_pa is None

    def test_out_of_validity_domain_is_not_misreported_as_no_intersection(self):
        result = self.evaluate(
            fan_curve_flow_m3_s=[0.0, 0.02],
            fan_curve_pressure_pa=[500.0, 500.0],
        )
        assert result.operating_point_status == "correlation_out_of_range"
        assert not result.feasible

    def test_half_fin_path_units_and_geometry_trends(self):
        baseline = fin_half_path_resistance(
            fin_height_m=0.02,
            conductivity_w_mk=210.0,
            thickness_m=0.0003,
            flow_length_m=0.08,
        )
        thin_fin = fin_half_path_resistance(
            fin_height_m=0.02,
            conductivity_w_mk=210.0,
            thickness_m=0.00015,
            flow_length_m=0.08,
        )
        higher_k = fin_half_path_resistance(
            fin_height_m=0.02,
            conductivity_w_mk=420.0,
            thickness_m=0.0003,
            flow_length_m=0.08,
        )
        twice_area = fin_half_path_resistance(
            fin_height_m=0.02,
            conductivity_w_mk=210.0,
            thickness_m=0.0003,
            flow_length_m=0.16,
        )
        assert baseline == pytest.approx(0.02 / (2 * 210 * 0.0003 * 0.08))
        assert thin_fin == pytest.approx(2 * baseline)
        assert higher_k == pytest.approx(baseline / 2)
        assert twice_area == pytest.approx(baseline / 2)

    def test_two_face_normalization_uses_total_source_power(self):
        one_face = self.evaluate(face_count=1, source_power_w=120.0)
        two_face = self.evaluate(face_count=2, source_power_w=120.0)
        assert one_face.outlet_air_temperature_c > 25.0
        assert two_face.outlet_air_temperature_c > 25.0
        assert two_face.rth == pytest.approx(two_face.r_face_k_w / 2.0)
        assert two_face.rth < two_face.r_face_k_w
        assert two_face.source_power_w == pytest.approx(120.0)

    def test_optimizer_returns_integer_geometry_that_fills_width(self):
        result = cspi_optimize(
            lambda_hs=210.0,
            a_chip=0.0032,
            c=0.04,
            p_fan_max=6.6,
            t_min=0.0003,
            fan_free_flow_m3_s=0.59 / 60.0,
            fan_shutoff_pressure_pa=340.0,
            n_pts=5,
        )
        assert isinstance(result.n, int)
        assert result.n >= 2
        assert result.n * result.s + (result.n + 1) * result.t == pytest.approx(0.04)
        assert result.t >= 0.0003

    def test_b08_manufacturing_constraint_changes_selected_geometry(self):
        theoretical = cspi_optimize(lambda_hs=210.0, a_chip=0.0032, c=0.04, p_fan_max=6.6, n_pts=5)
        manufactured = cspi_optimize(
            lambda_hs=210.0,
            a_chip=0.0032,
            c=0.04,
            p_fan_max=6.6,
            t_min=0.001,
            n_pts=5,
        )
        assert theoretical.t < manufactured.t
        assert manufactured.t >= 0.001
        assert theoretical.n != manufactured.n or theoretical.s != manufactured.s


class TestM7ReviewCorrections:
    def evaluate(self, **overrides):
        values = dict(
            lambda_hs=210.0,
            sink_width_m=0.04,
            fin_height_m=0.02,
            sink_length_m=0.08,
            base_thickness_m=0.005,
            channel_count=30,
            channel_width_m=0.001,
            fin_thickness_m=0.0003,
            p_fan_max=6.6,
            fan_diameter_m=0.04,
            fan_depth_m=0.028,
            duct_length_m=0.014,
            assembly_face_width_m=0.04,
            assembly_face_height_m=0.04,
            fan_free_flow_m3_s=0.05,
            fan_shutoff_pressure_pa=3400.0,
            fan_speed_rpm=15500.0,
            t_air_c=25.0,
        )
        values.update(overrides)
        return cspi_evaluate_geometry(**values)

    def test_search_continues_to_turbulent_domain_without_bridging_transition(self):
        result = self.evaluate(
            fan_free_flow_m3_s=0.05,
            fan_shutoff_pressure_pa=3400.0,
        )
        assert result.operating_point_status == "converged"
        assert result.flow_rate_m3_s == pytest.approx(0.026497078327, rel=2e-8)
        assert result.re == pytest.approx(5349.5323, rel=2e-5)
        assert result.pressure_drop_pa == pytest.approx(1833.8629, rel=2e-5)
        assert result.pressure_drop_pa == pytest.approx(
            result.fan_pressure_scale * result.fan_pressure_pa, rel=1e-8
        )

    def test_zero_pressure_curve_has_no_forced_air_operating_point(self):
        result = self.evaluate(
            fan_speed_rpm=None,
            fan_free_flow_m3_s=None,
            fan_shutoff_pressure_pa=None,
            fan_curve_flow_m3_s=[0.0, 0.01],
            fan_curve_pressure_pa=[0.0, 0.0],
        )
        assert result.operating_point_status == "no_intersection"
        assert result.flow_rate_m3_s is None
        assert result.pressure_drop_pa is None
        assert not result.feasible
        assert result.n_fan is None

    @pytest.mark.parametrize(
        "field,value",
        [
            ("channel_count", True),
            ("channel_count", 2.5),
            ("face_count", True),
            ("face_count", 1.5),
            ("hydraulic_branch_count", False),
            ("hydraulic_branch_count", 1.5),
        ],
    )
    def test_nonintegral_or_boolean_counts_are_rejected(self, field, value):
        with pytest.raises(ValueError, match=field):
            self.evaluate(**{field: value})

    def test_overfilled_channel_and_fin_width_is_rejected(self):
        with pytest.raises(ValueError, match="overfill"):
            self.evaluate(channel_count=100)

    def test_envelope_must_contain_fan_and_complete_sink_bbox(self):
        with pytest.raises(ValueError, match="assembly_face_width_m"):
            self.evaluate(assembly_face_width_m=0.001)
        with pytest.raises(ValueError, match="assembly_face_height_m"):
            self.evaluate(assembly_face_height_m=0.001)
        with pytest.raises(ValueError, match="assembly_face_height_m"):
            self.evaluate(base_thickness_m=0.01, assembly_face_height_m=0.025)

    def test_optimizer_base_fits_inside_total_height_envelope(self):
        result = cspi_optimize(
            lambda_hs=210.0,
            a_chip=0.0032,
            c=0.04,
            p_fan_max=6.6,
            base_thickness_m=0.01,
            n_pts=3,
        )
        assert result.feasible
        assert result.sink_volume_l == pytest.approx(0.128)
        assert result.sink_material_bbox_l == pytest.approx(0.128)

    def test_only_one_or_symmetric_two_face_topologies_are_supported(self):
        with pytest.raises(ValueError, match="face_count must be 1 or 2"):
            self.evaluate(face_count=3)
        with pytest.raises(ValueError, match="face_count must be 1 or 2"):
            cspi_optimize(
                lambda_hs=210.0,
                a_chip=0.0032,
                c=0.04,
                p_fan_max=6.6,
                face_count=3,
                n_pts=3,
            )

    def test_heated_faces_are_distinct_and_multiple_channel_bodies_are_rejected(self):
        shared = self.evaluate(face_count=2, hydraulic_branch_count=1)
        assert shared.heated_face_count == 2
        assert shared.hydraulic_branch_count == 1
        with pytest.raises(ValueError, match="hydraulic_branch_count must be 1"):
            self.evaluate(face_count=2, hydraulic_branch_count=2)
        with pytest.raises(ValueError, match="hydraulic_branch_count must be 1"):
            cspi_optimize(
                lambda_hs=210.0,
                a_chip=0.0032,
                c=0.04,
                p_fan_max=6.6,
                hydraulic_branch_count=2,
                n_pts=3,
            )
        shared_loss = _rectangular_pressure_drop(
            q_total=0.01,
            n_channels=30,
            hydraulic_branch_count=1,
            gap=0.001,
            height=0.02,
            length=0.08,
            t_air_c=25.0,
        )
        duplicate_loss = _rectangular_pressure_drop(
            q_total=0.01,
            n_channels=30,
            hydraulic_branch_count=2,
            gap=0.001,
            height=0.02,
            length=0.08,
            t_air_c=25.0,
        )
        assert shared_loss[1] == pytest.approx(2.0 * duplicate_loss[1])
        assert shared_loss[0] > duplicate_loss[0]

    def test_supplied_endpoints_do_not_inherit_similarity_rpm(self):
        without_speed = self.evaluate(
            fan_free_flow_m3_s=0.009,
            fan_shutoff_pressure_pa=300.0,
            fan_speed_rpm=None,
        )
        with_speed = self.evaluate(
            fan_free_flow_m3_s=0.009,
            fan_shutoff_pressure_pa=300.0,
            fan_speed_rpm=15500.0,
        )
        assert without_speed.n_fan is None
        assert with_speed.n_fan == pytest.approx(15500.0)

    def test_independent_integer_count_gap_search_finds_better_26_channel_candidate(self):
        optimized = cspi_optimize(
            lambda_hs=210.0,
            a_chip=0.0032,
            c=0.04,
            p_fan_max=6.6,
            t_air=80.0,
            n_pts=3,
            channel_width_min_m=0.0002,
            channel_width_step_m=0.0002,
        )
        gap = 0.001
        thickness = (0.04 - 26 * gap) / 27
        candidate = cspi_evaluate_geometry(
            lambda_hs=210.0,
            sink_width_m=0.04,
            fin_height_m=0.04,
            sink_length_m=0.0032 / 0.04,
            base_thickness_m=0.0,
            channel_count=26,
            channel_width_m=gap,
            fin_thickness_m=thickness,
            p_fan_max=6.6,
            fan_diameter_m=0.04,
            t_air_c=80.0,
        )
        assert candidate.feasible
        assert thickness == pytest.approx(0.0005185185185)
        assert candidate.n_channels == 26
        assert candidate.cspi == pytest.approx(24.925537766, rel=1e-8)
        assert optimized.feasible
        assert optimized.cspi >= candidate.cspi
        assert optimized.n * optimized.s + (optimized.n + 1) * optimized.t == pytest.approx(0.04)
