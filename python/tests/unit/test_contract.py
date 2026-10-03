from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from thermal_cli.baseplate.contract import (
    HeatBalanceV1,
    ThermalResultV1,
    ThermalScenarioV1,
    celsius_to_kelvin,
    kelvin_to_celsius,
)


def device(device_id: str, x: float) -> dict:
    return {
        "id": device_id,
        "center_x_m": x,
        "center_y_m": 0.04,
        "orientation_deg": 0,
        "package_envelope": {"width_m": 0.018, "height_m": 0.025},
        "thermal_contact_footprint": {"width_m": 0.015, "height_m": 0.020},
        "mounting_clearance_m": 0.001,
        "geometry_provenance": "synthetic test package envelope",
        "power_W": 30.0,
        "r_theta_jc": {
            "metric": "RthetaJC",
            "value_K_per_W": 0.4,
            "from_surface": "junction",
            "to_surface": "package_case_bottom",
            "test_conditions": "synthetic fixture conditions",
            "provenance": "synthetic test input",
        },
        "contact_resistance": {
            "metric": "Rcontact",
            "value_K_per_W": 0.05,
            "from_surface": "package_case_bottom",
            "to_surface": "baseplate_top",
            "included_path": "case_bottom_to_baseplate_top_once",
            "provenance": "synthetic test input",
        },
        "junction_limit_K": 423.15,
        "junction_limit_provenance": "synthetic test limit",
        "observed_metrics": [],
    }


def scenario_data() -> dict:
    return {
        "schema_version": "thermal-scenario/v1",
        "scenario_id": "synthetic-shared-sink",
        "evidence_class": "synthetic",
        "coordinate_origin": "lower_left_baseplate_corner",
        "units": {
            "length": "m",
            "power": "W",
            "resistance": "K/W",
            "temperature": "K",
            "temperature_difference": "K",
        },
        "baseplate": {
            "length_x_m": 0.1,
            "length_y_m": 0.08,
            "thickness_m": 0.003,
            "conductivity_W_mK": 385.0,
            "material_id": "synthetic-copper-like",
            "material_provenance": "synthetic test input",
            "grid_points_x": 21,
            "grid_points_y": 17,
        },
        "sink": {
            "baseplate_to_sink_contact": {
                "metric": "Rmount",
                "value_K_per_W": 0.0,
                "from_surface": "baseplate_bottom",
                "to_surface": "heatsink_base",
                "provenance": "synthetic ideal mounting boundary",
            },
            "r_theta_sa": {
                "metric": "RthetaSA",
                "value_K_per_W": 0.2,
                "from_surface": "heatsink_base",
                "to_surface": "ambient_air",
                "reference_temperature_K": 298.15,
                "operating_conditions": "synthetic fixed ambient reference",
                "provenance": "synthetic test input",
                "spatial_approximation": "uniform_area_extraction",
            }
        },
        "devices": [device("SYNTH-Q1", 0.03), device("SYNTH-Q2", 0.07)],
        "assumptions": ["synthetic inputs; contract test only"],
    }


def test_celsius_kelvin_conversion_round_trip_and_absolute_zero() -> None:
    for celsius in (-273.15, -40.0, 0.0, 25.0, 150.0):
        assert kelvin_to_celsius(celsius_to_kelvin(celsius)) == pytest.approx(celsius)
    assert celsius_to_kelvin(-273.15) == 0.0
    with pytest.raises(ValueError):
        celsius_to_kelvin(float("nan"))
    with pytest.raises(ValueError):
        kelvin_to_celsius(-0.01)


def test_scenario_preserves_device_order_and_explicit_units() -> None:
    scenario = ThermalScenarioV1.model_validate(scenario_data())
    assert [item.id for item in scenario.devices] == ["SYNTH-Q1", "SYNTH-Q2"]
    assert scenario.units.temperature == "K"
    assert scenario.sink.baseplate_to_sink_contact.from_surface == "baseplate_bottom"
    assert scenario.sink.baseplate_to_sink_contact.to_surface == "heatsink_base"
    assert scenario.sink.r_theta_sa.from_surface == "heatsink_base"
    assert scenario.sink.r_theta_sa.to_surface == "ambient_air"


