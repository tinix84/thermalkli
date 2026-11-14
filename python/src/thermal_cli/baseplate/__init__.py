"""2D multi-source baseplate analysis and versioned thermal contracts."""

from thermal_cli.baseplate.compare import compare_layouts
from thermal_cli.baseplate.contract import (
    BackendStatusV1,
    BaseplateSinkMountingSpec,
    BaseplateSpec,
    ContactResistanceSpec,
    DeviceSpec,
    DeviceThermalResultV1,
    HeatBalanceV1,
    PsiJTObservation,
    RThetaJAObservation,
    RThetaJCSpec,
    RThetaSASpec,
    ScenarioUnits,
    SinkSpec,
    ThermalResultV1,
    ThermalScenarioV1,
    celsius_to_kelvin,
    kelvin_to_celsius,
)
from thermal_cli.baseplate.fdm_solver import solve_fdm
from thermal_cli.baseplate.types import BaseplateConfig, BaseplateResult, Device

__all__ = [
    "BackendStatusV1",
    "BaseplateConfig",
    "BaseplateResult",
    "BaseplateSinkMountingSpec",
    "BaseplateSpec",
    "ContactResistanceSpec",
    "Device",
    "DeviceSpec",
    "DeviceThermalResultV1",
    "HeatBalanceV1",
    "PsiJTObservation",
    "RThetaJAObservation",
    "RThetaJCSpec",
    "RThetaSASpec",
    "ScenarioUnits",
    "SinkSpec",
    "ThermalResultV1",
    "ThermalScenarioV1",
    "celsius_to_kelvin",
    "compare_layouts",
    "kelvin_to_celsius",
    "solve_fdm",
]
