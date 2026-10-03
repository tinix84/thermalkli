"""Repeatable validation scenarios and evidence reporting."""

from __future__ import annotations

import json
import platform
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from thermal_cli import __version__
from thermal_cli.benchmarks.waffler import WAFFLER_B03
from thermal_cli.cspi.optimizer import cspi_evaluate_geometry, cspi_optimize
from thermal_cli.fluids.liquid import LiquidProperty
from thermal_cli.liquid_cooling import (
    TPEL2005_B06_OBSERVATION,
    CalibratedPortLoss,
    ConstantLiquidProperties,
    SlotChannel,
    evaluate_liquid_cooler,
    liquid_energy_balance,
    pesc2004_b05_curve,
    pesc2004_b05_flow_area_resistance_k_w,
)
from thermal_cli.transient.rc_network import (
    NodalRCNetwork,
    PowerWaveform,
    intelec2003_chip8_cauer,
    onsemi_and8215_b01_network,
)


@dataclass(frozen=True)
class Scenario:
    case_id: str
    capability: str
    source: str
    conditions: Mapping[str, Any]
    run: Callable[[], Mapping[str, Any]]
    evidence_status: str
    limitations: tuple[str, ...] = ()
    acceptance_criteria: str | None = None
    acceptance: Callable[[Mapping[str, Any]], bool] | None = None


@dataclass(frozen=True)
class ScenarioRecord:
    case_id: str
    capability: str
    source: str
    conditions: Mapping[str, Any]
    evidence_status: str
    acceptance_criteria: str | None
    execution_status: str
    acceptance_status: str
    status: str
    outputs: Mapping[str, Any] | None
    limitations: tuple[str, ...]
    error: str | None = None
    acceptance_error: str | None = None


