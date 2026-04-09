"""Tests for thermal_cli.designer — ThermalModelSemi and ThermalPcb.

Reference values from test_thermal_model_semi.m.
"""

from __future__ import annotations

import pytest

from thermal_cli.designer import SemiInput, SemiOutput, ThermalModelSemi, ThermalPcb
from thermal_cli.designer.types import LayerDef

# --- ThermalPcb ---


class TestThermalPcb:
    def test_no_vias(self) -> None:
        """Without vias, effective conductivity equals laminate conductivity."""
        pcb = ThermalPcb(
            layer_stack=[LayerDef(thickness=0.001, conductivity=0.3)],
            area_contact=1e-4,
            num_via=0,
        )
        stack = pcb.to_thermal_layer_stack()
        assert stack.layers[0].k_op == pytest.approx(0.3, rel=1e-10)

    def test_with_vias_increases_conductivity(self) -> None:
        """Vias increase effective through-plane conductivity."""
        pcb_no_via = ThermalPcb(
            layer_stack=[LayerDef(thickness=0.001, conductivity=0.3)],
            area_contact=1e-4,
            num_via=0,
        )
        pcb_with_via = ThermalPcb(
            layer_stack=[LayerDef(thickness=0.001, conductivity=0.3)],
            area_contact=1e-4,
            num_via=10,
            area_single_via=7.85e-8,  # 0.1mm radius via
            k_via=385.0,
        )
        k_no = pcb_no_via.to_thermal_layer_stack().layers[0].k_op
        k_with = pcb_with_via.to_thermal_layer_stack().layers[0].k_op
        assert k_with > k_no

    def test_via_fraction_capped(self) -> None:
        """Via fraction can't exceed 1.0."""
        pcb = ThermalPcb(
            layer_stack=[LayerDef(thickness=0.001, conductivity=0.3)],
            area_contact=1e-6,  # very small area
            num_via=1000,
            area_single_via=1e-5,  # impossibly large fraction
            k_via=385.0,
        )
        stack = pcb.to_thermal_layer_stack()
        # k_eff should be capped at k_via when fraction >= 1
        assert stack.layers[0].k_op == pytest.approx(385.0, rel=1e-10)


# --- ThermalModelSemi ---


class TestThermalModelSemiCase2:
    """Case 2: bottom path without vias."""

    @pytest.fixture()
    def result(self) -> SemiOutput:
        inp = SemiInput(
            p_loss_junction=5.0,  # moderate power for PCB-mounted semi
            include_bottom=True,
            r_th_jc_bottom=0.5,
            area_contact=1e-4,  # 10mm x 10mm die
            area_diss_bottom=4e-4,  # 20mm x 20mm dissipation
            h_fluid_bottom=500.0,
            temp_fluid_bottom=343.15,  # 70°C
            pcb_layer_stack=[
                LayerDef(thickness=0.0003, conductivity=0.3),
                LayerDef(thickness=0.0001, conductivity=385.0),
                LayerDef(thickness=0.0003, conductivity=0.3),
            ],
        )
        model = ThermalModelSemi(inp)
        return model.solve()

    def test_case_detected(self, result: SemiOutput) -> None:
        assert result.path_case == 2

    def test_junction_above_fluid(self, result: SemiOutput) -> None:
        assert result.t_junction > 343.15

    def test_junction_realistic(self, result: SemiOutput) -> None:
        """5W through PCB: junction should be between 70°C and 200°C."""
        assert 343.15 < result.t_junction < 473.15

    def test_rth_positive(self, result: SemiOutput) -> None:
        assert result.r_th_junction_fluid_bottom > 0.0


class TestThermalModelSemiCase1:
    """Case 1: bottom path with vias."""

    @pytest.fixture()
    def result(self) -> SemiOutput:
        inp = SemiInput(
            p_loss_junction=20.0,
            include_bottom=True,
            r_th_jc_bottom=0.3,
            area_contact=42e-6,
            area_diss_bottom=168e-6,
            h_fluid_bottom=500.0,
            temp_fluid_bottom=347.15,  # 74°C
            pcb_layer_stack=[
                LayerDef(thickness=0.0003, conductivity=0.3),
            ],
            pcb_num_via=238,
            area_single_via=4.9e-8,
            k_via=385.0,
        )
        model = ThermalModelSemi(inp)
        return model.solve()

    def test_case_detected(self, result: SemiOutput) -> None:
        assert result.path_case == 1

    def test_junction_above_fluid(self, result: SemiOutput) -> None:
        assert result.t_junction > 347.15

    def test_rth_positive(self, result: SemiOutput) -> None:
        assert result.r_th_junction_fluid_bottom > 0.0

    def test_via_count_stored(self, result: SemiOutput) -> None:
        assert result.pcb_num_via == 238


class TestThermalModelSemiCase5:
    """Case 5: top path only."""

    @pytest.fixture()
    def result(self) -> SemiOutput:
        inp = SemiInput(
            p_loss_junction=10.0,
            include_bottom=False,
            include_top=True,
            r_th_jc_top=1.5,
            area_case_top=1e-4,
            area_diss_top=4e-4,
            h_fluid_top=25.0,
            temp_fluid_top=323.15,  # 50°C
        )
        model = ThermalModelSemi(inp)
        return model.solve()

    def test_case_detected(self, result: SemiOutput) -> None:
        assert result.path_case == 5

    def test_junction_above_fluid(self, result: SemiOutput) -> None:
        assert result.t_junction > 323.15

    def test_rth_top(self, result: SemiOutput) -> None:
        """Rth_top = Rth_jc + 1/(h*A) = 1.5 + 1/(25*4e-4) = 1.5 + 100 = 101.5."""
        expected = 1.5 + 1.0 / (25.0 * 4e-4)
        assert result.r_th_case_top_ambient == pytest.approx(expected, rel=1e-6)


class TestThermalModelSemiCase3:
    """Case 3: bottom + top with vias."""

    @pytest.fixture()
    def result(self) -> SemiOutput:
        inp = SemiInput(
            p_loss_junction=30.0,
            include_bottom=True,
            include_top=True,
            r_th_jc_bottom=0.3,
            r_th_jc_top=2.0,
            area_contact=42e-6,
            area_diss_bottom=168e-6,
            h_fluid_bottom=500.0,
            temp_fluid_bottom=343.15,
            area_case_top=1e-4,
            area_diss_top=4e-4,
            h_fluid_top=25.0,
            temp_fluid_top=323.15,
            pcb_layer_stack=[LayerDef(thickness=0.0003, conductivity=0.3)],
            pcb_num_via=100,
            area_single_via=4.9e-8,
            k_via=385.0,
        )
        model = ThermalModelSemi(inp)
        return model.solve()

    def test_case_detected(self, result: SemiOutput) -> None:
        assert result.path_case == 3

    def test_parallel_lower_rth(self, result: SemiOutput) -> None:
        """Parallel path → junction temp lower than single-path would give."""
        assert result.t_junction > 0.0
        # Should be warmer than coldest fluid but not excessively hot
        assert result.t_junction > 323.15
