"""Literature-validated tests for CSPI formulas.
Reference: Drofenik & Kolar, CIPS 2006.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from thermal_cli.cspi.formulas import cspi_calc, fan_scaling_fit
from thermal_cli.cspi.optimizer import cspi_evaluate_geometry


class TestCspiLiterature:
    def test_eq41_definition(self):
        """CSPI = 1/(Rth * Vol) — eq. 41. Rth=0.2, Vol=1 -> CSPI=5."""
        assert cspi_calc(rth=0.2, vol_cs=1.0) == pytest.approx(5.0)

    def test_cspi_units_consistency(self):
        """Rth=1 K/W, Vol=1 liter -> CSPI=1 W/(K*liter)."""
        assert cspi_calc(rth=1.0, vol_cs=1.0) == pytest.approx(1.0)

    def test_b07_supplied_resistance_screening_identity(self):
        """PCC Fig. 8/eq. 18: measured one-face R, symmetric volume boundary."""
        r_system = 0.56 / 2.0
        v_system_l = 0.195
        assert cspi_calc(rth=r_system, vol_cs=v_system_l) == pytest.approx(18.315018315)


class TestFanScalingLiterature:
    def test_drofenik_eq29_31_roundtrip(self):
        """Fan scaling roundtrip: fit k then reconstruct original values."""
        v_max, dp_max, p_fan = 0.06, 80.0, 4.0
        d, n = 0.10, 3000.0
        k1, k2, k3 = fan_scaling_fit(v_max=v_max, dp_max=dp_max, p_fan=p_fan, d=d, n=n)
        assert k1 * n * d**3 == pytest.approx(v_max, rel=1e-10)
        assert k2 * n**2 * d**2 == pytest.approx(dp_max, rel=1e-10)
        assert k3 * n**3 * d**5 == pytest.approx(p_fan, rel=1e-10)


class TestB07SanyoFanCurve:
    def _curve(self):
        path = Path(__file__).parent / "fixtures" / "b07_sanyodenki_109p0412k3013_curve.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = csv.DictReader(line for line in handle if not line.startswith("#"))
            data = list(rows)
        return (
            [float(row["flow_m3_min"]) / 60.0 for row in data],
            [float(row["pressure_pa"]) for row in data],
        )

    @pytest.mark.parametrize("t_air_c", [25.0, 80.0])
    def test_b07_shared_channel_manufacturer_curve_operating_case(self, t_air_c):
        flow, pressure = self._curve()
        result = cspi_evaluate_geometry(
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
            face_count=2,
            hydraulic_branch_count=1,
            t_air_c=t_air_c,
            assembly_face_width_m=0.04,
            assembly_face_height_m=0.04,
            fan_curve_flow_m3_s=flow,
            fan_curve_pressure_pa=pressure,
            fan_speed_rpm=15500.0,
            auxiliary_power_w=6.6,
            auxiliary_power_basis=(
                "Sanyo rated input at 12 V; rpm inferred from adjacent table/catalog"
            ),
        )
        assert result.feasible
        assert result.operating_point_status == "converged"
        assert result.face_count == 2
        assert result.hydraulic_branch_count == 1
        assert result.n_fan == pytest.approx(15500.0)
        assert result.fin_spacing_ratio == pytest.approx(0.75)
        assert result.fan_pressure_scale == pytest.approx(0.75)
        assert result.pressure_drop_pa == pytest.approx(
            result.fan_pressure_scale * result.fan_pressure_pa, rel=1e-8
        )
        assert 0.0 < result.flow_rate_m3_s < flow[-1]
        assert result.pressure_drop_pa > 0.0
        assert result.vol == pytest.approx(0.1952)
        assert result.sink_material_bbox_l == pytest.approx(0.08)

    def test_b07_symmetric_faces_use_half_fin_height_per_face(self):
        flow, pressure = self._curve()
        two_face = cspi_evaluate_geometry(
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
            face_count=2,
            hydraulic_branch_count=1,
            t_air_c=80.0,
            assembly_face_width_m=0.04,
            assembly_face_height_m=0.04,
            fan_curve_flow_m3_s=flow,
            fan_curve_pressure_pa=pressure,
            fan_speed_rpm=15500.0,
            auxiliary_power_w=6.6,
            auxiliary_power_basis="B07 source curve diagnostic",
        )
        one_face = cspi_evaluate_geometry(
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
            face_count=1,
            hydraulic_branch_count=1,
            t_air_c=80.0,
            assembly_face_width_m=0.04,
            assembly_face_height_m=0.04,
            fan_curve_flow_m3_s=flow,
            fan_curve_pressure_pa=pressure,
            fan_speed_rpm=15500.0,
            auxiliary_power_w=6.6,
            auxiliary_power_basis="B07 source curve diagnostic",
        )

        # PCC's symmetric half-sink face has c/2 fin height; this is a
        # geometry/network check, not a claim of source thermal parity.
        assert two_face.fin_spacing_ratio == pytest.approx(0.75)
        assert two_face.fan_pressure_pa is not None
        assert two_face.pressure_drop_pa == pytest.approx(
            two_face.fin_spacing_ratio * two_face.fan_pressure_pa, rel=1e-8
        )
        assert two_face.flow_rate_m3_s == pytest.approx(0.003642153368, rel=1e-8)
        assert two_face.r_face_k_w == pytest.approx(0.572478762, rel=1e-8)
        expected_fin_area_per_face = 2.0 * 31 * 0.08 * (0.02 / 2.0)
        assert expected_fin_area_per_face == pytest.approx(0.0496)
        assert two_face.fin_efficiency == pytest.approx(0.931877867, rel=1e-7)
        assert two_face.r_face_k_w == pytest.approx(0.572478762, rel=1e-7)
        assert two_face.rth == pytest.approx(0.286239381, rel=1e-7)
        assert one_face.fin_efficiency == pytest.approx(0.780956364, rel=1e-7)
        assert one_face.r_face_k_w == pytest.approx(0.321909418, rel=1e-7)