@dataclass(frozen=True)
class ValidationReport:
    created_utc: str
    package_version: str
    runtime: Mapping[str, Any]
    records: tuple[ScenarioRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_scenarios(scenarios: Sequence[Scenario]) -> ValidationReport:
    """Execute named cases and preserve source conditions, outputs, and failures."""
    ids = [scenario.case_id for scenario in scenarios]
    if len(set(ids)) != len(ids):
        raise ValueError("scenario case_id values must be unique")
    records = []
    for scenario in scenarios:
        try:
            outputs = _json_safe(dict(scenario.run()))
        except Exception as exc:
            records.append(
                ScenarioRecord(
                    case_id=scenario.case_id,
                    capability=scenario.capability,
                    source=scenario.source,
                    conditions=_json_safe(dict(scenario.conditions)),
                    evidence_status=scenario.evidence_status,
                    acceptance_criteria=scenario.acceptance_criteria,
                    execution_status="failed",
                    acceptance_status="not_checked",
                    status="failed",
                    outputs=None,
                    limitations=scenario.limitations,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        acceptance_error = None
        if scenario.acceptance is None:
            acceptance_status = "not_checked"
        else:
            try:
                acceptance_status = "passed" if scenario.acceptance(outputs) else "failed"
            except Exception as exc:
                acceptance_status = "failed"
                acceptance_error = f"{type(exc).__name__}: {exc}"
        records.append(
            ScenarioRecord(
                case_id=scenario.case_id,
                capability=scenario.capability,
                source=scenario.source,
                conditions=_json_safe(dict(scenario.conditions)),
                evidence_status=scenario.evidence_status,
                acceptance_criteria=scenario.acceptance_criteria,
                execution_status="passed",
                acceptance_status=acceptance_status,
                status=(
                    "failed"
                    if acceptance_status == "failed"
                    else "passed"
                    if acceptance_status == "passed"
                    else "recorded"
                ),
                outputs=outputs,
                limitations=scenario.limitations,
                acceptance_error=acceptance_error,
            )
        )
    return ValidationReport(
        created_utc=datetime.now(UTC).isoformat(),
        package_version=__version__,
        runtime={
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "processor": platform.processor() or "unreported",
        },
        records=tuple(records),
    )


def write_report(report: ValidationReport, path: Path) -> None:
    """Write an inspectable JSON report; parent directories are created as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def built_in_reference_scenarios() -> tuple[Scenario, ...]:
    """Return source-traceable accepted cases with conservative evidence labels."""

    def b01() -> Mapping[str, Any]:
        network = onsemi_and8215_b01_network()
        outputs = {
            "mos_self_k_w": network.steady_resistance_k_w("mos", "mos"),
            "controller_self_k_w": network.steady_resistance_k_w("cs", "cs"),
            "mos_controller_mutual_k_w": network.steady_resistance_k_w("mos", "cs"),
            "controller_mos_mutual_k_w": network.steady_resistance_k_w("cs", "mos"),
            "shortest_network_time_constant_s": network.shortest_time_constant_s,
        }
        expected = {
            "mos_self_k_w": 47.0001,
            "controller_self_k_w": 63.5032,
            "mos_controller_mutual_k_w": 29.7268,
        }
        outputs["steady_max_abs_error_k_w"] = max(
            abs(outputs[key] - value) for key, value in expected.items()
        )
        outputs["steady_reference_tolerance_k_w"] = 1e-4
        outputs["steady_reference_within_tolerance"] = outputs["steady_max_abs_error_k_w"] <= 1e-4
        return outputs

    def b02() -> Mapping[str, Any]:
        network = intelec2003_chip8_cauer()
        output_node = network.output_nodes[0]
        resistance_sum = sum((0.196, 0.633, 0.297))
        response_times = np.concatenate(([0.0], np.geomspace(1e-7, 10.0, 240)))
        powers = np.zeros((len(response_times), len(network.node_names)))
        powers[:, -1] = 1.0
        transient = network.simulate(PowerWaveform(response_times, powers))
        sample_indices = np.unique(np.linspace(0, len(response_times) - 1, 8, dtype=int))
        step_rise = transient.output_temperatures_k[:, 0] - network.ambient_k
        dc_rth = network.steady_resistance_k_w(output_node, output_node)
        return {
            "resistance_sum_k_w": resistance_sum,
            "network_dc_rth_k_w": dc_rth,
            "dc_resistance_error_k_w": abs(dc_rth - resistance_sum),
            "step_response_samples_K_per_W": step_rise[sample_indices].tolist(),
            "step_response_times_s": response_times[sample_indices].tolist(),
            "step_response_final_K_per_W": float(step_rise[-1]),
            "step_equilibrium_error_k_w": abs(float(step_rise[-1]) - resistance_sum),
        }

    def b05() -> Mapping[str, Any]:
        # PESC source conditions: water at 40 C and 992 kg/m^3, nu=658e-9 m^2/s,
        # conductivity=0.63 W/(m K), Pr=4.328. The constant-property fixture is
        # intentionally restricted to this exact source temperature.
        water = ConstantLiquidProperties(
            density_kg_m3=992.0,
            dynamic_viscosity_pa_s=992.0 * 658e-9,
            thermal_conductivity_w_mk=0.63,
            specific_heat_j_kgk=4.328 * 0.63 / (992.0 * 658e-9),
            reference_temperature_k=313.15,
            provenance="Drofenik et al., PESC 2004, water at 40 C",
        )
        geometry = SlotChannel(length_m=0.020, width_m=0.0192, gap_m=0.00025)
        pump = pesc2004_b05_curve()
        flow_area_rth = pesc2004_b05_flow_area_resistance_k_w(geometry)
        ideal = evaluate_liquid_cooler(
            pump_curve=pump,
            geometry=geometry,
            fluid=water,
            inlet_temperature_k=313.15,
            heat_w=0.0,
        )
        calibrated = evaluate_liquid_cooler(
            pump_curve=pump,
            geometry=geometry,
            fluid=water,
            inlet_temperature_k=313.15,
            heat_w=0.0,
            calibrated_port_loss=CalibratedPortLoss.pesc2004(),
            flow_area_rth_k_w=flow_area_rth,
        )
        ideal_op = ideal.operating_point
        calibrated_op = calibrated.operating_point
        energy = calibrated.energy
        energy_error = (
            abs(energy.heat_w - energy.energy_recovered_w)
            if energy is not None and energy.energy_recovered_w is not None
            else None
        )
        return {
            "pump_domain_m3_s": pump.domain_m3_s,
            "pump_provenance": pump.provenance,
            "channel_gap_m": geometry.gap_m,
            "ideal_operating_point_status": ideal_op.status,
            "ideal_flow_m3_s": ideal_op.total_flow_m3_s,
            "ideal_pressure_pa": ideal_op.pressure_pa,
            "ideal_channel_reynolds": (
                ideal_op.channel_state.reynolds if ideal_op.channel_state else None
            ),
            "ideal_slot_wall_to_bulk_rth_k_w": ideal.ideal_slot_wall_to_bulk_rth_k_w,
            "ideal_slot_to_inlet_rth_k_w": ideal.ideal_slot_to_inlet_rth_k_w,
            "calibrated_operating_point_status": calibrated_op.status,
            "calibrated_flow_m3_s": calibrated_op.total_flow_m3_s,
            "calibrated_pressure_pa": calibrated_op.pressure_pa,
            "calibrated_port_loss_pa": (
                calibrated_op.channel_state.calibrated_pressure_drop_pa
                if calibrated_op.channel_state
                else None
            ),
            "flow_area_rth_k_w": calibrated.flow_area_rth_k_w,
            "calibrated_plate_to_inlet_rth_k_w": calibrated.calibrated_plate_to_inlet_rth_k_w,
            "thermal_heat_w": energy.heat_w if energy else None,
            "thermal_energy_status": energy.status if energy else None,
            "thermal_outlet_temperature_k": energy.outlet_temperature_k if energy else None,
            "thermal_energy_balance_error_w": energy_error,
        }

    def b06() -> Mapping[str, Any]:
        return {
            "measured_flow_m3_s": TPEL2005_B06_OBSERVATION.flow_m3_s,
            "measured_pressure_pa": TPEL2005_B06_OBSERVATION.pressure_pa,
            "measured_thermal_resistance_k_w": (TPEL2005_B06_OBSERVATION.thermal_resistance_k_w),
            "thermal_reference": TPEL2005_B06_OBSERVATION.thermal_reference,
            "source_conditions": TPEL2005_B06_OBSERVATION.conditions,
        }

    def m8_energy_balance() -> Mapping[str, Any]:
        fluid = LiquidProperty("H2OGly50")
        energy = liquid_energy_balance(
            heat_w=150.0,
            flow_m3_s=2.0e-5,
            inlet_temperature_k=313.15,
            fluid=fluid,
        )
        zero_flow = liquid_energy_balance(
            heat_w=150.0,
            flow_m3_s=0.0,
            inlet_temperature_k=313.15,
            fluid=fluid,
        )
        return {
            "energy_status": energy.status,
            "inlet_temperature_k": energy.inlet_temperature_k,
            "outlet_temperature_k": energy.outlet_temperature_k,
            "mass_flow_kg_s": energy.mass_flow_kg_s,
            "energy_balance_error_w": (
                abs(energy.heat_w - energy.energy_recovered_w)
                if energy.energy_recovered_w is not None
                else None
            ),
            "positive_heat_zero_flow_status": zero_flow.status,
        }

    def m9_behavior() -> Mapping[str, Any]:
        network = onsemi_and8215_b01_network()
        index = {name: i for i, name in enumerate(network.node_names)}
        times = np.array([0.0, 1e-3, 1e-2, 0.1, 1.0])
        source_vectors = []
        for source in ("mos", "cs"):
            powers = np.zeros((len(times), len(network.node_names)))
            powers[:, index[source]] = 1.0
            source_vectors.append(
                network.simulate(PowerWaveform(times, powers)).node_temperatures_k
            )
        combined = np.zeros((len(times), len(network.node_names)))
        combined[:, index["mos"]] = 1.0
        combined[:, index["cs"]] = 1.0
        combined_result = network.simulate(PowerWaveform(times, combined))
        additive_error = float(
            np.max(
                np.abs(
                    combined_result.node_temperatures_k
                    - source_vectors[0]
                    - source_vectors[1]
                    + network.ambient_k
                )
            )
        )

        cauer = intelec2003_chip8_cauer()
        coarse_t = np.linspace(0.0, 0.1, 101)
        fine_t = np.linspace(0.0, 0.1, 201)
        coarse_p = np.zeros((len(coarse_t), len(cauer.node_names)))
        fine_p = np.zeros((len(fine_t), len(cauer.node_names)))
        coarse_p[:, -1] = fine_p[:, -1] = 1.0
        coarse = cauer.simulate(PowerWaveform(coarse_t, coarse_p))
        fine = cauer.simulate(PowerWaveform(fine_t, fine_p))
        refinement_delta = abs(
            float(coarse.output_temperatures_k[-1, 0]) - float(fine.output_temperatures_k[-1, 0])
        )

        pulse_period = NodalRCNetwork.cauer_ladder((1.0,), (1.0,), ambient_k=300.0)
        pulse_times = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
        pulse_powers = np.array([[0.0], [1.0], [1.0], [0.0], [0.0]])
        periodic = pulse_period.periodic_steady_state(
            PowerWaveform(pulse_times, pulse_powers),
            absolute_tolerance_k=1e-6,
            max_cycles=100,
        )

        min_pulse = network.minimum_supported_pulse_s
        assert min_pulse is not None
        short_times = np.array([0.0, min_pulse * 0.1, min_pulse * 0.2])
        short_powers = np.zeros((len(short_times), len(network.node_names)))
        short_powers[1, index["mos"]] = 1.0
        try:
            network.simulate(PowerWaveform(short_times, short_powers))
            short_pulse_rejected = False
        except ValueError:
            short_pulse_rejected = True

        return {
            "independent_source_superposition_max_error_k": additive_error,
            "waveform_grid_refinement_delta_at_0_1_s_k": refinement_delta,
            "periodic_state_converged": periodic.converged,
            "periodic_cycles": periodic.cycles,
            "unsupported_short_pulse_rejected": short_pulse_rejected,
            "declared_minimum_pulse_s": min_pulse,
        }

    def b03() -> Mapping[str, Any]:
        fixture = WAFFLER_B03
        return {
            "channel_pitch_m": fixture.channel_pitch_m,
            "plate_height_m": fixture.plate_height_m,
            "channel_diameter_m": fixture.channel_diameter_m,
            "extrusion_depth_m": fixture.extrusion_depth_m,
            "top_heat_flux_w_m2": fixture.top_heat_flux_W_m2,
            "applied_power_w": fixture.applied_power_W,
            "effective_metal_path_m": fixture.effective_metal_path_m,
            "analytic_metal_temperature_rise_k": fixture.analytic_metal_temperature_rise_K,
            "channel_wall_temperature_k": fixture.channel_wall_temperature_K,
            "top_sample_points_xy_m": fixture.top_sample_points_xy_m,
        }

    def b07() -> Mapping[str, Any]:
        flow_curve_m3_min = np.array(
            [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.59]
        )
        pressure_pa = np.array(
            [340.0, 308.9, 271.4, 230.2, 188.0, 140.0, 119.6, 114.7, 110.2, 89.7, 63.7, 30.5, 0.0]
        )
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
            t_air_c=80.0,
            assembly_face_width_m=0.04,
            assembly_face_height_m=0.04,
            fan_curve_flow_m3_s=tuple(float(value / 60.0) for value in flow_curve_m3_min),
            fan_curve_pressure_pa=tuple(float(value) for value in pressure_pa),
            fan_speed_rpm=15500.0,
            auxiliary_power_w=6.6,
            auxiliary_power_basis="Sanyo rated input at 12 V; rpm attribution is inferred",
        )
        measured_r_face = 0.56
        return {
            "operating_point_status": result.operating_point_status,
            "feasible": result.feasible,
            "flow_m3_s": result.flow_rate_m3_s,
            "fan_static_pressure_pa": result.fan_pressure_pa,
            "channel_pressure_drop_pa": result.pressure_drop_pa,
            "fin_spacing_pressure_scale": result.fin_spacing_ratio,
            "one_face_model_resistance_k_w": result.r_face_k_w,
            "measured_one_face_resistance_k_w": measured_r_face,
            "measured_resistance_relative_error": abs(result.r_face_k_w / measured_r_face - 1.0),
            "system_resistance_k_w": result.rth,
            "system_volume_l": result.vol,
            "cspi_w_k_l": result.cspi,
            "auxiliary_power_w": result.auxiliary_power_w,
            "auxiliary_power_basis": result.auxiliary_power_basis,
            "fan_curve_digitization_uncertainty": {
                "flow_m3_min": 0.005,
                "pressure_pa": 10.0,
                "speed_rpm_association": "inferred from adjacent table/catalog",
            },
        }

    def b08() -> Mapping[str, Any]:
        unconstrained = cspi_optimize(lambda_hs=210.0, a_chip=0.0032, c=0.04, p_fan_max=5.0)
        manufacturing = cspi_optimize(
            lambda_hs=210.0, a_chip=0.0032, c=0.04, p_fan_max=5.0, t_min=0.001
        )
        return {
            "unconstrained_model": {
                "channels": unconstrained.n,
                "fins": unconstrained.n_fins,
                "channel_width_m": unconstrained.s,
                "fin_thickness_m": unconstrained.t,
                "resistance_k_w": unconstrained.rth,
                "cspi_w_k_l": unconstrained.cspi,
                "feasible": unconstrained.feasible,
            },
            "minimum_fin_1mm_model": {
                "channels": manufacturing.n,
                "fins": manufacturing.n_fins,
                "channel_width_m": manufacturing.s,
                "fin_thickness_m": manufacturing.t,
                "resistance_k_w": manufacturing.rth,
                "cspi_w_k_l": manufacturing.cspi,
                "feasible": manufacturing.feasible,
            },
            "source_reported_theoretical": {
                "fins": 26,
                "channel_width_m": 0.001,
                "fin_thickness_m": 0.00054,
                "resistance_k_w": 0.26,
            },
            "source_reported_manufacturing": {
                "fins": 16,
                "channel_width_m": 0.0015,
                "fin_thickness_m": 0.001,
                "resistance_k_w": 0.30,
            },
        }

    return (
        Scenario(
            "B01",
            "grounded coupled package RC network",
            "onsemi AND8215/D Rev. 1, Tables 1-2",
            {"nodes": 16, "power_inputs": "independent MOS and controller nodes"},
            b01,
            "steady_coefficients_checked; transient source-curve comparison pending",
            (
                "Published steady coefficients are reported; digitized transient "
                "samples are not bundled.",
            ),
            "steady_max_abs_error_k_w <= steady_reference_tolerance_k_w",
            lambda output: output["steady_reference_within_tolerance"] is True,
        ),
        Scenario(
            "B02",
            "Cauer ladder step response",
            "Drofenik et al., INTELEC 2003, Table 3/Fig. 10, chip 8",
            {
                "resistances_k_w": [0.196, 0.633, 0.297],
                "capacitances_j_k": [0.0223, 0.0215, 0.253],
                "input": "1 W step at junction node",
            },
            b02,
            "Cauer_step_executed; digitized transient comparison pending",
            ("Cauer topology is retained as a ladder and is not treated as Foster branches.",),
            "DC and final step resistance errors <= 1e-8 K/W",
            lambda output: (
                output["dc_resistance_error_k_w"] <= 1e-8
                and output["step_equilibrium_error_k_w"] <= 1e-8
            ),
        ),
        Scenario(
            "B03",
            "Waffler periodic solid-conduction channel fixture",
            "Waffler, Fig. 4.46 and Eqs. 4.152/4.154",
            {
                "channel_pitch_m": WAFFLER_B03.channel_pitch_m,
                "plate_height_m": WAFFLER_B03.plate_height_m,
                "channel_diameter_m": WAFFLER_B03.channel_diameter_m,
                "extrusion_depth_m": WAFFLER_B03.extrusion_depth_m,
                "top_heat_flux_w_m2": WAFFLER_B03.top_heat_flux_W_m2,
                "conductivity_w_m_k": WAFFLER_B03.aluminum_conductivity_W_m_K,
            },
            b03,
            "source_fixture_and_analytic_estimate_recorded; FEMM/source-field parity pending",
            (
                "The analytic metal path is a correlation estimate, not a FEMM result; "
                "the fixed channel-wall boundary is an explicit fixture choice.",
            ),
        ),
        Scenario(
            "B05",
            "pump-limited ideal and calibrated slot",
            "Drofenik et al., PESC 2004, Eqs. 1-13 and Fig. 2",
            {
                "slot_length_m": 0.020,
                "slot_width_m": 0.0192,
                "slot_gap_m": 0.00025,
                "water_temperature_k": 313.15,
                "thermal_resistance_basis": "small-signal at 313.15 K; heat_w=0",
                "flow_basis": "total loop flow; one channel",
            },
            b05,
            "model_output_executed; PESC source parity pending",
            (
                "The calibrated port fit is source-specific and requires the original "
                "inlet/outlet geometry. Resistance outputs use constant water properties "
                "at 313.15 K and zero-load small-signal evaluation.",
            ),
            "ideal and calibrated operating points and calibrated thermal energy balance are ok",
            lambda output: (
                output["ideal_operating_point_status"] == "ok"
                and output["calibrated_operating_point_status"] == "ok"
                and output["thermal_energy_status"] == "ok"
                and output["thermal_energy_balance_error_w"] <= 1e-8
                and output["ideal_slot_wall_to_bulk_rth_k_w"] is not None
                and output["calibrated_plate_to_inlet_rth_k_w"] is not None
            ),
        ),
        Scenario(
            "B06",
            "liquid-cooler measured reference",
            TPEL2005_B06_OBSERVATION.source,
            {
                "flow_m3_s": TPEL2005_B06_OBSERVATION.flow_m3_s,
                "pressure_pa": TPEL2005_B06_OBSERVATION.pressure_pa,
                "baseplate": "25 x 34 mm",
            },
            b06,
            "source_observation_retained; model reproduction unresolved",
            ("Matching geometry and boundary/contact data are not present.",),
        ),
        Scenario(
            "B07",
            "bounded fan operating point and two-face CSPI",
            (
                "Drofenik & Kolar, PCC 2007, Figs. 6-9 and Eqs. 1-18; "
                "Sanyo Technical Report 48, Fig. 6"
            ),
            {
                "sink_m": [0.08, 0.04, 0.025],
                "base_thickness_m": 0.005,
                "channel_count": 30,
                "channel_width_m": 0.001,
                "fin_thickness_m": 0.0003,
                "heated_faces": 2,
                "fan_curve": (
                    "109P0412K3013 digitized; exact endpoints and ~0.05 m3/min interior samples"
                ),
            },
            b07,
            (
                "source-mapped operating case executed; fixture-specific resistance "
                "criterion only; exact source parity not claimed"
            ),
            (
                "Interior fan-curve digitization uncertainty is approximately ±0.005 "
                "m3/min and ±10 Pa; speed attribution is inferred. The 20% resistance "
                "criterion is B07-specific, not a general accuracy bound.",
            ),
            "operating point converged and |R_face/0.56 - 1| <= 0.20",
            lambda output: (
                output["operating_point_status"] == "converged"
                and output["feasible"] is True
                and output["measured_resistance_relative_error"] <= 0.20
            ),
        ),
        Scenario(
            "B08",
            "theoretical and manufacturing-constrained CSPI optima",
            "Drofenik & Kolar, PCC 2007, Fig. 7 and reported practical geometry",
            {"a_chip_m2": 0.0032, "sink_height_m": 0.04, "conductivity_w_m_k": 210.0},
            b08,
            "both current-model searches executed; source-reported geometry parity pending",
            (
                "Current pressure and heat-transfer model outputs differ from the "
                "reported B08 geometries; "
                "they are kept side by side and not presented as reproduction.",
            ),
            "both model cases feasible; 1 mm minimum-fin constraint is satisfied and raises R",
            lambda output: (
                output["unconstrained_model"]["feasible"] is True
                and output["minimum_fin_1mm_model"]["feasible"] is True
                and output["minimum_fin_1mm_model"]["fin_thickness_m"] >= 0.001 - 1e-12
                and output["minimum_fin_1mm_model"]["resistance_k_w"]
                > output["unconstrained_model"]["resistance_k_w"]
            ),
        ),
        Scenario(
            "M8-ENERGY",
            "temperature-dependent liquid energy balance",
            "M8 conservation equation Q=m_dot*cp(T_mean)*(Tout-Tin)",
            {"heat_w": 150.0, "flow_m3_s": 2e-5, "inlet_temperature_k": 313.15},
            m8_energy_balance,
            "energy_balance_and_zero_flow_behavior_executed",
            acceptance_criteria=("energy error <= 1e-8 W and positive-heat zero-flow is invalid"),
            acceptance=lambda output: (
                output["energy_status"] == "ok"
                and output["energy_balance_error_w"] <= 1e-8
                and output["positive_heat_zero_flow_status"] == "invalid_flow"
            ),
        ),
        Scenario(
            "M9-DYNAMICS",
            "waveform-grid refinement, independent sources, periodic convergence, pulse limit",
            "M9 grounded nodal RC solver acceptance",
            {"onsemi_nodes": 16, "cauer_fixture": "INTELEC 2003 chip 8"},
            m9_behavior,
            "behavioral_acceptance_executed; source waveform parity pending",
            acceptance_criteria=(
                "source superposition <= 1e-8 K, waveform-grid delta <= 1e-5 K, "
                "periodic convergence and short-pulse rejection"
            ),
            acceptance=lambda output: (
                output["independent_source_superposition_max_error_k"] <= 1e-8
                and output["waveform_grid_refinement_delta_at_0_1_s_k"] <= 1e-5
                and output["periodic_state_converged"] is True
                and output["unsupported_short_pulse_rejected"] is True
            ),
        ),
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"report contains non-JSON value {type(value).__name__}")
