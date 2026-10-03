"""Bounded fan/channel optimizer and supplied-resistance CSPI utilities.

References
----------
Drofenik & Kolar, "Analyzing the Theoretical Limits of Forced Air-Cooling",
CIPS 2006 / PCC 2007.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real

import numpy as np

from thermal_cli.cspi.formulas import air_properties, channel_rth, cspi_calc
from thermal_cli.formula.fin import fin_efficiency


@dataclass
class CspiOptResult:
    """Result of a single CSPI optimisation run."""

    cspi: float  # [W/(K liter)]
    rth: float  # [K/W]
    vol: float  # [liters]
    n: int  # compatibility name for the number of parallel channels
    s: float  # optimal channel width [m]
    t: float  # fin thickness [m]
    re: float  # Reynolds number
    n_fan: float | None  # fan rpm; None when a supplied curve has no reference speed
    length: float  # heatsink length [m]
    v_max: float  # max fan flow [m^3/s]
    dp_max: float  # max fan pressure [Pa]
    feasible: bool  # bounded operating point and valid geometry
    operating_point_status: str = "not_evaluated"
    fan_curve_model: str = "not_evaluated"
    flow_rate_m3_s: float | None = None
    pressure_drop_pa: float | None = None
    fan_pressure_pa: float | None = None
    fin_spacing_ratio: float = 0.0
    fan_pressure_scale: float = 1.0
    auxiliary_power_w: float | None = None
    auxiliary_power_basis: str = "rated shaft power upper bound"
    temperature_reference_c: float = 80.0
    source_power_w: float = 0.0
    outlet_air_temperature_c: float | None = None
    face_count: int = 1  # heated faces; does not imply duplicated hydraulic channels
    hydraulic_branch_count: int = 1  # supported public geometry has one channel body
    r_face_k_w: float = float("inf")
    sink_volume_l: float = 0.0
    fan_volume_l: float = 0.0
    duct_volume_l: float = 0.0
    sink_material_bbox_l: float = 0.0
    fin_efficiency: float = 0.0
    fin_half_path_rth_k_w: float = float("inf")
    correlation: str = "rectangular smooth duct"
    pressure_correlation: str = "not_evaluated"
    heat_transfer_correlation: str = "not_evaluated"
    validity: tuple[str, ...] = ()

    @property
    def heated_face_count(self) -> int:
        """Number of thermally parallel heated faces."""
        return self.face_count

    @property
    def n_channels(self) -> int:
        """Number of parallel air channels in the selected geometry."""
        return self.n

    @property
    def n_fins(self) -> int:
        """Number of separator fins; fixed geometry assumes channels + 1 fins."""
        return self.n + 1


@dataclass
class CspiSweepResult:
    """Result of a 2-D CSPI parameter sweep."""

    cs: list[float]
    lambdas: list[float]
    cspi: np.ndarray  # shape (len(cs), len(lambdas))
    rth: np.ndarray  # shape (len(cs), len(lambdas))


def fin_half_path_resistance(
    *, fin_height_m: float, conductivity_w_mk: float, thickness_m: float, flow_length_m: float
) -> float:
    """Half-fin conduction path (height/2)/(k * thickness * flow_length)."""
    values = (fin_height_m, conductivity_w_mk, thickness_m, flow_length_m)
    if any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("fin path dimensions and conductivity must be finite and > 0")
    return fin_height_m / (2.0 * conductivity_w_mk * thickness_m * flow_length_m)


def _validated_count(name: str, value: int, minimum: int) -> int:
    """Accept integer-valued numeric counts, but never bools or fractions."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    numeric = float(value)
    if not math.isfinite(numeric) or not numeric.is_integer() or numeric < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(numeric)


def _validated_face_count(value: int) -> int:
    """Validate the one-face and symmetric two-face sink topologies modeled here."""
    count = _validated_count("face_count", value, 1)
    if count not in (1, 2):
        raise ValueError("face_count must be 1 or 2 for supported sink geometries")
    return count