def test_duplicate_device_ids_are_rejected() -> None:
    data = scenario_data()
    data["devices"][1]["id"] = data["devices"][0]["id"]
    with pytest.raises(ValidationError, match="device IDs must be unique"):
        ThermalScenarioV1.model_validate(data)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda data: data["devices"][0].update(power_W=-1.0), "greater than or equal to 0"),
        (
            lambda data: data["devices"][0]["thermal_contact_footprint"].update(width_m=0.0),
            "greater than 0",
        ),
        (
            lambda data: data["devices"][0]["r_theta_jc"].update(value_K_per_W=float("inf")),
            "finite number",
        ),
    ],
)
def test_invalid_power_geometry_and_resistance_are_rejected(change, message: str) -> None:
    data = scenario_data()
    change(data)
    with pytest.raises(ValidationError, match=message):
        ThermalScenarioV1.model_validate(data)


def test_package_and_mounting_clearance_must_fit_baseplate() -> None:
    data = scenario_data()
    data["devices"][0]["center_x_m"] = 0.005
    with pytest.raises(ValidationError, match="must fit the baseplate"):
        ThermalScenarioV1.model_validate(data)


def test_contact_footprint_must_fit_mechanical_envelope() -> None:
    data = scenario_data()
    data["devices"][0]["thermal_contact_footprint"]["width_m"] = 0.020
    with pytest.raises(ValidationError, match="must fit its package envelope"):
        ThermalScenarioV1.model_validate(data)


def test_observation_metrics_have_distinct_reference_surfaces() -> None:
    data = scenario_data()
    data["devices"][0]["observed_metrics"] = [
        {
            "metric": "PsiJT",
            "value_K_per_W": 0.6,
            "from_surface": "junction",
            "to_surface": "package_top_center",
            "test_conditions": "synthetic characterization conditions",
            "provenance": "synthetic test observation",
        }
    ]
    scenario = ThermalScenarioV1.model_validate(data)
    assert scenario.devices[0].observed_metrics[0].metric == "PsiJT"


def test_psi_jt_cannot_be_used_as_rjc_or_as_an_extra_resistor() -> None:
    data = scenario_data()
    data["devices"][0]["r_theta_jc"]["metric"] = "PsiJT"
    with pytest.raises(ValidationError):
        ThermalScenarioV1.model_validate(data)

    data = scenario_data()
    data["devices"][0]["psi_jt_resistance_K_per_W"] = 0.6
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ThermalScenarioV1.model_validate(data)


def test_engineering_scenario_rejects_unknown_or_synthetic_evidence() -> None:
    data = scenario_data()
    data["evidence_class"] = "engineering"
    with pytest.raises(ValidationError, match="require sourced inputs"):
        ThermalScenarioV1.model_validate(data)


def test_required_physical_fields_do_not_receive_implicit_defaults() -> None:
    data = scenario_data()
    data["devices"][0]["contact_resistance"].pop("value_K_per_W")
    with pytest.raises(ValidationError, match="Field required"):
        ThermalScenarioV1.model_validate(data)


def test_result_margin_residual_and_device_order_are_consistent() -> None:
    data = {
        "schema_version": "thermal-result/v1",
        "scenario_schema_version": "thermal-scenario/v1",
        "scenario_id": "synthetic-shared-sink",
        "device_order": ["SYNTH-Q1"],
        "devices": [
            {
                "device_id": "SYNTH-Q1",
                "baseplate_temperature_K": 330.0,
                "baseplate_temperature_sampling": "area_weighted_mean_over_thermal_contact_footprint",
                "case_bottom_temperature_K": 331.5,
                "junction_temperature_K": 343.5,
                "junction_temperature_interpretation": "steady_state_estimate",
                "junction_limit_K": 423.15,
                "margin_K": 79.65,
                "constraint_residual_K": -79.65,
                "constraint_status": "satisfied",
                "validity_status": "valid",
            }
        ],
        "convergence_status": "converged",
        "validity_status": "valid",
        "heat_balance": {
            "heat_input_W": 30.0,
            "heat_rejected_W": 30.0,
            "residual_W": 0.0,
            "relative_error": 0.0,
        },
        "backend": {
            "backend_id": "synthetic-contract-only",
            "status": "completed",
            "assumptions": ["no solver executed by this contract test"],
        },
    }
    result = ThermalResultV1.model_validate(data)
    assert result.device_order == [record.device_id for record in result.devices]

    reversed_result = deepcopy(data)
    reversed_result["devices"][0]["device_id"] = "SYNTH-Q2"
    with pytest.raises(ValidationError, match="exactly the declared device_order"):
        ThermalResultV1.model_validate(reversed_result)


