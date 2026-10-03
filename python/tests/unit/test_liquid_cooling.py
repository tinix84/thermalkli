"""Focused regression tests for M8 pump-limited liquid cooling."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest
from typer.testing import CliRunner

from thermal_cli.cli.main import app
from thermal_cli.fluids.liquid import LiquidProperty
from thermal_cli.liquid_cooling import (
    PumpCurve,
    SlotChannel,
    _darcy_factor,
    channel_hydraulic_state,
    evaluate_liquid_cooler,
    liquid_energy_balance,
    pesc2004_b05_flow_area_resistance_k_w,
)


@dataclass(frozen=True)
class _TestFluid:
    temperature_range_k: tuple[float, float] = (280.0, 340.0)

    def density(self, temperature: float) -> float:
        self._check(temperature)
        return 1000.0

    def dynamic_viscosity(self, temperature: float) -> float:
        self._check(temperature)
        return 0.001

    def thermal_conductivity(self, temperature: float) -> float:
        self._check(temperature)
        return 0.6

    def specific_heat_cp(self, temperature: float) -> float:
        self._check(temperature)
        return 4180.0

    def _check(self, temperature: float) -> None:
        if not self.temperature_range_k[0] <= temperature <= self.temperature_range_k[1]:
            raise ValueError("temperature outside test-fluid range")


def _pump_at_flow(
    geometry: SlotChannel, fluid: _TestFluid, flow_m3_s: float, channel_count: int
) -> PumpCurve:
    pressure = channel_hydraulic_state(
        geometry=geometry,
        total_flow_m3_s=flow_m3_s,
        channel_count=channel_count,
        fluid=fluid,
        temperature_k=300.0,
    ).pressure_drop_pa
    return PumpCurve(
        np.array([0.0, flow_m3_s, 2.0 * flow_m3_s]),
        np.array([2.0 * pressure, pressure, 0.0]),
    )


def test_equal_parallel_channels_reduce_whole_plate_slot_resistance() -> None:
    fluid = _TestFluid()
    geometry = SlotChannel(length_m=0.02, width_m=0.0192, gap_m=0.0003)
    branch_flow = 1.0e-5

    one_channel = evaluate_liquid_cooler(
        pump_curve=_pump_at_flow(geometry, fluid, branch_flow, 1),
        geometry=geometry,
        fluid=fluid,
        inlet_temperature_k=300.0,
        heat_w=150.0,
        channel_count=1,
        flow_area_rth_k_w=1.0,
    )
    two_channels = evaluate_liquid_cooler(
        pump_curve=_pump_at_flow(geometry, fluid, 2.0 * branch_flow, 2),
        geometry=geometry,
        fluid=fluid,
        inlet_temperature_k=300.0,
        heat_w=150.0,
        channel_count=2,
        flow_area_rth_k_w=1.0,
    )

    assert one_channel.ideal_slot_wall_to_bulk_rth_k_w is not None
    assert two_channels.ideal_slot_wall_to_bulk_rth_k_w == pytest.approx(
        one_channel.ideal_slot_wall_to_bulk_rth_k_w / 2.0
    )
    assert one_channel.ideal_slot_to_inlet_rth_k_w is not None
    assert two_channels.ideal_slot_to_inlet_rth_k_w == pytest.approx(
        one_channel.ideal_slot_to_inlet_rth_k_w / 2.0
    )
    assert two_channels.flow_area_rth_k_w == 1.0
    assert two_channels.calibrated_plate_to_inlet_rth_k_w == pytest.approx(
        1.0
        / (
            1.0 / two_channels.ideal_slot_wall_to_bulk_rth_k_w
            + 1.0 / two_channels.flow_area_rth_k_w
        )
        + (two_channels.ideal_slot_to_inlet_rth_k_w - two_channels.ideal_slot_wall_to_bulk_rth_k_w)
    )


def test_zero_flow_with_positive_heat_is_returned_without_slot_assertion() -> None:
    fluid = _TestFluid()
    result = evaluate_liquid_cooler(
        pump_curve=PumpCurve(np.array([0.0, 1.0e-4]), np.array([0.0, 0.0])),
        geometry=SlotChannel(length_m=0.02, width_m=0.0192, gap_m=0.0003),
        fluid=fluid,
        inlet_temperature_k=300.0,
        heat_w=150.0,
    )

    assert result.operating_point.status == "ok"
    assert result.energy is not None
    assert result.energy.status == "invalid_flow"
    assert result.energy.reason == "positive heat requires positive liquid flow"
    assert result.ideal_slot_wall_to_bulk_rth_k_w is None


def test_positive_heat_that_pushes_outlet_outside_fluid_range_is_invalid() -> None:
    fluid = LiquidProperty("H2OGly50")

    result = liquid_energy_balance(
        heat_w=1000.0,
        flow_m3_s=1.0e-5,
        inlet_temperature_k=350.0,
        fluid=fluid,
    )

    assert result.status == "invalid_temperature"
    assert result.outlet_temperature_k is not None
    assert result.outlet_temperature_k > fluid.temperature_range_k[1]
    assert "outlet temperature" in (result.reason or "")


def test_constant_source_properties_reject_temperature_rise_extrapolation() -> None:
    from thermal_cli.liquid_cooling import ConstantLiquidProperties

    fluid = ConstantLiquidProperties(
        density_kg_m3=1000.0,
        dynamic_viscosity_pa_s=0.001,
        thermal_conductivity_w_mk=0.6,
        specific_heat_j_kgk=4180.0,
        reference_temperature_k=300.0,
        provenance="test source point",
    )

    result = liquid_energy_balance(
        heat_w=100.0,
        flow_m3_s=1.0e-4,
        inlet_temperature_k=300.0,
        fluid=fluid,
    )

    assert result.status == "invalid_temperature"
    assert result.reason is not None


def test_missing_heat_capacity_is_an_explicit_invalid_property_state() -> None:
    oil = LiquidProperty("SAE30")

    assert oil.density(293.15) == pytest.approx(881.5, abs=5.0)
    assert oil.dynamic_viscosity(293.15) == pytest.approx(0.2394, abs=0.01)
    result = liquid_energy_balance(
        heat_w=100.0,
        flow_m3_s=1.0e-4,
        inlet_temperature_k=293.15,
        fluid=oil,
    )

    assert result.status == "invalid_properties"
    assert "does not provide specific heat cp" in (result.reason or "")


def test_slot_darcy_factor_is_continuous_at_laminar_transition() -> None:
    geometry = SlotChannel(length_m=0.02, width_m=0.01, gap_m=0.01)
    dh = geometry.hydraulic_diameter_m

    just_below = _darcy_factor(2299.999, geometry, dh)
    at_transition = _darcy_factor(2300.0, geometry, dh)

    assert at_transition == pytest.approx(just_below, rel=1.0e-6)


def test_pesc_flow_area_calibration_uses_published_gap_boundary() -> None:
    below = SlotChannel(length_m=0.02, width_m=0.0192, gap_m=1.2e-3)
    above = SlotChannel(length_m=0.02, width_m=0.0192, gap_m=1.2001e-3)

    assert pesc2004_b05_flow_area_resistance_k_w(below) == 1.0
    assert pesc2004_b05_flow_area_resistance_k_w(above) == 0.4


def test_cli_returns_failure_for_zero_flow_with_positive_heat(tmp_path) -> None:
    config = tmp_path / "zero-flow.yaml"
    config.write_text(
        """\