def _validated_hydraulic_branch_count(value: int) -> int:
    """Reject multiple channel bodies until their thermal/volume topology is modeled."""
    count = _validated_count("hydraulic_branch_count", value, 1)
    if count != 1:
        raise ValueError(
            "hydraulic_branch_count must be 1; multiple hydraulic channel bodies are unsupported"
        )
    return count


def _fan_curve_model(
    *,
    diameter: float,
    p_fan_max: float,
    k1: float,
    k2: float,
    k3: float,
    fan_curve_flow_m3_s: list[float] | tuple[float, ...] | None,
    fan_curve_pressure_pa: list[float] | tuple[float, ...] | None,
    fan_free_flow_m3_s: float | None,
    fan_shutoff_pressure_pa: float | None,
    fan_speed_rpm: float | None,
):
    reference_speed = None
    if fan_speed_rpm is not None:
        if not math.isfinite(fan_speed_rpm) or fan_speed_rpm <= 0:
            raise ValueError("fan_speed_rpm must be finite and > 0")
        reference_speed = float(fan_speed_rpm)
    similarity_speed = (p_fan_max / (k3 * diameter**5)) ** (1.0 / 3.0)
    if fan_curve_flow_m3_s is not None or fan_curve_pressure_pa is not None:
        if fan_curve_flow_m3_s is None or fan_curve_pressure_pa is None:
            raise ValueError("both fan curve arrays must be supplied")
        q = np.asarray(fan_curve_flow_m3_s, dtype=float)
        dp = np.asarray(fan_curve_pressure_pa, dtype=float)
        if q.ndim != 1 or dp.ndim != 1 or len(q) < 2 or len(q) != len(dp):
            raise ValueError(
                "fan curve arrays must be equal one-dimensional arrays with >=2 points"
            )
        if not np.all(np.isfinite(q)) or not np.all(np.isfinite(dp)):
            raise ValueError("fan curve points must be finite")
        if not math.isclose(float(q[0]), 0.0, abs_tol=1e-14) or q[-1] <= 0:
            raise ValueError("fan curve must start at zero flow and end at positive flow")
        if np.any(np.diff(q) <= 0) or np.any(np.diff(dp) > 1e-12) or np.any(dp < 0):
            raise ValueError(
                "fan flow must increase and pressure must be nonincreasing/nonnegative"
            )
        return (
            reference_speed,
            float(q[-1]),
            float(dp[0]),
            "user supplied piecewise-linear curve",
            lambda x: float(np.interp(x, q, dp)),
        )
    if (fan_free_flow_m3_s is None) != (fan_shutoff_pressure_pa is None):
        raise ValueError("fan free-flow and shutoff-pressure endpoints must be supplied together")
    if fan_free_flow_m3_s is None:
        speed = reference_speed if reference_speed is not None else similarity_speed
        qmax = k1 * speed * diameter**3
        dp0 = k2 * speed**2 * diameter**2
        model = "parabolic fit to similarity endpoints"
        reported_speed = speed
    else:
        qmax = float(fan_free_flow_m3_s)
        dp0 = float(fan_shutoff_pressure_pa)
        model = "parabolic fit to supplied endpoints"
        reported_speed = reference_speed
    if not math.isfinite(qmax) or not math.isfinite(dp0) or qmax <= 0 or dp0 <= 0:
        raise ValueError("fan curve endpoints must be finite and > 0")
    return reported_speed, qmax, dp0, model, lambda x: dp0 * max(0.0, 1.0 - (x / qmax) ** 2)