def test_rtheta_ja_is_a_junction_to_ambient_observation() -> None:
    data = scenario_data()
    data["devices"][0]["observed_metrics"] = [
        {
            "metric": "RthetaJA",
            "value_K_per_W": 24.0,
            "from_surface": "junction",
            "to_surface": "ambient_air",
            "test_conditions": "synthetic board-level test description",
            "provenance": "synthetic observation only",
        }
    ]
    scenario = ThermalScenarioV1.model_validate(data)
    observation = scenario.devices[0].observed_metrics[0]
    assert observation.metric == "RthetaJA"
    assert observation.to_surface == "ambient_air"


def test_heat_balance_residual_and_relative_error_are_auditable() -> None:
    balance = HeatBalanceV1(
        heat_input_W=30.0,
        heat_rejected_W=29.0,
        residual_W=1.0,
        relative_error=1.0 / 30.0,
    )
    assert balance.residual_W == 1.0
    with pytest.raises(ValidationError, match="residual_W must equal"):
        HeatBalanceV1(
            heat_input_W=30.0,
            heat_rejected_W=29.0,
            residual_W=0.0,
            relative_error=0.0,
        )


def test_rtheta_ja_cannot_occupy_the_rjc_network_field() -> None:
    data = scenario_data()
    data["devices"][0]["r_theta_jc"]["metric"] = "RthetaJA"
    with pytest.raises(ValidationError):
        ThermalScenarioV1.model_validate(data)

def _location_contains_field_path(location: tuple[object, ...], path: tuple[object, ...]) -> bool:
    parts = iter(location)
    return all(any(part == candidate for candidate in parts) for part in path)


@pytest.mark.parametrize(
    ("path", "expected_loc"),
    [
        (("scenario_id",), ("scenario_id",)),
        (("baseplate", "material_id"), ("baseplate", "material_id")),
        (("baseplate", "material_provenance"), ("baseplate", "material_provenance")),
        (("sink", "baseplate_to_sink_contact", "provenance"), ("sink", "baseplate_to_sink_contact", "provenance")),
        (("sink", "r_theta_sa", "operating_conditions"), ("sink", "r_theta_sa", "operating_conditions")),
        (("sink", "r_theta_sa", "provenance"), ("sink", "r_theta_sa", "provenance")),
        (("devices", 0, "id"), ("devices", 0, "id")),
        (("devices", 0, "geometry_provenance"), ("devices", 0, "geometry_provenance")),
        (("devices", 0, "r_theta_jc", "test_conditions"), ("devices", 0, "r_theta_jc", "test_conditions")),
        (("devices", 0, "r_theta_jc", "provenance"), ("devices", 0, "r_theta_jc", "provenance")),
        (("devices", 0, "contact_resistance", "provenance"), ("devices", 0, "contact_resistance", "provenance")),
        (("devices", 0, "junction_limit_provenance"), ("devices", 0, "junction_limit_provenance")),
        (("assumptions", 0), ("assumptions", 0)),
        (("devices", 0, "observed_metrics", 0, "test_conditions"), ("devices", 0, "observed_metrics", 0, "test_conditions")),
        (("devices", 0, "observed_metrics", 0, "provenance"), ("devices", 0, "observed_metrics", 0, "provenance")),
    ],
)
def test_mandatory_scenario_text_rejects_whitespace_only_with_field_location(
    path: tuple[str | int, ...], expected_loc: tuple[str | int, ...]
) -> None:
    data = scenario_data()
    data["devices"][0]["observed_metrics"] = [
        {
            "metric": "PsiJT",
            "value_K_per_W": 0.6,
            "from_surface": "junction",
            "to_surface": "package_top_center",
            "test_conditions": "synthetic observation conditions",
            "provenance": "synthetic observation source",
        }
    ]
    target = data
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = " \t\n "

    with pytest.raises(ValidationError) as exc_info:
        ThermalScenarioV1.model_validate(data)

    assert any(
        _location_contains_field_path(error["loc"], expected_loc)
        and "must contain non-whitespace text" in error["msg"]
        for error in exc_info.value.errors()
    )