fluid: H2OGly50
inlet_temperature_k: 313.15
heat_w: 150
pump_curve:
  flow_m3_s: [0.0, 0.0001]
  pressure_pa: [0.0, 0.0]
geometry:
  type: slot
  length_m: 0.02
  width_m: 0.0192
  gap_m: 0.0003
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["liquid-cooler", "--config", str(config)])

    assert result.exit_code == 1, result.output
    assert "energy_status=invalid_flow" in result.output
    assert "positive heat requires positive liquid flow" in result.output


def test_cli_rejects_fractional_channel_count_without_truncation(tmp_path) -> None:
    config = tmp_path / "fractional-count.yaml"
    config.write_text(
        """\
fluid: H2OGly50
inlet_temperature_k: 313.15
heat_w: 150
pump_curve:
  flow_m3_s: [0.0, 0.00001, 0.00002, 0.00003]
  pressure_pa: [14000, 11000, 7000, 2000]
geometry:
  type: slot
  length_m: 0.02
  width_m: 0.0192
  gap_m: 0.0003
  channel_count: 1.9
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["liquid-cooler", "--config", str(config)])

    assert result.exit_code == 2, result.output
    assert "channel_count must be a positive integer" in result.output


def test_cli_reports_source_calibrated_flow_area_path(tmp_path) -> None:
    config = tmp_path / "calibrated-flow-area.yaml"
    config.write_text(
        """\
fluid: H2OGly50
inlet_temperature_k: 313.15
heat_w: 150
pump_curve:
  flow_m3_s: [0.0, 0.00001, 0.00002, 0.00003]
  pressure_pa: [14000, 11000, 7000, 2000]
geometry:
  type: slot
  length_m: 0.02
  width_m: 0.0192
  gap_m: 0.0003
flow_area_calibration: pesc2004_b05
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["liquid-cooler", "--config", str(config)])

    assert result.exit_code == 0, result.output
    assert "flow_area_calibration=pesc2004_b05" in result.output
    assert "R_flow_area_K_W=1" in result.output
    assert "R_calibrated_plate_to_inlet_K_W=" in result.output