def _rectangular_pressure_drop(
    *,
    q_total: float,
    n_channels: int,
    hydraulic_branch_count: int,
    gap: float,
    height: float,
    length: float,
    t_air_c: float,
):
    """Smooth rectangular-duct Darcy loss; manifold and minor losses excluded."""
    fluid = air_properties(t_air_c)
    q_ch = q_total / (n_channels * hydraulic_branch_count)
    area = gap * height
    velocity = q_ch / area
    dh = 2.0 * gap * height / (gap + height)
    re = velocity * dh / fluid.kinematic_viscosity
    if q_total == 0:
        return 0.0, 0.0, 0.0, "zero-flow boundary"
    aspect = min(gap, height) / max(gap, height)
    if re <= 0:
        return math.inf, re, velocity, "invalid_zero_flow"
    if re < 2300.0:
        poiseuille = 96.0 * (
            1.0
            - 1.3553 * aspect
            + 1.9467 * aspect**2
            - 1.7012 * aspect**3
            + 0.9564 * aspect**4
            - 0.2537 * aspect**5
        )
        f_darcy = poiseuille / re
        regime = "laminar rectangular Poiseuille"
    elif 3000.0 <= re <= 100000.0:
        f_darcy = 1.0 / (0.79 * math.log(re) - 1.64) ** 2
        regime = "smooth Gnielinski friction"
    else:
        return math.inf, re, velocity, "outside transition/correlation range"
    dp = f_darcy * (length / dh) * 0.5 * fluid.density * velocity**2
    return dp, re, velocity, regime


def _bounded_operating_point(
    *,
    q_max: float,
    fan_dp,
    fan_pressure_scale: float,
    n_channels: int,
    hydraulic_branch_count: int,
    gap: float,
    height: float,
    length: float,
    t_air_c: float,
):
    """Find a root only inside contiguous supported Reynolds-number domains.

    Re 2300--3000 is deliberately excluded. A sign change across that gap is
    reported as correlation_out_of_range; it is never passed to the root solver.
    The exactly-zero-flow endpoint is excluded from forced-air feasibility.
    """
    fluid = air_properties(t_air_c)
    area = gap * height
    dh = 2.0 * gap * height / (gap + height)
    q_floor = max(q_max * 1e-10, 1e-14)
    if q_max <= q_floor:
        return "no_intersection", None, None, None, None

    def flow_at_reynolds(reynolds: float) -> float:
        return (
            reynolds * n_channels * hydraulic_branch_count * area * fluid.kinematic_viscosity / dh
        )

    def residual(q: float):
        dp_system, re, _, regime = _rectangular_pressure_drop(
            q_total=q,
            n_channels=n_channels,
            hydraulic_branch_count=hydraulic_branch_count,
            gap=gap,
            height=height,
            length=length,
            t_air_c=t_air_c,
        )
        if not math.isfinite(dp_system):
            return -math.inf, dp_system, re, regime
        return fan_pressure_scale * fan_dp(q) - dp_system, dp_system, re, regime

    laminar_hi = min(q_max, flow_at_reynolds(2300.0 * (1.0 - 1e-10)))
    turbulent_lo = max(q_floor, flow_at_reynolds(3000.0 * (1.0 + 1e-10)))
    max_supported_re = 100000.0 * (1.0 - 1e-10)
    turbulent_hi = min(q_max, flow_at_reynolds(max_supported_re))
    domains = (
        (q_floor, laminar_hi, "laminar rectangular Poiseuille"),
        (turbulent_lo, turbulent_hi, "smooth Gnielinski friction"),
    )
    roots = []
    for lo, hi, expected_regime in domains:
        if hi <= lo:
            continue
        flo, dp_lo, re_lo, regime_lo = residual(lo)
        fhi, dp_hi, re_hi, regime_hi = residual(hi)
        if regime_lo != expected_regime or regime_hi != expected_regime:
            continue
        if flo == 0.0:
            roots.append((lo, dp_lo, re_lo, regime_lo))
            continue
        if fhi == 0.0:
            roots.append((hi, dp_hi, re_hi, regime_hi))
            continue
        if flo < 0.0 or fhi > 0.0:
            continue
        left, right = lo, hi
        fleft = flo
        for _ in range(100):
            mid = (left + right) / 2.0
            fm, dp_mid, re_mid, regime_mid = residual(mid)
            if regime_mid != expected_regime:
                break
            if abs(fm) <= max(1e-7, abs(dp_mid) * 1e-8) or right - left <= max(
                1e-13, q_max * 1e-11
            ):
                roots.append((mid, dp_mid, re_mid, regime_mid))
                break
            if fleft * fm <= 0.0:
                right = mid
            else:
                left, fleft = mid, fm
        else:
            mid = (left + right) / 2.0
            _, dp_mid, re_mid, regime_mid = residual(mid)
            roots.append((mid, dp_mid, re_mid, regime_mid))

    if roots:
        q, dp, re, regime = min(roots, key=lambda item: item[0])
        if q <= q_floor or q <= 0.0 or dp <= 0.0:
            return "no_intersection", None, None, None, None
        return "converged", q, dp, re, regime

    # Only classify the operating point as outside the supported correlations
    # when the residual forces a crossing through an excluded interval.
    excluded_crossing = False
    if laminar_hi > q_floor and turbulent_lo < q_max:
        f_laminar_edge = residual(laminar_hi)[0]
        f_turbulent_edge = residual(turbulent_lo)[0]
        excluded_crossing = f_laminar_edge >= 0.0 and f_turbulent_edge <= 0.0
    high_re_flow = flow_at_reynolds(max_supported_re)
    if q_max > high_re_flow:
        f_high_re = residual(min(high_re_flow, q_max))[0]
        excluded_crossing = excluded_crossing or f_high_re >= 0.0
    q_re = q_max * dh / (n_channels * hydraulic_branch_count * area * fluid.kinematic_viscosity)
    if 2300.0 <= q_re < 3000.0 and laminar_hi > q_floor:
        excluded_crossing = excluded_crossing or residual(laminar_hi)[0] >= 0.0
    return (
        ("correlation_out_of_range" if excluded_crossing else "no_intersection"),
        None,
        None,
        None,
        None,
    )


