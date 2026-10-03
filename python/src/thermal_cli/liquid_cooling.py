"""Pump-limited liquid cooling primitives with explicit loop boundaries."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise
from typing import Protocol

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import brentq


class LiquidFluid(Protocol):
    def density(self, temperature: float) -> float: ...
    def dynamic_viscosity(self, temperature: float) -> float: ...
    def thermal_conductivity(self, temperature: float) -> float: ...
    def specific_heat_cp(self, temperature: float) -> float: ...


@dataclass(frozen=True)
class ConstantLiquidProperties:
    """Source-condition properties where no validated temperature table exists."""

    density_kg_m3: float
    dynamic_viscosity_pa_s: float
    thermal_conductivity_w_mk: float
    specific_heat_j_kgk: float
    reference_temperature_k: float
    provenance: str

    def __post_init__(self) -> None:
        for name in (
            "density_kg_m3",
            "dynamic_viscosity_pa_s",
            "thermal_conductivity_w_mk",
            "specific_heat_j_kgk",
            "reference_temperature_k",
        ):
            _finite(name, getattr(self, name), positive=True)
        if not self.provenance.strip():
            raise ValueError("provenance must identify the property source")

    def _check_temperature(self, temperature: float) -> None:
        _finite("temperature_k", temperature, positive=True)
        if temperature != self.reference_temperature_k:
            raise ValueError(
                "constant properties are only valid at their declared reference temperature"
            )

    @property
    def temperature_range_k(self) -> tuple[float, float]:
        return self.reference_temperature_k, self.reference_temperature_k

    def density(self, temperature: float) -> float:
        self._check_temperature(temperature)
        return self.density_kg_m3

    def dynamic_viscosity(self, temperature: float) -> float:
        self._check_temperature(temperature)
        return self.dynamic_viscosity_pa_s

    def thermal_conductivity(self, temperature: float) -> float:
        self._check_temperature(temperature)
        return self.thermal_conductivity_w_mk

    def specific_heat_cp(self, temperature: float) -> float:
        self._check_temperature(temperature)
        return self.specific_heat_j_kgk


def _finite(name: str, value: float, *, positive: bool = False) -> float:
    value = float(value)
    if not math.isfinite(value) or (value <= 0.0 if positive else value < 0.0):
        op = "> 0" if positive else ">= 0"
        raise ValueError(f"{name} must be finite and {op}")
    return value


def _count(name: str, value: int) -> int:
    if isinstance(value, bool) or int(value) != value or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


@dataclass(frozen=True)
class PumpCurve:
    """Available pressure versus total loop flow, with a bounded SI domain."""

    flow_m3_s: NDArray[np.float64]
    pressure_pa: NDArray[np.float64]
    provenance: str = "user-supplied"

    def __post_init__(self) -> None:
        q = np.asarray(self.flow_m3_s, dtype=float)
        p = np.asarray(self.pressure_pa, dtype=float)
        if q.ndim != 1 or p.ndim != 1 or len(q) != len(p) or len(q) < 2:
            raise ValueError("pump curve requires at least two paired one-dimensional points")
        if (
            not np.all(np.isfinite(q))
            or not np.all(np.isfinite(p))
            or np.any(q < 0)
            or np.any(p < 0)
        ):
            raise ValueError("pump curve points must be finite and nonnegative")
        if np.any(np.diff(q) <= 0):
            raise ValueError("pump curve flow points must be strictly increasing")
        q, p = q.copy(), p.copy()
        q.setflags(write=False)
        p.setflags(write=False)
        object.__setattr__(self, "flow_m3_s", q)
        object.__setattr__(self, "pressure_pa", p)

    @property
    def domain_m3_s(self) -> tuple[float, float]:
        return float(self.flow_m3_s[0]), float(self.flow_m3_s[-1])

    def pressure_at(self, flow_m3_s: float) -> float:
        q = _finite("flow_m3_s", flow_m3_s)
        lo, hi = self.domain_m3_s
        if q < lo or q > hi:
            raise ValueError(f"flow {q:g} is outside pump curve domain [{lo:g}, {hi:g}]")
        return float(np.interp(q, self.flow_m3_s, self.pressure_pa))


def pesc2004_b05_curve(sample_count: int = 257) -> PumpCurve:
    """PESC 2004 Eq. 1 measured available-system curve; Q is in m^3/s."""
    if isinstance(sample_count, bool) or int(sample_count) != sample_count or sample_count < 2:
        raise ValueError("sample_count must be an integer >= 2")
    a, b, c = 13.88e12, 148.3e6, 14.7e3
    qmax = (-b + math.sqrt(b * b + 4.0 * a * c)) / (2.0 * a)
    q = np.linspace(0.0, qmax, int(sample_count))
    p = c - b * q - a * q**2
    p[-1] = 0.0
    return PumpCurve(q, p, "Drofenik et al., PESC 2004, Eq. 1")


@dataclass(frozen=True)
class MeasuredLiquidCoolingObservation:
    case_id: str
    source: str
    flow_m3_s: float
    pressure_pa: float
    thermal_resistance_k_w: float
    thermal_reference: str
    conditions: str

    def __post_init__(self) -> None:
        for name in ("flow_m3_s", "pressure_pa", "thermal_resistance_k_w"):
            _finite(name, getattr(self, name), positive=True)
        if not all(
            (
                self.case_id.strip(),
                self.source.strip(),
                self.thermal_reference.strip(),
                self.conditions.strip(),
            )
        ):
            raise ValueError("observation provenance and conditions are required")


# Approximate source values; retained as measured observations, not predictions.
TPEL2005_B06_OBSERVATION = MeasuredLiquidCoolingObservation(
    case_id="B06",
    source="Drofenik et al., IEEE TPEL 2005, conclusion",
    flow_m3_s=1.2e-3 / 60.0,
    pressure_pa=80.0e2,
    thermal_resistance_k_w=0.10,
    thermal_reference="baseplate-to-coolant reference reported by the source",
    conditions=(
        "approximately 80 mbar, 1.2 L/min, and 0.10 K/W; 25 x 34 mm baseplate; "
        "preserve measured/source basis and do not label as this model's prediction"
    ),
)


@dataclass(frozen=True)
class CircularChannel:
    length_m: float
    diameter_m: float
    roughness_m: float = 0.0
    minor_loss_k: float = 0.0

    def __post_init__(self) -> None:
        _finite("length_m", self.length_m, positive=True)
        _finite("diameter_m", self.diameter_m, positive=True)
        _finite("roughness_m", self.roughness_m)
        _finite("minor_loss_k", self.minor_loss_k)
        if self.roughness_m >= self.diameter_m:
            raise ValueError("roughness_m must be smaller than diameter_m")

    @property
    def area_m2(self) -> float:
        return math.pi * self.diameter_m**2 / 4.0

    @property
    def hydraulic_diameter_m(self) -> float:
        return self.diameter_m


@dataclass(frozen=True)
class SlotChannel:
    length_m: float
    width_m: float
    gap_m: float
    roughness_m: float = 0.0
    minor_loss_k: float = 0.0

    def __post_init__(self) -> None:
        for name in ("length_m", "width_m", "gap_m"):
            _finite(name, getattr(self, name), positive=True)
        _finite("roughness_m", self.roughness_m)
        _finite("minor_loss_k", self.minor_loss_k)
        if self.roughness_m >= min(self.width_m, self.gap_m):
            raise ValueError("roughness_m must be smaller than both slot dimensions")

    @property
    def area_m2(self) -> float:
        return self.width_m * self.gap_m

    @property
    def hydraulic_diameter_m(self) -> float:
        return 2.0 * self.width_m * self.gap_m / (self.width_m + self.gap_m)


@dataclass(frozen=True)
class CalibratedPortLoss:
    """Separate empirical loss: a_q2*Q_branch^2 + b_v2*(Q_branch/A)^2."""

    a_q2_pa_s2_m6: float
    b_v2_pa_s2_m2: float
    calibration_reference: str

    def __post_init__(self) -> None:
        _finite("a_q2_pa_s2_m6", self.a_q2_pa_s2_m6)
        _finite("b_v2_pa_s2_m2", self.b_v2_pa_s2_m2)
        if not self.calibration_reference.strip():
            raise ValueError("calibration_reference must identify the calibration")

    @classmethod
    def pesc2004(cls) -> CalibratedPortLoss:
        """PESC 2004 Eqs. 11-13 fit for its unchanged inlet/outlet geometry."""
        return cls(
            8.3e12,
            130.0,
            "Drofenik et al., PESC 2004, Eqs. 11-13; fitted c=0.35 and 2.5 mm",
        )

    def pressure_drop_pa(self, flow_m3_s: float, channel_area_m2: float) -> float:
        q = _finite("flow_m3_s", flow_m3_s)
        area = _finite("channel_area_m2", channel_area_m2, positive=True)
        return self.a_q2_pa_s2_m6 * q**2 + self.b_v2_pa_s2_m2 * (q / area) ** 2


@dataclass(frozen=True)
class ChannelHydraulicState:
    total_flow_m3_s: float
    per_channel_flow_m3_s: float
    channel_count: int
    reynolds: float
    velocity_m_s: float
    friction_factor_darcy: float
    friction_pressure_drop_pa: float
    minor_pressure_drop_pa: float
    calibrated_pressure_drop_pa: float
    pressure_drop_pa: float


@dataclass(frozen=True)
class OperatingPoint:
    status: str
    total_flow_m3_s: float | None
    pressure_pa: float | None
    channel_state: ChannelHydraulicState | None
    reason: str | None = None


def channel_hydraulic_state(
    *,
    geometry: CircularChannel | SlotChannel,
    total_flow_m3_s: float,
    channel_count: int,
    fluid: LiquidFluid,
    temperature_k: float,
    calibrated_port_loss: CalibratedPortLoss | None = None,
) -> ChannelHydraulicState:
    """Compute pressure balance; total flow divides evenly across parallel channels."""
    q_total = _finite("total_flow_m3_s", total_flow_m3_s)
    n = _count("channel_count", channel_count)
    _finite("temperature_k", temperature_k, positive=True)
    q = q_total / n
    rho, mu = fluid.density(temperature_k), fluid.dynamic_viscosity(temperature_k)
    area, dh = geometry.area_m2, geometry.hydraulic_diameter_m
    velocity = q / area
    re = rho * velocity * dh / mu
    f = _darcy_factor(re, geometry, dh)
    dp_f = f * geometry.length_m / dh * rho * velocity**2 / 2.0
    dp_m = geometry.minor_loss_k * rho * velocity**2 / 2.0
    dp_c = calibrated_port_loss.pressure_drop_pa(q, area) if calibrated_port_loss else 0.0
    return ChannelHydraulicState(
        q_total, q, n, re, velocity, f, dp_f, dp_m, dp_c, dp_f + dp_m + dp_c
    )


def solve_operating_point(
    *,
    pump_curve: PumpCurve,
    geometry: CircularChannel | SlotChannel,
    channel_count: int,
    fluid: LiquidFluid,
    temperature_k: float,
    calibrated_port_loss: CalibratedPortLoss | None = None,
) -> OperatingPoint:
    """Intersect measured/system pressure with channel loss, inside curve domain only."""
    lo, hi = pump_curve.domain_m3_s

    def residual(q: float) -> float:
        loss = channel_hydraulic_state(
            geometry=geometry,
            total_flow_m3_s=q,
            channel_count=channel_count,
            fluid=fluid,
            temperature_k=temperature_k,
            calibrated_port_loss=calibrated_port_loss,
        ).pressure_drop_pa
        return pump_curve.pressure_at(q) - loss

    points = np.unique(np.concatenate((pump_curve.flow_m3_s, np.linspace(lo, hi, 257))))
    root: float | None = None
    for q0, q1 in pairwise(points):
        r0, r1 = residual(float(q0)), residual(float(q1))
        if r0 == 0.0:
            root = float(q0)
            break
        if r0 * r1 < 0.0:
            root = float(brentq(residual, float(q0), float(q1)))
            break
        if r1 == 0.0:
            root = float(q1)
            break
    if root is None:
        return OperatingPoint(
            "no_intersection",
            None,
            None,
            None,
            "pump and system curves do not intersect within the pump-curve domain",
        )
    state = channel_hydraulic_state(
        geometry=geometry,
        total_flow_m3_s=root,
        channel_count=channel_count,
        fluid=fluid,
        temperature_k=temperature_k,
        calibrated_port_loss=calibrated_port_loss,
    )
    return OperatingPoint("ok", root, state.pressure_drop_pa, state)


@dataclass(frozen=True)
class LiquidEnergyResult:
    status: str
    heat_w: float
    flow_m3_s: float
    mass_flow_kg_s: float | None
    cp_j_kgk: float | None
    density_kg_m3: float | None
    inlet_temperature_k: float
    outlet_temperature_k: float | None
    temperature_rise_k: float | None
    energy_recovered_w: float | None
    reason: str | None = None


def liquid_energy_balance(
    *,
    heat_w: float,
    flow_m3_s: float,
    inlet_temperature_k: float,
    fluid: LiquidFluid,
) -> LiquidEnergyResult:
    """Solve Q=m_dot*cp(T_mean)*(Tout-Tin), with rho and cp temperature-dependent."""
    qheat = _finite("heat_w", heat_w)
    flow = _finite("flow_m3_s", flow_m3_s)
    tin = _finite("inlet_temperature_k", inlet_temperature_k, positive=True)
    temperature_range = getattr(fluid, "temperature_range_k", None)
    if temperature_range is not None:
        lower_temperature, upper_temperature = temperature_range
        if tin < lower_temperature or tin > upper_temperature:
            return LiquidEnergyResult(
                "invalid_temperature",
                qheat,
                flow,
                None,
                None,
                None,
                tin,
                None,
                None,
                None,
                f"inlet temperature {tin:g} K is outside fluid range "
                f"[{lower_temperature:g}, {upper_temperature:g}] K",
            )
    if flow == 0.0:
        valid_zero = qheat == 0.0
        return LiquidEnergyResult(
            "no_flow" if valid_zero else "invalid_flow",
            qheat,
            flow,
            None,
            None,
            None,
            tin,
            tin if valid_zero else None,
            0.0 if valid_zero else None,
            0.0 if valid_zero else None,
            None if valid_zero else "positive heat requires positive liquid flow",
        )
    tout = tin
    for _ in range(100):
        tmean = (tin + tout) / 2.0
        if temperature_range is not None and not (
            temperature_range[0] <= tmean <= temperature_range[1]
        ):
            return LiquidEnergyResult(
                "invalid_temperature",
                qheat,
                flow,
                None,
                None,
                None,
                tin,
                tout,
                tout - tin,
                None,
                f"mean fluid temperature {tmean:g} K is outside fluid range "
                f"[{temperature_range[0]:g}, {temperature_range[1]:g}] K",
            )
        try:
            cp, rho = fluid.specific_heat_cp(tmean), fluid.density(tmean)
        except ValueError as exc:
            return LiquidEnergyResult(
                "invalid_properties",
                qheat,
                flow,
                None,
                None,
                None,
                tin,
                None,
                None,
                None,
                str(exc),
            )
        updated = tin + qheat / (rho * flow * cp)
        if not math.isfinite(updated):
            raise ValueError("energy balance produced non-finite outlet temperature")
        if temperature_range is not None and not (
            temperature_range[0] <= updated <= temperature_range[1]
        ):
            mdot = rho * flow
            recovered = mdot * cp * (updated - tin)
            return LiquidEnergyResult(
                "invalid_temperature",
                qheat,
                flow,
                mdot,
                cp,
                rho,
                tin,
                updated,
                updated - tin,
                recovered,
                f"outlet temperature {updated:g} K is outside fluid range "
                f"[{temperature_range[0]:g}, {temperature_range[1]:g}] K",
            )
        if abs(updated - tout) <= max(1e-10, abs(updated) * 1e-12):
            tout = updated
            break
        tout = updated
    else:
        raise ValueError("temperature-dependent energy balance did not converge")
    tmean = (tin + tout) / 2.0
    cp, rho = fluid.specific_heat_cp(tmean), fluid.density(tmean)
    mdot = rho * flow
    recovered = mdot * cp * (tout - tin)
    return LiquidEnergyResult("ok", qheat, flow, mdot, cp, rho, tin, tout, tout - tin, recovered)


def ideal_slot_resistance_k_w(
    *, geometry: SlotChannel, flow_m3_s: float, fluid: LiquidFluid, mean_temperature_k: float
) -> float:
    """One-channel hot-plate-to-bulk resistance; excludes port/contact paths."""
    q = _finite("flow_m3_s", flow_m3_s)
    temp = _finite("mean_temperature_k", mean_temperature_k, positive=True)
    if q == 0.0:
        raise ValueError("positive flow is required for finite slot resistance")
    rho, mu = fluid.density(temp), fluid.dynamic_viscosity(temp)
    cp, conductivity = fluid.specific_heat_cp(temp), fluid.thermal_conductivity(temp)
    velocity = q / geometry.area_m2
    re_l = velocity * geometry.length_m * rho / mu
    pr = cp * mu / conductivity
    if re_l <= 0.0 or pr <= 0.0:
        raise ValueError("fluid properties and flow must yield positive Re and Pr")
    nu_lam = 0.664 * math.sqrt(re_l) * pr ** (1.0 / 3.0)
    nu_turb = 0.037 * re_l**0.8 * pr / (1.0 + 2.443 * re_l**-0.1 * (pr ** (2.0 / 3.0) - 1.0))
    nu = math.hypot(nu_lam, nu_turb)
    h = nu * conductivity / geometry.length_m
    return 1.0 / (h * geometry.length_m * geometry.width_m)


def calibrated_slot_resistance_k_w(*, ideal_slot_rth_k_w: float, flow_area_rth_k_w: float) -> float:
    """Combine whole-plate slot and inlet/outlet-area paths to mean coolant."""

    a = _finite("ideal_slot_rth_k_w", ideal_slot_rth_k_w, positive=True)
    b = _finite("flow_area_rth_k_w", flow_area_rth_k_w, positive=True)
    return 1.0 / (1.0 / a + 1.0 / b)


def pesc2004_b05_flow_area_resistance_k_w(geometry: SlotChannel) -> float:
    """Return the PESC 2004 Sec. 2.4.2 CFD fit for inlet/outlet flow area."""
    return 0.4 if geometry.gap_m > 1.2e-3 else 1.0


@dataclass(frozen=True)
class LiquidLoopVolume:
    """Volume ledger keeps cold plate distinct from pump, pipes, and exchanger."""

    cold_plate_m3: float
    pump_m3: float = 0.0
    pipes_m3: float = 0.0
    heat_exchanger_m3: float = 0.0

    def __post_init__(self) -> None:
        for name in ("cold_plate_m3", "pump_m3", "pipes_m3", "heat_exchanger_m3"):
            _finite(name, getattr(self, name))

    @property
    def auxiliary_m3(self) -> float:
        return self.pump_m3 + self.pipes_m3 + self.heat_exchanger_m3

    @property
    def system_m3(self) -> float:
        return self.cold_plate_m3 + self.auxiliary_m3

    @property
    def cold_plate_l(self) -> float:
        return self.cold_plate_m3 * 1000.0

    @property
    def system_l(self) -> float:
        return self.system_m3 * 1000.0


@dataclass(frozen=True)
class LiquidCoolerResult:
    operating_point: OperatingPoint
    energy: LiquidEnergyResult | None
    ideal_slot_wall_to_bulk_rth_k_w: float | None
    ideal_slot_to_inlet_rth_k_w: float | None
    calibrated_plate_to_inlet_rth_k_w: float | None
    volume: LiquidLoopVolume | None
    flow_area_rth_k_w: float | None = None


def evaluate_liquid_cooler(
    *,
    pump_curve: PumpCurve,
    geometry: CircularChannel | SlotChannel,
    fluid: LiquidFluid,
    inlet_temperature_k: float,
    heat_w: float,
    channel_count: int = 1,
    calibrated_port_loss: CalibratedPortLoss | None = None,
    flow_area_rth_k_w: float | None = None,
    volume: LiquidLoopVolume | None = None,
) -> LiquidCoolerResult:
    """Run bounded hydraulics, bulk balance, and optional slot heat-path estimates."""
    op = solve_operating_point(
        pump_curve=pump_curve,
        geometry=geometry,
        channel_count=channel_count,
        fluid=fluid,
        temperature_k=inlet_temperature_k,
        calibrated_port_loss=calibrated_port_loss,
    )
    if op.status != "ok" or op.total_flow_m3_s is None or op.channel_state is None:
        return LiquidCoolerResult(op, None, None, None, None, volume, flow_area_rth_k_w)
    energy = liquid_energy_balance(
        heat_w=heat_w,
        flow_m3_s=op.total_flow_m3_s,
        inlet_temperature_k=inlet_temperature_k,
        fluid=fluid,
    )
    ideal_local = ideal_inlet = calibrated = None
    if isinstance(geometry, SlotChannel) and energy.status == "ok":
        assert energy.outlet_temperature_k is not None
        assert energy.mass_flow_kg_s is not None and energy.cp_j_kgk is not None
        tmean = (inlet_temperature_k + energy.outlet_temperature_k) / 2.0
        branch_resistance = ideal_slot_resistance_k_w(
            geometry=geometry,
            flow_m3_s=op.channel_state.per_channel_flow_m3_s,
            fluid=fluid,
            mean_temperature_k=tmean,
        )
        ideal_local = branch_resistance / op.channel_state.channel_count
        bulk_rth = 0.5 / (energy.mass_flow_kg_s * energy.cp_j_kgk)
        ideal_inlet = ideal_local + bulk_rth
        if flow_area_rth_k_w is not None:
            calibrated = (
                calibrated_slot_resistance_k_w(
                    ideal_slot_rth_k_w=ideal_local,
                    flow_area_rth_k_w=flow_area_rth_k_w,
                )
                + bulk_rth
            )
    return LiquidCoolerResult(
        op, energy, ideal_local, ideal_inlet, calibrated, volume, flow_area_rth_k_w
    )


def _darcy_factor(re: float, geometry: CircularChannel | SlotChannel, dh: float) -> float:
    if re <= 0.0:
        return 0.0
    laminar_f_re = _laminar_darcy_re_product(geometry)
    if re < 2300.0:
        return laminar_f_re / re
    arg = (geometry.roughness_m / (3.7 * dh)) ** 1.11 + 6.9 / re
    f_turb = 1.0 / (-1.8 * math.log10(arg)) ** 2
    if re >= 4000.0:
        return f_turb
    f_lam = laminar_f_re / 2300.0
    return f_lam + (re - 2300.0) / 1700.0 * (f_turb - f_lam)


def _laminar_darcy_re_product(geometry: CircularChannel | SlotChannel) -> float:
    if isinstance(geometry, CircularChannel):
        return 64.0
    aspect = min(geometry.gap_m, geometry.width_m) / max(geometry.gap_m, geometry.width_m)
    return 96.0 * (
        1.0
        - 1.3553 * aspect
        + 1.9467 * aspect**2
        - 1.7012 * aspect**3
        + 0.9564 * aspect**4
        - 0.2537 * aspect**5
    )
