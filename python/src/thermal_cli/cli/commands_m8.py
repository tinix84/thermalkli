"""M8 CLI commands: cspi, cspi-optimize, fan-fit, cspi-sweep.

All units follow the Drofenik/Kolar CSPI conventions:
  - volumes in liters for the CSPI metric
  - lengths/areas in SI (m, m^2)
  - temperatures in Celsius on the CLI (forwarded as Celsius to underlying functions)
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import yaml

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _out(key: str, value: float) -> None:
    """Emit a key=value line matching the CLI output format."""
    typer.echo(f"{key}={value:g}")


# ===========================================================================
# cspi
# ===========================================================================


def _cspi_command(
    rth: Annotated[float, typer.Option("--rth", help="Thermal resistance [K/W]")],
    vol: Annotated[float, typer.Option("--vol", help="Cooling system volume [liters]")],
) -> None:
    """Compute Cooling System Performance Index: CSPI = 1 / (Rth * V_cs)."""
    from thermal_cli.cspi.formulas import cspi_calc

    val = cspi_calc(rth=rth, vol_cs=vol)
    _out("cspi", val)


# ===========================================================================
# cspi-optimize
# ===========================================================================


def _cspi_optimize_command(
    lambda_hs: Annotated[
        float, typer.Option("--lambda", help="Heatsink thermal conductivity [W/(m K)]")
    ],
    a_chip: Annotated[float, typer.Option("--a-chip", help="Total chip footprint area [m^2]")],
    c: Annotated[float, typer.Option("--c", help="Heatsink height = fan diameter [m]")],
    p_fan: Annotated[float, typer.Option("--p-fan", help="Maximum fan shaft power [W]")],
    t_min: Annotated[
        float, typer.Option("--t-min", help="Minimum fin thickness [m] (0 = unconstrained)")
    ] = 0.0,
    k1: Annotated[
        float, typer.Option("--k1", help="Fan scaling coeff k1: V_MAX = k1·N·D^3")
    ] = 6e-3,
    k2: Annotated[
        float, typer.Option("--k2", help="Fan scaling coeff k2: dP_MAX = k2·N^2·D^2")
    ] = 5e-4,
    k3: Annotated[
        float, typer.Option("--k3", help="Fan scaling coeff k3: P_FAN = k3·N^3·D^5")
    ] = 30e-6,
    t_air: Annotated[float, typer.Option("--t-air", help="Reference air temperature [°C]")] = 80.0,
) -> None:
    """Optimise heatsink channel width to maximise CSPI (Drofenik/Kolar CIPS06)."""
    from thermal_cli.cspi.optimizer import cspi_optimize

    res = cspi_optimize(
        lambda_hs=lambda_hs,
        a_chip=a_chip,
        c=c,
        p_fan_max=p_fan,
        t_min=t_min,
        k1=k1,
        k2=k2,
        k3=k3,
        t_air=t_air,
    )

    _out("cspi", res.cspi)
    _out("rth", res.rth)
    _out("vol", res.vol)
    _out("n_fins", res.n)
    _out("s_channel", res.s)
    _out("t_fin", res.t)
    _out("Re", res.re)
    _out("N_fan", res.n_fan)
    _out("V_MAX", res.v_max)
    _out("dp_MAX", res.dp_max)
    typer.echo(f"feasible={'true' if res.feasible else 'false'}")


# ===========================================================================
# fan-fit
# ===========================================================================


def _fan_fit_command(
    v_max: Annotated[float, typer.Option("--v-max", help="Maximum volumetric flow rate [m^3/s]")],
    dp_max: Annotated[float, typer.Option("--dp-max", help="Maximum static pressure rise [Pa]")],
    p_fan: Annotated[float, typer.Option("--p-fan", help="Fan shaft power [W]")],
    diameter: Annotated[float, typer.Option("--diameter", help="Fan diameter [m]")],
    speed: Annotated[float, typer.Option("--speed", help="Fan rotational speed [rpm]")],
) -> None:
    """Compute Drofenik fan scaling coefficients k1, k2, k3 (eq. 29-31)."""
    from thermal_cli.cspi.formulas import fan_scaling_fit

    k1, k2, k3 = fan_scaling_fit(
        v_max=v_max,
        dp_max=dp_max,
        p_fan=p_fan,
        d=diameter,
        n=speed,
    )
    _out("k1", k1)
    _out("k2", k2)
    _out("k3", k3)


# ===========================================================================
# cspi-sweep
# ===========================================================================


def _cspi_sweep_command(
    config: Annotated[Path, typer.Option("--config", help="YAML sweep config file")],
) -> None:
    """2-D CSPI parameter sweep over lambda and c values from a YAML config.

    Config format::

        a_chip: 10e-4
        p_fan_max: 5.0
        lambda: [200, 385]
        c: [0.030, 0.040, 0.050]
        t_min: 0.0        # optional

    Output: table with rows=c values, columns=lambda values, cells=CSPI.
    """
    from thermal_cli.cspi.optimizer import cspi_sweep

    if not config.exists():
        typer.echo(f"Error: config file not found: {config}", err=True)
        raise typer.Exit(1)

    with open(config) as fh:
        cfg = yaml.safe_load(fh)

    a_chip = float(cfg["a_chip"])
    p_fan_max = float(cfg["p_fan_max"])
    lambdas = [float(v) for v in cfg["lambda"]]
    cs = [float(v) for v in cfg["c"]]
    t_min = float(cfg.get("t_min", 0.0))

    # Forward any extra kwargs recognised by cspi_optimize
    extra_keys = {"k1", "k2", "k3", "t_air"}
    kwargs = {k: float(cfg[k]) for k in extra_keys if k in cfg}

    res = cspi_sweep(
        a_chip=a_chip,
        p_fan_max=p_fan_max,
        lambdas=lambdas,
        cs=cs,
        t_min=t_min,
        **kwargs,
    )

    # Header row: "c\lambda" then lambda values
    header_parts = ["c\\lambda"] + [f"{lam:g}" for lam in res.lambdas]
    typer.echo("\t".join(header_parts))

    # Data rows
    for i, c_val in enumerate(res.cs):
        row_parts = [f"{c_val:g}"] + [f"{res.cspi[i, j]:g}" for j in range(len(res.lambdas))]
        typer.echo("\t".join(row_parts))


# ===========================================================================
# register_all — wire everything into the main Typer app
# ===========================================================================


def register_all(app: typer.Typer) -> None:
    """Add all M8 commands to *app*."""
    app.command("cspi")(_cspi_command)
    app.command("cspi-optimize")(_cspi_optimize_command)
    app.command("fan-fit")(_fan_fit_command)
    app.command("cspi-sweep")(_cspi_sweep_command)