def cspi_evaluate_geometry(
    *,
    lambda_hs: float,
    sink_width_m: float,
    fin_height_m: float,
    sink_length_m: float,
    base_thickness_m: float,
    channel_count: int,
    channel_width_m: float,
    fin_thickness_m: float,
    p_fan_max: float,
    fan_diameter_m: float,
    fan_depth_m: float = 0.0,
    duct_length_m: float = 0.0,
    face_count: int = 1,
    hydraulic_branch_count: int = 1,
    t_air_c: float = 80.0,
    source_power_w: float = 0.0,
    assembly_face_width_m: float | None = None,
    assembly_face_height_m: float | None = None,
    fan_curve_flow_m3_s: list[float] | tuple[float, ...] | None = None,
    fan_curve_pressure_pa: list[float] | tuple[float, ...] | None = None,
    fan_free_flow_m3_s: float | None = None,
    fan_shutoff_pressure_pa: float | None = None,
    fan_speed_rpm: float | None = None,
    auxiliary_power_w: float | None = None,
    auxiliary_power_basis: str | None = None,
    k1: float = 6e-3,
    k2: float = 5e-4,
    k3: float = 30e-6,
) -> CspiOptResult:
    """Evaluate a fixed sink against a bounded fan curve.

    ``face_count`` is the number of thermally heated faces. One hydraulic channel
    body is modeled; ``hydraulic_branch_count`` is retained as an explicit input
    and must be 1. Multiple-body topologies require a matching thermal and volume
    model before they can be evaluated. A shared channel body may have two heated
    faces. Explicit fan curves carry no rpm unless the caller supplies their
    reference speed.
    """
    channel_count = _validated_count("channel_count", channel_count, 2)
    face_count = _validated_face_count(face_count)
    hydraulic_branch_count = _validated_hydraulic_branch_count(hydraulic_branch_count)
    positive = {
        "lambda_hs": lambda_hs,
        "sink_width_m": sink_width_m,
        "fin_height_m": fin_height_m,
        "sink_length_m": sink_length_m,
        "channel_width_m": channel_width_m,
        "fin_thickness_m": fin_thickness_m,
        "fan_diameter_m": fan_diameter_m,
        "p_fan_max": p_fan_max,
        "k1": k1,
        "k2": k2,
        "k3": k3,
    }
    for name, value in positive.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and > 0")
    lengths_and_power = (base_thickness_m, fan_depth_m, duct_length_m, source_power_w)
    if any(not math.isfinite(v) or v < 0 for v in lengths_and_power):
        raise ValueError("base/fan/duct lengths and source power must be finite and >= 0")
    if base_thickness_m + fin_height_m <= 0:
        raise ValueError("physical sink height must be > 0")
    if not math.isfinite(t_air_c) or t_air_c <= -273.15:
        raise ValueError("t_air_c must be finite and above absolute zero")

    occupied_width = channel_count * channel_width_m + (channel_count + 1) * fin_thickness_m
    width_tolerance = max(1e-12, sink_width_m * 1e-12)
    if occupied_width > sink_width_m + width_tolerance:
        raise ValueError(
            f"channel and fin widths overfill sink_width_m: {occupied_width:g} m > "
            f"{sink_width_m:g} m"
        )
    physical_height = base_thickness_m + fin_height_m
    required_face_width = max(sink_width_m, fan_diameter_m)
    required_face_height = max(physical_height, fan_diameter_m)
    face_w = required_face_width if assembly_face_width_m is None else assembly_face_width_m
    face_h = required_face_height if assembly_face_height_m is None else assembly_face_height_m
    if not math.isfinite(face_w) or not math.isfinite(face_h) or face_w <= 0 or face_h <= 0:
        raise ValueError("assembly face dimensions must be finite and > 0")
    if face_w + width_tolerance < required_face_width:
        raise ValueError("assembly_face_width_m must contain sink width and fan diameter")
    if face_h + width_tolerance < required_face_height:
        raise ValueError(
            "assembly_face_height_m must contain full base/fin height and fan diameter"
        )

    speed, qmax, dpmax, fan_model, fan_dp = _fan_curve_model(
        diameter=fan_diameter_m,
        p_fan_max=p_fan_max,
        k1=k1,
        k2=k2,
        k3=k3,
        fan_curve_flow_m3_s=fan_curve_flow_m3_s,
        fan_curve_pressure_pa=fan_curve_pressure_pa,
        fan_free_flow_m3_s=fan_free_flow_m3_s,
        fan_shutoff_pressure_pa=fan_shutoff_pressure_pa,
        fan_speed_rpm=fan_speed_rpm,
    )
    # PCC 2007 Eq. 6 (also PCIM 2005 Eq. 7) models the pressure available at
    # the channel inlet as k times fan static pressure, where Eq. 1 defines
    # k = s / (b / n). With no bypass/leakage path, total fan flow equals the
    # aggregate channel flow; that flow-conservation mapping is an explicit
    # model assumption because the source uses separate V and V_lam symbols.
    fin_spacing_ratio = channel_count * channel_width_m / sink_width_m
    status, flow, dp, re, regime = _bounded_operating_point(
        q_max=qmax,
        fan_dp=fan_dp,
        fan_pressure_scale=fin_spacing_ratio,
        n_channels=channel_count,
        hydraulic_branch_count=hydraulic_branch_count,
        gap=channel_width_m,
        height=fin_height_m,
        length=sink_length_m,
        t_air_c=t_air_c,
    )
    sink_vol = face_w * face_h * sink_length_m * 1000.0
    fan_vol = face_w * face_h * fan_depth_m * 1000.0
    duct_vol = face_w * face_h * duct_length_m * 1000.0
    total_vol = sink_vol + fan_vol + duct_vol
    material_bbox = sink_width_m * physical_height * sink_length_m * 1000.0
    half_fin_r = fin_height_m / (2.0 * lambda_hs * fin_thickness_m * sink_length_m)
    validity = (
        "one smooth rectangular channel body; equal flow split among its parallel channels",
        "heated-face count controls thermal normalization and does not duplicate "
        "hydraulic channels",
        "available channel-inlet pressure is fin_spacing_ratio times fan static pressure "
        "per PCC 2007 Eq. 6; aggregate fan/channel flow equality assumes no bypass or leakage",
        "pressure drop is fully developed Darcy-Weisbach; entrance/exit, plenum, duct "
        "and leakage losses excluded",
        "laminar rectangular Poiseuille for Re < 2300; transition 2300-3000 rejected; "
        "smooth Gnielinski friction for 3000-100000",
        "forced-air feasibility excludes the zero-flow endpoint; positive roots only",
        "heat transfer reuses thermal_cli.channel_rth; its source correlation ranges "
        "remain an independent validity condition",
        "fin conduction is distributed with the constant-cross-section fin-efficiency primitive",
        "sink volume uses the declared envelope containing the complete base/fin "
        "bounding box; fan and duct use that same envelope",
        "two-face normalization uses total power; multiple hydraulic channel bodies "
        "are unsupported",
    )
    if auxiliary_power_w is None:
        reported_auxiliary_power = p_fan_max
        reported_auxiliary_basis = (
            "p_fan_max shaft-power proxy; not electrical input at the operating point"
        )
    else:
        if not math.isfinite(auxiliary_power_w) or auxiliary_power_w < 0:
            raise ValueError("auxiliary_power_w must be finite and >= 0")
        reported_auxiliary_power = auxiliary_power_w
        reported_auxiliary_basis = auxiliary_power_basis or "caller-supplied auxiliary power"
    validity = (*validity, f"auxiliary power basis: {reported_auxiliary_basis}")
    common = dict(
        n=channel_count,
        s=channel_width_m,
        t=fin_thickness_m,
        n_fan=speed,
        length=sink_length_m,
        v_max=qmax,
        dp_max=dpmax,
        operating_point_status=status,
        fan_curve_model=fan_model,
        fan_pressure_pa=fan_dp(flow) if flow is not None else None,
        fin_spacing_ratio=fin_spacing_ratio,
        fan_pressure_scale=fin_spacing_ratio,
        flow_rate_m3_s=flow,
        pressure_drop_pa=dp,
        auxiliary_power_w=reported_auxiliary_power,
        auxiliary_power_basis=reported_auxiliary_basis,
        temperature_reference_c=t_air_c,
        source_power_w=source_power_w,
        face_count=face_count,
        hydraulic_branch_count=hydraulic_branch_count,
        sink_volume_l=sink_vol,
        fan_volume_l=fan_vol,
        duct_volume_l=duct_vol,
        sink_material_bbox_l=material_bbox,
        fin_half_path_rth_k_w=half_fin_r,
        correlation=regime or "not evaluated",
        pressure_correlation=regime or "not evaluated",
        heat_transfer_correlation="not evaluated",
        validity=validity,
    )
    if status != "converged" or flow is None:
        return CspiOptResult(
            cspi=0.0, rth=math.inf, vol=total_vol, re=re or 0.0, feasible=False, **common
        )

    fluid = air_properties(t_air_c)
    outlet = t_air_c
    for _ in range(8):
        if flow > 0 and source_power_w > 0:
            outlet = t_air_c + source_power_w / (fluid.density * flow * fluid.heat_capacity)
        fluid = air_properties(0.5 * (t_air_c + outlet))
    q_channel = flow / (hydraulic_branch_count * channel_count)
    _, heat_re, _, h = channel_rth(
        width=channel_width_m,
        height=fin_height_m,
        length=sink_length_m,
        flow_rate=q_channel,
        fluid=fluid,
    )
    heat_correlation = (
        "Sieder-Tate/Shah-London laminar developing"
        if heat_re <= 2300.0
        else "Gnielinski turbulent"
    )
    if not (heat_re < 2300.0 or 3000.0 <= heat_re <= 100000.0) or h <= 0:
        common["operating_point_status"] = "heat_transfer_correlation_out_of_range"
        common["correlation"] = f"{regime}; heat Re={heat_re:g}"
        common["heat_transfer_correlation"] = heat_correlation
        return CspiOptResult(
            cspi=0.0, rth=math.inf, vol=total_vol, re=heat_re, feasible=False, **common
        )

    n_fins = channel_count + 1
    fin_height_per_face_m = fin_height_m / face_count
    fin_area = 2.0 * n_fins * sink_length_m * fin_height_per_face_m
    bare_area = (sink_width_m - n_fins * fin_thickness_m) * sink_length_m
    eta = fin_efficiency(
        L=fin_height_per_face_m,
        h=h,
        A=2.0 * sink_length_m * fin_height_per_face_m,
        k=lambda_hs,
        Ac=fin_thickness_m * sink_length_m,
    )
    r_conv = 1.0 / (h * (bare_area + eta * fin_area))
    q_face = flow / face_count
    r_warming = 0.5 / (fluid.density * fluid.heat_capacity * q_face)
    r_base = base_thickness_m / (lambda_hs * sink_width_m * sink_length_m)
    r_face = r_base + r_conv + r_warming
    r_system = r_face / face_count
    common["fin_efficiency"] = eta
    common["r_face_k_w"] = r_face
    common["outlet_air_temperature_c"] = outlet
    common["correlation"] = regime
    common["heat_transfer_correlation"] = heat_correlation
    cspi = cspi_calc(rth=r_system, vol_cs=total_vol) if total_vol > 0 else 0.0
    return CspiOptResult(
        cspi=cspi,
        rth=r_system,
        vol=total_vol,
        re=heat_re,
        feasible=math.isfinite(r_system) and r_system > 0 and cspi > 0,
        **common,
    )


