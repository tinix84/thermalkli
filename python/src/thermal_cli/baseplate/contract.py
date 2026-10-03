"""Versioned scenario and result contracts for shared-baseplate analysis.

The contract describes inputs and result semantics. It deliberately does not
implement or imply a solver backend.
"""

from __future__ import annotations

import math
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


FiniteFloat = Annotated[float, Field(strict=True, allow_inf_nan=False)]
PositiveFloat = Annotated[float, Field(strict=True, gt=0, allow_inf_nan=False)]
NonNegativeFloat = Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)]
PositiveInt = Annotated[int, Field(strict=True, ge=2)]
def _require_nonblank_text(value: str) -> str:
    if not value.strip():
        raise ValueError("must contain non-whitespace text")
    return value


NonEmptyString = Annotated[
    str,
    Field(strict=True, min_length=1),
    AfterValidator(_require_nonblank_text),
]


AbsoluteTemperatureK = Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)]


class ContractModel(BaseModel):
    """Shared strictness for versioned public contract models."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ScenarioUnits(ContractModel):
    length: Literal["m"]
    power: Literal["W"]
    resistance: Literal["K/W"]
    temperature: Literal["K"]
    temperature_difference: Literal["K"]


class BaseplateSpec(ContractModel):
    length_x_m: PositiveFloat
    length_y_m: PositiveFloat
    thickness_m: PositiveFloat
    conductivity_W_mK: PositiveFloat
    material_id: NonEmptyString
    material_provenance: NonEmptyString
    grid_points_x: PositiveInt
    grid_points_y: PositiveInt


class RThetaSASpec(ContractModel):
    metric: Literal["RthetaSA"]
    value_K_per_W: PositiveFloat
    from_surface: Literal["heatsink_base"]
    to_surface: Literal["ambient_air"]
    reference_temperature_K: AbsoluteTemperatureK
    operating_conditions: NonEmptyString
    provenance: NonEmptyString
    spatial_approximation: Literal["uniform_area_extraction"]


class BaseplateSinkMountingSpec(ContractModel):
    metric: Literal["Rmount"]
    value_K_per_W: NonNegativeFloat
    from_surface: Literal["baseplate_bottom"]
    to_surface: Literal["heatsink_base"]
    provenance: NonEmptyString


class SinkSpec(ContractModel):
    baseplate_to_sink_contact: BaseplateSinkMountingSpec
    r_theta_sa: RThetaSASpec


class RThetaJCSpec(ContractModel):
    metric: Literal["RthetaJC"]
    value_K_per_W: PositiveFloat
    from_surface: Literal["junction"]
    to_surface: Literal["package_case_bottom"]
    test_conditions: NonEmptyString
    provenance: NonEmptyString


class RThetaJAObservation(ContractModel):
    metric: Literal["RthetaJA"]
    value_K_per_W: PositiveFloat
    from_surface: Literal["junction"]
    to_surface: Literal["ambient_air"]
    test_conditions: NonEmptyString
    provenance: NonEmptyString


class PsiJTObservation(ContractModel):
    metric: Literal["PsiJT"]
    value_K_per_W: PositiveFloat
    from_surface: Literal["junction"]
    to_surface: Literal["package_top_center"]
    test_conditions: NonEmptyString
    provenance: NonEmptyString


MetricObservation = RThetaJAObservation | PsiJTObservation


class RectangularGeometry(ContractModel):
    width_m: PositiveFloat
    height_m: PositiveFloat


class ContactResistanceSpec(ContractModel):
    metric: Literal["Rcontact"]
    value_K_per_W: NonNegativeFloat
    from_surface: Literal["package_case_bottom"]
    to_surface: Literal["baseplate_top"]
    included_path: Literal["case_bottom_to_baseplate_top_once"]
    provenance: NonEmptyString


class DeviceSpec(ContractModel):
    id: NonEmptyString
    center_x_m: FiniteFloat
    center_y_m: FiniteFloat
    orientation_deg: Literal[0, 90, 180, 270]

    @field_validator("orientation_deg", mode="before")
    @classmethod
    def reject_boolean_orientation(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("orientation_deg must be an integer cardinal angle, not a boolean")
        return value
    package_envelope: RectangularGeometry
    thermal_contact_footprint: RectangularGeometry
    mounting_clearance_m: NonNegativeFloat
    geometry_provenance: NonEmptyString
    power_W: NonNegativeFloat
    r_theta_jc: RThetaJCSpec
    contact_resistance: ContactResistanceSpec
    junction_limit_K: AbsoluteTemperatureK
    junction_limit_provenance: NonEmptyString
    observed_metrics: list[MetricObservation]


class ThermalScenarioV1(ContractModel):
    """Complete input for a steady-state shared-baseplate evaluation."""

    schema_version: Literal["thermal-scenario/v1"]
    scenario_id: NonEmptyString
    evidence_class: Literal["synthetic", "engineering", "legacy_unverified"]
    coordinate_origin: Literal["lower_left_baseplate_corner"]
    units: ScenarioUnits
    baseplate: BaseplateSpec
    sink: SinkSpec
    devices: Annotated[list[DeviceSpec], Field(min_length=1)]
    assumptions: list[NonEmptyString]

    @model_validator(mode="after")
    def validate_layout_and_evidence(self) -> ThermalScenarioV1:
        ids = [device.id for device in self.devices]
        if len(ids) != len(set(ids)):
            raise ValueError("device IDs must be unique")

        bounds: list[tuple[float, float, float, float, str]] = []
        for device in self.devices:
            package_width = device.package_envelope.width_m
            package_height = device.package_envelope.height_m
            contact_width = device.thermal_contact_footprint.width_m
            contact_height = device.thermal_contact_footprint.height_m
            if device.orientation_deg in (90, 270):
                package_width, package_height = package_height, package_width
                contact_width, contact_height = contact_height, contact_width

            if contact_width > package_width or contact_height > package_height:
                raise ValueError(
                    f"device {device.id!r} thermal contact footprint must fit its package envelope"
                )

            half_width = package_width / 2 + device.mounting_clearance_m
            half_height = package_height / 2 + device.mounting_clearance_m
            x_min = device.center_x_m - half_width
            x_max = device.center_x_m + half_width
            y_min = device.center_y_m - half_height
            y_max = device.center_y_m + half_height
            if (
                x_min < 0
                or y_min < 0
                or x_max > self.baseplate.length_x_m
                or y_max > self.baseplate.length_y_m
            ):
                raise ValueError(
                    f"device {device.id!r} package and mounting clearance must fit the baseplate"
                )
            bounds.append((x_min, x_max, y_min, y_max, device.id))

        for index, first in enumerate(bounds):
            for second in bounds[index + 1 :]:
                if (
                    first[0] < second[1]
                    and second[0] < first[1]
                    and first[2] < second[3]
                    and second[2] < first[3]
                ):
                    raise ValueError(
                        "package envelopes and mounting clearances overlap: "
                        f"{first[4]!r} and {second[4]!r}"
                    )

        if self.evidence_class == "engineering":
            evidence = [
                self.baseplate.material_provenance,
                self.sink.baseplate_to_sink_contact.provenance,
                self.sink.r_theta_sa.operating_conditions,
                self.sink.r_theta_sa.provenance,
                *self.assumptions,
            ]
            for device in self.devices:
                evidence.extend(
                    [
                        device.geometry_provenance,
                        device.contact_resistance.provenance,
                        device.junction_limit_provenance,
                        device.r_theta_jc.test_conditions,
                        device.r_theta_jc.provenance,
                    ]
                )
                for metric in device.observed_metrics:
                    evidence.extend([metric.test_conditions, metric.provenance])
            incomplete_markers = ("unknown", "unspecified", "synthetic", "legacy")
            if any(
                marker in item.lower()
                for item in evidence
                for marker in incomplete_markers
            ):
                raise ValueError(
                    "engineering scenarios require sourced inputs and explicit operating conditions"
                )

        return self


class DeviceThermalResultV1(ContractModel):
    device_id: NonEmptyString
    baseplate_temperature_K: AbsoluteTemperatureK
    baseplate_temperature_sampling: Literal[
        "area_weighted_mean_over_thermal_contact_footprint"
    ]
    case_bottom_temperature_K: AbsoluteTemperatureK
    junction_temperature_K: AbsoluteTemperatureK
    junction_temperature_interpretation: Literal["steady_state_estimate"]
    junction_limit_K: AbsoluteTemperatureK
    margin_K: FiniteFloat
    constraint_residual_K: FiniteFloat
    constraint_status: Literal["satisfied", "violated"]
    validity_status: Literal["valid", "invalid", "out_of_domain"]

    @model_validator(mode="after")
    def validate_signed_constraint(self) -> DeviceThermalResultV1:
        expected_margin = self.junction_limit_K - self.junction_temperature_K
        expected_residual = self.junction_temperature_K - self.junction_limit_K
        if not math.isclose(self.margin_K, expected_margin, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("margin_K must equal junction_limit_K - junction_temperature_K")
        if not math.isclose(
            self.constraint_residual_K,
            expected_residual,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError(
                "constraint_residual_K must equal junction_temperature_K - junction_limit_K"
            )
        expected_status = "satisfied" if expected_residual <= 0 else "violated"
        if self.constraint_status != expected_status:
            raise ValueError("constraint_status must agree with the signed residual")
        return self


class HeatBalanceV1(ContractModel):
    heat_input_W: NonNegativeFloat
    heat_rejected_W: NonNegativeFloat
    residual_W: FiniteFloat
    relative_error: NonNegativeFloat

    @model_validator(mode="after")
    def validate_balance_values(self) -> HeatBalanceV1:
        expected_residual = self.heat_input_W - self.heat_rejected_W
        if not math.isclose(self.residual_W, expected_residual, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("residual_W must equal heat_input_W - heat_rejected_W")
        scale = max(self.heat_input_W, self.heat_rejected_W)
        expected_relative_error = abs(expected_residual) / scale if scale else 0.0
        if not math.isclose(
            self.relative_error,
            expected_relative_error,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("relative_error must equal |residual_W| / max(input, rejected heat)")
        return self


class BackendStatusV1(ContractModel):
    backend_id: NonEmptyString
    status: Literal["not_run", "completed", "failed"]
    assumptions: list[NonEmptyString]


class ThermalResultV1(ContractModel):
    schema_version: Literal["thermal-result/v1"]
    scenario_schema_version: Literal["thermal-scenario/v1"]
    scenario_id: NonEmptyString
    device_order: list[NonEmptyString]
    devices: list[DeviceThermalResultV1]
    convergence_status: Literal["not_run", "converged", "not_converged"]
    validity_status: Literal["valid", "invalid", "out_of_domain"]
    heat_balance: HeatBalanceV1
    backend: BackendStatusV1

    @model_validator(mode="after")
    def validate_device_order(self) -> ThermalResultV1:
        ids = [device.device_id for device in self.devices]
        if len(self.device_order) != len(set(self.device_order)):
            raise ValueError("device_order IDs must be unique")
        if ids != self.device_order:
            raise ValueError("device results must appear in exactly the declared device_order")
        return self


def celsius_to_kelvin(temperature_c: float) -> float:
    """Convert a finite Celsius absolute temperature to Kelvin."""
    if isinstance(temperature_c, bool) or not isinstance(temperature_c, (int, float)):
        raise ValueError("Celsius temperature must be a finite number")
    if not math.isfinite(temperature_c):
        raise ValueError("Celsius temperature must be finite")
    temperature_k = float(temperature_c) + 273.15
    if temperature_k < 0:
        raise ValueError("Celsius temperature cannot be below absolute zero")
    return temperature_k


def kelvin_to_celsius(temperature_k: float) -> float:
    """Convert a finite Kelvin absolute temperature to Celsius."""
    if isinstance(temperature_k, bool) or not isinstance(temperature_k, (int, float)):
        raise ValueError("Kelvin temperature must be a finite number")
    if not math.isfinite(temperature_k):
        raise ValueError("Kelvin temperature must be finite")
    if temperature_k < 0:
        raise ValueError("Kelvin temperature cannot be below absolute zero")
    return float(temperature_k) - 273.15