def test_engineering_scenario_rejects_whitespace_only_provenance() -> None:
    data = scenario_data()
    data["evidence_class"] = "engineering"
    data["baseplate"]["material_provenance"] = " \t "

    with pytest.raises(ValidationError) as exc_info:
        ThermalScenarioV1.model_validate(data)

    assert any(
        error["loc"] == ("baseplate", "material_provenance")
        for error in exc_info.value.errors()
    )


def test_nonblank_contract_text_is_preserved_verbatim() -> None:
    data = scenario_data()
    data["scenario_id"] = "  run id  "
    data["baseplate"]["material_provenance"] = "  datasheet reference  "
    data["sink"]["r_theta_sa"]["operating_conditions"] = "  still air at 25 C  "

    scenario = ThermalScenarioV1.model_validate(data)

    assert scenario.scenario_id == "  run id  "
    assert scenario.baseplate.material_provenance == "  datasheet reference  "
    assert scenario.sink.r_theta_sa.operating_conditions == "  still air at 25 C  "


@pytest.mark.parametrize("orientation", [False, True])
def test_boolean_orientation_is_rejected(orientation: bool) -> None:
    data = scenario_data()
    data["devices"][0]["orientation_deg"] = orientation

    with pytest.raises(ValidationError) as exc_info:
        ThermalScenarioV1.model_validate(data)

    assert any(
        error["loc"] == ("devices", 0, "orientation_deg")
        and "not a boolean" in error["msg"]
        for error in exc_info.value.errors()
    )


@pytest.mark.parametrize("orientation", [0, 90, 180, 270])
def test_integer_cardinal_orientations_remain_valid(orientation: int) -> None:
    data = scenario_data()
    data["devices"][0]["orientation_deg"] = orientation

    scenario = ThermalScenarioV1.model_validate(data)

    assert scenario.devices[0].orientation_deg == orientation


@pytest.mark.parametrize(
    ("path", "expected_loc"),
    [
        (("scenario_id",), ("scenario_id",)),
        (("device_order", 0), ("device_order", 0)),
        (("devices", 0, "device_id"), ("devices", 0, "device_id")),
        (("backend", "backend_id"), ("backend", "backend_id")),
        (("backend", "assumptions", 0), ("backend", "assumptions", 0)),
    ],
)
def test_result_mandatory_text_rejects_whitespace_only_with_field_location(
    path: tuple[str | int, ...], expected_loc: tuple[str | int, ...]
) -> None:
    data = {
        "schema_version": "thermal-result/v1",
        "scenario_schema_version": "thermal-scenario/v1",
        "scenario_id": "scenario-1",
        "device_order": ["Q1"],
        "devices": [
            {
                "device_id": "Q1",
                "baseplate_temperature_K": 300.0,
                "baseplate_temperature_sampling": "area_weighted_mean_over_thermal_contact_footprint",
                "case_bottom_temperature_K": 301.0,
                "junction_temperature_K": 310.0,
                "junction_temperature_interpretation": "steady_state_estimate",
                "junction_limit_K": 400.0,
                "margin_K": 90.0,
                "constraint_residual_K": -90.0,
                "constraint_status": "satisfied",
                "validity_status": "valid",
            }
        ],
        "convergence_status": "converged",
        "validity_status": "valid",
        "heat_balance": {
            "heat_input_W": 0.0,
            "heat_rejected_W": 0.0,
            "residual_W": 0.0,
            "relative_error": 0.0,
        },
        "backend": {
            "backend_id": "test-backend",
            "status": "completed",
            "assumptions": ["no extra assumptions"],
        },
    }
    target = data
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = " \t "

    with pytest.raises(ValidationError) as exc_info:
        ThermalResultV1.model_validate(data)

    assert any(
        _location_contains_field_path(error["loc"], expected_loc)
        and "must contain non-whitespace text" in error["msg"]
        for error in exc_info.value.errors()
    )