def cspi_optimize(
    *,
    lambda_hs: float,
    a_chip: float,
    c: float,
    p_fan_max: float,
    t_min: float = 0.0,
    k1: float = 6e-3,
    k2: float = 5e-4,
    k3: float = 30e-6,
    t_air: float = 80.0,
    n_pts: int = 8,
    face_count: int = 1,
    hydraulic_branch_count: int = 1,
    source_power_w: float = 0.0,
    base_thickness_m: float = 0.0,
    fan_depth_m: float = 0.0,
    duct_length_m: float = 0.0,
    channel_width_min_m: float = 0.2e-3,
    channel_width_step_m: float = 0.2e-3,
    fan_curve_flow_m3_s: list[float] | tuple[float, ...] | None = None,
    fan_curve_pressure_pa: list[float] | tuple[float, ...] | None = None,
    fan_free_flow_m3_s: float | None = None,
    fan_shutoff_pressure_pa: float | None = None,
    fan_speed_rpm: float | None = None,
    auxiliary_power_w: float | None = None,
    auxiliary_power_basis: str | None = None,
) -> CspiOptResult:
    """Search integer channel counts and an independent channel-gap grid.

    ``c`` is the total square sink envelope height/width. Base thickness consumes
    part of that height; fin height is ``c - base_thickness_m``. For each channel
    count, the gap is sampled from ``channel_width_min_m`` through the largest
    gap that leaves every fin at least ``t_min`` thick. Fin thickness closes the
    width exactly. ``n_pts`` sets the uniform gap-grid resolution per count and
    ``channel_width_step_m`` inserts explicit manufacturable gap increments.
    """
    values = (lambda_hs, a_chip, c, p_fan_max, k1, k2, k3)
    if any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("lambda_hs, a_chip, c, p_fan_max, k1, k2, k3 must be finite and > 0")
    if not math.isfinite(t_air) or t_air <= -273.15:
        raise ValueError("t_air must be finite and above absolute zero [°C]")
    if not math.isfinite(t_min) or t_min < 0:
        raise ValueError(f"t_min must be finite and >= 0, got {t_min}")
    n_pts = _validated_count("n_pts", n_pts, 2)
    face_count = _validated_face_count(face_count)
    hydraulic_branch_count = _validated_hydraulic_branch_count(hydraulic_branch_count)
    if not math.isfinite(source_power_w) or source_power_w < 0:
        raise ValueError("source_power_w must be finite and >= 0")
    if not math.isfinite(base_thickness_m) or base_thickness_m < 0 or base_thickness_m >= c:
        raise ValueError(
            "base_thickness_m must be finite, >= 0, and smaller than total sink height c"
        )
    if not math.isfinite(channel_width_min_m) or channel_width_min_m <= 0:
        raise ValueError("channel_width_min_m must be finite and > 0")
    if not math.isfinite(channel_width_step_m) or channel_width_step_m <= 0:
        raise ValueError("channel_width_step_m must be finite and > 0")
    for name, value in (("fan_depth_m", fan_depth_m), ("duct_length_m", duct_length_m)):
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and >= 0")

    length = a_chip / c
    fin_height = c - base_thickness_m
    maximum_count = int(c / channel_width_min_m)
    candidates = []
    gap_step_count = math.floor((c - channel_width_min_m) / channel_width_step_m) + 1
    explicit_gaps = [
        channel_width_min_m + index * channel_width_step_m for index in range(gap_step_count)
    ]
    for channels in range(2, maximum_count + 1):
        maximum_gap = (c - (channels + 1) * t_min) / channels
        if maximum_gap < channel_width_min_m:
            continue
        uniform = np.linspace(channel_width_min_m, maximum_gap, n_pts)
        gaps = {float(value) for value in uniform}
        gaps.update(
            value for value in explicit_gaps if value <= maximum_gap + max(1e-12, c * 1e-12)
        )
        gaps.add(float(maximum_gap))
        for gap in sorted(gaps):
            thickness = (c - channels * gap) / (channels + 1)
            if thickness < t_min or thickness <= 0:
                continue
            candidates.append(
                cspi_evaluate_geometry(
                    lambda_hs=lambda_hs,
                    sink_width_m=c,
                    fin_height_m=fin_height,
                    sink_length_m=length,
                    base_thickness_m=base_thickness_m,
                    channel_count=channels,
                    channel_width_m=gap,
                    fin_thickness_m=thickness,
                    p_fan_max=p_fan_max,
                    fan_diameter_m=c,
                    fan_depth_m=fan_depth_m,
                    duct_length_m=duct_length_m,
                    face_count=face_count,
                    hydraulic_branch_count=hydraulic_branch_count,
                    t_air_c=t_air,
                    source_power_w=source_power_w,
                    fan_curve_flow_m3_s=fan_curve_flow_m3_s,
                    fan_curve_pressure_pa=fan_curve_pressure_pa,
                    fan_free_flow_m3_s=fan_free_flow_m3_s,
                    fan_shutoff_pressure_pa=fan_shutoff_pressure_pa,
                    fan_speed_rpm=fan_speed_rpm,
                    auxiliary_power_w=auxiliary_power_w,
                    auxiliary_power_basis=auxiliary_power_basis,
                    k1=k1,
                    k2=k2,
                    k3=k3,
                    assembly_face_width_m=c,
                    assembly_face_height_m=c,
                )
            )
    if not candidates:
        raise ValueError("no integer channel/gap geometries satisfy width and manufacturing bounds")
    feasible = [item for item in candidates if item.feasible]
    if feasible:
        return max(feasible, key=lambda item: item.cspi)
    return candidates[0]


