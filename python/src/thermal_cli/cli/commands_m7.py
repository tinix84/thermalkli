"""M7 CLI commands: h-coeff, radiation, free-conv, water-cooling,
natural-conv-hs, hydraulic-op, fin-rth.

All temperature CLI options are in degrees Celsius.  The underlying formula
functions take Kelvin, so the CLI adds 273.15 before calling them.  The
radiation sub-app is the exception: it takes T1/T2 directly in Kelvin,
matching the radiation.py API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import yaml

# ---------------------------------------------------------------------------
# Sub-apps
# ---------------------------------------------------------------------------

_h_coeff_app = typer.Typer(
    name="h-coeff",
    help="Heat-transfer coefficient correlations (forced, natural, radiation).",
    no_args_is_help=True,
)

_radiation_app = typer.Typer(
    name="radiation",
    help="Radiation heat transfer between surfaces (T1/T2 in Kelvin).",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_C_TO_K = 273.15


def _out(key: str, value: float) -> None:
    """Emit a key=value line matching the Octave CLI output format."""
    typer.echo(f"{key}={value:g}")


# ===========================================================================
# h-coeff  sub-commands
# ===========================================================================


@_h_coeff_app.command("forced")
def h_coeff_forced(
    length: Annotated[float, typer.Option("--length", help="Plate length [m]")],
    velocity: Annotated[float, typer.Option("--velocity", help="Free-stream velocity [m/s]")],
    t_ambient: Annotated[float, typer.Option("--t-ambient", help="Ambient temperature [°C]")],
    t_surface: Annotated[float, typer.Option("--t-surface", help="Surface temperature [°C]")],
) -> None:
    """Forced-convection h for flow over a flat plate (Blasius/mixed)."""
    from thermal_cli.formula.convection import h_forced

    h, Re = h_forced(
        length=length,
        velocity=velocity,
        t_ambient=t_ambient + _C_TO_K,
        t_surface=t_surface + _C_TO_K,
    )
    _out("h", h)
    _out("Re", Re)


@_h_coeff_app.command("natural")
def h_coeff_natural(
    orientation: Annotated[
        str,
        typer.Option(
            "--orientation",
            help="Surface orientation: vertical | horizontal_top | horizontal_bottom",
        ),
    ],
    length: Annotated[float, typer.Option("--length", help="Characteristic length [m]")],
    t_ambient: Annotated[float, typer.Option("--t-ambient", help="Ambient temperature [°C]")],
    t_surface: Annotated[float, typer.Option("--t-surface", help="Surface temperature [°C]")],
) -> None:
    """Natural-convection h (Incropera Ch.9 correlations)."""
    from thermal_cli.formula.convection import h_natural

    h, Nu = h_natural(
        orientation=orientation,
        length=length,
        t_ambient=t_ambient + _C_TO_K,
        t_surface=t_surface + _C_TO_K,
    )
    _out("h", h)
    _out("Nu", Nu)


@_h_coeff_app.command("radiation")
def h_coeff_radiation(
    emissivity: Annotated[float, typer.Option("--emissivity", help="Surface emissivity [0-1]")],
    t_ambient: Annotated[float, typer.Option("--t-ambient", help="Ambient temperature [°C]")],
    t_surface: Annotated[float, typer.Option("--t-surface", help="Surface temperature [°C]")],
) -> None:
    """Linearized radiation heat-transfer coefficient."""
    from thermal_cli.formula.convection import h_radiation_linearized

    h = h_radiation_linearized(
        emissivity=emissivity,
        t_ambient=t_ambient + _C_TO_K,
        t_surface=t_surface + _C_TO_K,
    )
    _out("h", h)


# ===========================================================================
# radiation  sub-commands  (T1/T2 in Kelvin — matches radiation.py API)
# ===========================================================================


@_radiation_app.command("parallel")
def radiation_parallel(
    t1: Annotated[float, typer.Option("--t1", help="Temperature of surface 1 [K]")],
    t2: Annotated[float, typer.Option("--t2", help="Temperature of surface 2 [K]")],
    area: Annotated[float, typer.Option("--area", help="Surface area [m²]")],
    eps1: Annotated[float, typer.Option("--eps1", help="Emissivity of surface 1")],
    eps2: Annotated[float, typer.Option("--eps2", help="Emissivity of surface 2")],
) -> None:
    """Radiation between large parallel planes (Incropera eq. 13.24)."""
    from thermal_cli.formula.radiation import parallel_planes

    q = parallel_planes(T1=t1, T2=t2, A=area, eps1=eps1, eps2=eps2)
    _out("q", q)


@_radiation_app.command("cylinder")
def radiation_cylinder(
    t1: Annotated[float, typer.Option("--t1", help="Inner cylinder temperature [K]")],
    t2: Annotated[float, typer.Option("--t2", help="Outer cylinder temperature [K]")],
    r1: Annotated[float, typer.Option("--r1", help="Inner radius [m]")],
    r2: Annotated[float, typer.Option("--r2", help="Outer radius [m]")],
    length: Annotated[float, typer.Option("--length", help="Cylinder length [m]")],
    eps1: Annotated[float, typer.Option("--eps1", help="Emissivity of inner surface")],
    eps2: Annotated[float, typer.Option("--eps2", help="Emissivity of outer surface")],
) -> None:
    """Radiation between long concentric cylinders."""
    from thermal_cli.formula.radiation import concentric_cylinders

    q = concentric_cylinders(T1=t1, T2=t2, r1=r1, r2=r2, L=length, eps1=eps1, eps2=eps2)
    _out("q", q)


@_radiation_app.command("sphere")
def radiation_sphere(
    t1: Annotated[float, typer.Option("--t1", help="Inner sphere temperature [K]")],
    t2: Annotated[float, typer.Option("--t2", help="Outer sphere temperature [K]")],
    r1: Annotated[float, typer.Option("--r1", help="Inner radius [m]")],
    r2: Annotated[float, typer.Option("--r2", help="Outer radius [m]")],
    eps1: Annotated[float, typer.Option("--eps1", help="Emissivity of inner surface")],
    eps2: Annotated[float, typer.Option("--eps2", help="Emissivity of outer surface")],
) -> None:
    """Radiation between concentric spheres."""
    from thermal_cli.formula.radiation import concentric_spheres

    q = concentric_spheres(T1=t1, T2=t2, r1=r1, r2=r2, eps1=eps1, eps2=eps2)
    _out("q", q)


@_radiation_app.command("enclosure")
def radiation_enclosure(
    t1: Annotated[float, typer.Option("--t1", help="Temperature of surface 1 [K]")],
    t2: Annotated[float, typer.Option("--t2", help="Temperature of surface 2 [K]")],
    eps1: Annotated[float, typer.Option("--eps1", help="Emissivity of surface 1")],
    eps2: Annotated[float, typer.Option("--eps2", help="Emissivity of surface 2")],
    a1: Annotated[float, typer.Option("--a1", help="Area of surface 1 [m²]")],
    a2: Annotated[float, typer.Option("--a2", help="Area of surface 2 [m²]")],
    f12: Annotated[float, typer.Option("--f12", help="View factor from surface 1 to 2")],
) -> None:
    """Two-surface enclosure radiation (Incropera eq. 13.23)."""
    from thermal_cli.formula.radiation import enclosure

    q = enclosure(T1=t1, T2=t2, eps1=eps1, eps2=eps2, A1=a1, A2=a2, F12=f12)
    _out("q", q)


@_radiation_app.command("convex")
def radiation_convex(
    t1: Annotated[float, typer.Option("--t1", help="Small body temperature [K]")],
    t2: Annotated[float, typer.Option("--t2", help="Large cavity temperature [K]")],
    a1: Annotated[float, typer.Option("--a1", help="Surface area of the small body [m²]")],
    eps1: Annotated[float, typer.Option("--eps1", help="Emissivity of the small body")],
) -> None:
    """Radiation from a small convex body in a large enclosure."""
    from thermal_cli.formula.radiation import small_convex

    q = small_convex(T1=t1, T2=t2, A1=a1, eps1=eps1)
    _out("q", q)


# ===========================================================================
# free-conv
# ===========================================================================


def _parse_face(s: str):
    """Parse a face spec string into a Face dataclass.

    Expected format: ``area=<f>,length=<f>,orientation=<str>[,emissivity=<f>]``
    """
    from thermal_cli.formula.free_conv import Face

    kv: dict[str, str] = {}
    for part in s.split(","):
        key, _, val = part.partition("=")
        kv[key.strip()] = val.strip()

    try:
        area = float(kv["area"])
        length = float(kv["length"])
        orientation = kv["orientation"]
    except KeyError as exc:
        raise typer.BadParameter(
            f"Face spec missing required key {exc}. "
            "Format: area=<f>,length=<f>,orientation=<str>[,emissivity=<f>]"
        ) from exc

    emissivity = float(kv.get("emissivity", "0.9"))
    return Face(area=area, char_length=length, orientation=orientation, emissivity=emissivity)


def _free_conv_command(
    t_ambient: Annotated[float, typer.Option("--t-ambient", help="Ambient temperature [°C]")],
    p_total: Annotated[float, typer.Option("--p-total", help="Total heat to dissipate [W]")],
    face: Annotated[
        list[str],
        typer.Option(
            "--face",
            help=(
                "Face spec (repeatable): area=<m²>,length=<m>,orientation=<str>[,emissivity=<f>]"
            ),
        ),
    ],
) -> None:
    """Find surface temperature from natural convection + radiation on multiple faces."""
    from thermal_cli.formula.free_conv import free_conv_surface_temp

    if not face:
        typer.echo("Error: at least one --face is required.", err=True)
        raise typer.Exit(1)

    faces = [_parse_face(f) for f in face]

    result = free_conv_surface_temp(
        faces=faces,
        t_ambient=t_ambient + _C_TO_K,
        p_total=p_total,
    )

    t_surface_c = result.t_surface - _C_TO_K
    _out("t_surface", t_surface_c)
    for i, (h, q) in enumerate(zip(result.h_per_face, result.q_per_face, strict=True)):
        _out(f"h_face{i}", h)
        _out(f"q_face{i}", q)


# ===========================================================================
# water-cooling
# ===========================================================================


def _water_cooling_command(
    p_loss: Annotated[float, typer.Option("--p-loss", help="Total power loss [W]")],
    flow: Annotated[float, typer.Option("--flow", help="Coolant flow rate [l/min]")],
    t_in: Annotated[float, typer.Option("--t-in", help="Coolant inlet temperature [°C]")],
    rth_jc: Annotated[
        float, typer.Option("--rth-jc", help="Junction-to-case Rth per device [K/W]")
    ],
    n_devices: Annotated[int, typer.Option("--n-devices", help="Number of parallel devices")],
    cp: Annotated[float, typer.Option("--cp", help="Coolant specific heat [J/(kg K)]")] = 3483.0,
    rho: Annotated[float, typer.Option("--rho", help="Coolant density [kg/m³]")] = 1064.0,
    rth_cl: Annotated[
        float, typer.Option("--rth-cl", help="Case-to-liquid Rth per device [K/W]")
    ] = 0.0,
) -> None:
    """Coolant/junction temperature calculator for liquid-cooled assemblies."""
    from thermal_cli.formula.water_cooling import water_cooling

    result = water_cooling(
        p_loss=p_loss,
        flow_lpm=flow,
        t_inlet=t_in + _C_TO_K,
        rth_jc=rth_jc,
        n_devices=n_devices,
        cp=cp,
        rho=rho,
        rth_cl=rth_cl,
    )

    _out("dt_coolant", result.dt_coolant)
    _out("t_outlet", result.t_outlet - _C_TO_K)
    _out("t_junction", result.t_junction - _C_TO_K)
    _out("m_dot", result.m_dot)
    _out("p_per_device", result.p_per_device)


# ===========================================================================
# natural-conv-hs
# ===========================================================================


def _natural_conv_hs_command(
    n_fins: Annotated[int, typer.Option("--n-fins", help="Number of fins")],
    fin_height: Annotated[float, typer.Option("--fin-height", help="Fin height [m]")],
    fin_length: Annotated[float, typer.Option("--fin-length", help="Fin length [m]")],
    fin_thickness: Annotated[float, typer.Option("--fin-thickness", help="Fin thickness [m]")],
    channel_width: Annotated[float, typer.Option("--channel-width", help="Channel width [m]")],
    base_thickness: Annotated[
        float, typer.Option("--base-thickness", help="Base plate thickness [m]")
    ],
    k: Annotated[float, typer.Option("--k", help="Fin thermal conductivity [W/(m K)]")],
    t_ambient: Annotated[float, typer.Option("--t-ambient", help="Ambient temperature [°C]")],
    p_loss: Annotated[float, typer.Option("--p-loss", help="Applied power loss [W]")],
    emissivity: Annotated[float, typer.Option("--emissivity", help="Surface emissivity")] = 0.9,
) -> None:
    """Fanless heatsink Rth estimator (natural convection + radiation)."""
    from thermal_cli.heatsinks.natural_conv import natural_conv_hs

    result = natural_conv_hs(
        n_fins=n_fins,
        fin_height=fin_height,
        fin_length=fin_length,
        fin_thickness=fin_thickness,
        channel_width=channel_width,
        base_thickness=base_thickness,
        k=k,
        t_ambient=t_ambient + _C_TO_K,
        p_loss=p_loss,
        emissivity=emissivity,
    )

    _out("t_surface", result.t_surface - _C_TO_K)
    _out("rth", result.rth)
    _out("h_fin", result.h_fin)
    _out("h_base", result.h_base)
    _out("eta_fin", result.eta_fin)
    _out("q_total", result.q_total)


# ===========================================================================
# Shared YAML config loader helpers
# ===========================================================================


def _load_yaml_config(config_path: Path) -> dict:
    """Load and return a YAML config file as a dict."""
    if not config_path.exists():
        typer.echo(f"Error: config file not found: {config_path}", err=True)
        raise typer.Exit(1)
    with open(config_path) as f:
        return yaml.safe_load(f)


def _build_hs_geometry(cfg: dict):
    """Return (profile, material_name, b_m, width_m, n_fins, tf_m, bch_m, hf_m,
    vent_type, s_m, t_air_k) from a YAML config dict."""
    from thermal_cli.heatsinks.profiles_db import lookup_hs_profile

    hs_cfg = cfg["heatsink"]
    vent_cfg = cfg.get("ventilation", {})
    amb_cfg = cfg.get("ambient", {})

    profile = lookup_hs_profile(hs_cfg["profile"])
    b_m = float(hs_cfg["length"])  # heatsink length = fin depth direction
    width_m = float(hs_cfg["width"])  # heatsink width = fin span direction

    # Dimensions from profile (mm → m)
    hf_m = profile.hf_mm / 1000.0
    tf_m = profile.tf_mm / 1000.0
    bch_m = profile.bch_mm / 1000.0

    # Number of fins
    n_fins = round(width_m * 1000.0 / (bch_m * 1000.0 + tf_m * 1000.0))

    # Ventilation
    vent_type = vent_cfg.get("type", "push")
    s_m = float(vent_cfg.get("impingeOpening", 0.05)) if vent_type == "impinge" else width_m

    # Air inlet temperature with 5 K margin
    t_inlet_k = float(amb_cfg.get("tInlet", 313.15))
    t_air_k = t_inlet_k + 5.0

    material_name = hs_cfg.get("material", None)
    return profile, material_name, b_m, width_m, n_fins, tf_m, bch_m, hf_m, vent_type, s_m, t_air_k


# ===========================================================================
# hydraulic-op
# ===========================================================================


def _hydraulic_op_command(
    config: Annotated[Path, typer.Option("--config", help="YAML config file path")],
) -> None:
    """Fan-heatsink hydraulic operating point from YAML config."""

    from thermal_cli.heatsinks.channel_flow import hydraulic_operating_point
    from thermal_cli.heatsinks.profiles_db import lookup_fan

    cfg = _load_yaml_config(config)
    _, _, b_m, _width_m, n_fins, tf_m, bch_m, hf_m, vent_type, s_m, t_air_k = _build_hs_geometry(
        cfg
    )

    fan_cfg = cfg.get("fan", {})
    fan_model = fan_cfg["model"]
    fan_count = int(fan_cfg.get("count", 1))

    fan = lookup_fan(fan_model)
    # Parallel fans: multiply flow rates by count, pressure unchanged
    fan_qv = fan.qv * fan_count
    fan_hv = fan.hv

    result = hydraulic_operating_point(
        b=b_m,
        s=s_m,
        n_fins=n_fins,
        tf=tf_m,
        bch=bch_m,
        hf=hf_m,
        t_air=t_air_k,
        vent_type=vent_type,
        fan_qv=fan_qv,
        fan_hv=fan_hv,
    )

    _out("reynolds", result.reynolds)
    _out("pressure", result.pressure)
    _out("flowrate", result.flowrate)


# ===========================================================================
# fin-rth
# ===========================================================================


def _fin_rth_command(
    config: Annotated[Path, typer.Option("--config", help="YAML config file path")],
    flowrate: Annotated[float, typer.Option("--flowrate", help="Volumetric flow rate [m³/s]")],
) -> None:
    """Fin thermal resistance at a given flow rate from YAML config."""
    from thermal_cli.heatsinks.channel_flow import fin_thermal_resistance
    from thermal_cli.heatsinks.profiles_db import lookup_hs_material

    cfg = _load_yaml_config(config)
    _profile, material_name, b_m, width_m, n_fins, tf_m, bch_m, hf_m, vent_type, s_m, t_air_k = (
        _build_hs_geometry(cfg)
    )

    if material_name is None:
        typer.echo("Error: heatsink.material must be specified in config for fin-rth.", err=True)
        raise typer.Exit(1)

    material = lookup_hs_material(material_name)
    k_fin = material.k_fin

    result = fin_thermal_resistance(
        qv_f=flowrate,
        a=width_m,
        b=b_m,
        s=s_m,
        tf=tf_m,
        bch=bch_m,
        hf=hf_m,
        t_air=t_air_k,
        vent_type=vent_type,
        k_fin=k_fin,
        n_fins=n_fins,
    )

    _out("reynolds", result.reynolds)
    _out("v_ch1", result.v_ch1)
    _out("v_ch2", result.v_ch2)
    _out("rth", result.rth)
    _out("h_eq", result.h_eq)


# ===========================================================================
# register_all — wire everything into the main Typer app
# ===========================================================================


def register_all(app: typer.Typer) -> None:
    """Add all M7 sub-apps and commands to *app*."""
    # Sub-apps (groups with their own sub-commands)
    app.add_typer(_h_coeff_app, name="h-coeff")
    app.add_typer(_radiation_app, name="radiation")

    # Standalone commands — registered as direct commands on the main app
    app.command("free-conv")(_free_conv_command)
    app.command("water-cooling")(_water_cooling_command)
    app.command("natural-conv-hs")(_natural_conv_hs_command)
    app.command("hydraulic-op")(_hydraulic_op_command)
    app.command("fin-rth")(_fin_rth_command)