def cspi_sweep(
    *,
    a_chip: float,
    p_fan_max: float,
    lambdas: list[float],
    cs: list[float],
    t_min: float = 0.0,
    **kwargs,
) -> CspiSweepResult:
    """Parametric 2-D sweep over heatsink cross-section and thermal conductivity.

    Parameters
    ----------
    a_chip:    Total chip footprint area [m^2]
    p_fan_max: Maximum fan shaft power [W]
    lambdas:   List of thermal conductivities to sweep [W/(m K)]
    cs:        List of heatsink heights (fan diameters) to sweep [m]
    t_min:     Minimum fin thickness [m] (forwarded to cspi_optimize)
    **kwargs:  Additional keyword arguments forwarded to cspi_optimize
    """
    n_c = len(cs)
    n_l = len(lambdas)

    cspi_grid = np.zeros((n_c, n_l))
    rth_grid = np.zeros((n_c, n_l))

    for i, c in enumerate(cs):
        for j, lam in enumerate(lambdas):
            res = cspi_optimize(
                lambda_hs=lam,
                a_chip=a_chip,
                c=c,
                p_fan_max=p_fan_max,
                t_min=t_min,
                **kwargs,
            )
            cspi_grid[i, j] = res.cspi
            rth_grid[i, j] = res.rth

    return CspiSweepResult(
        cs=list(cs),
        lambdas=list(lambdas),
        cspi=cspi_grid,
        rth=rth_grid,
    )
