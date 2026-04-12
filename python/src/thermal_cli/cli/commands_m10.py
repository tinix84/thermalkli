"""M10 CLI command: forced-conv-sim."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import yaml


def register_all(app: typer.Typer) -> None:
    """Register M10 commands on the Typer app."""

    @app.command("forced-conv-sim")
    def forced_conv_sim_cmd(
        config: Annotated[Path, typer.Option("--config", help="Simulation YAML config (mm, °C)")],
    ) -> None:
        """Run a forced-convection single-scenario simulation."""
        from thermal_cli.forced_conv.workflow import ForcedConvConfig, run_forced_conv_sim

        if not config.exists():
            typer.echo(f"Error: config file not found: {config}", err=True)
            raise typer.Exit(1)

        with open(config) as fh:
            raw = yaml.safe_load(fh)

        hs = raw["heatsink"]
        fan = raw["fan"]
        env = raw.get("environment", {})
        grid = raw.get("grid", {})

        # Convert YAML (mm, °C) → SI (m, K)
        def _src_to_si(s: dict) -> dict:
            return {
                "name": s["name"],
                "x_m": float(s["x_mm"]) / 1000.0,
                "y_m": float(s["y_mm"]) / 1000.0,
                "width_m": float(s["width_mm"]) / 1000.0,
                "height_m": float(s["height_mm"]) / 1000.0,
                "power_w": float(s["power_w"]),
            }

        t_inlet_c = float(env.get("t_inlet_c", 40.0))

        cfg = ForcedConvConfig(
            hs_profile=hs["profile"],
            hs_material=hs["material"],
            length_x_m=float(hs["length_x_mm"]) / 1000.0,
            length_y_m=float(hs["length_y_mm"]) / 1000.0,
            copper_plate_thickness_m=float(hs.get("copper_plate_thickness_mm", 0.0)) / 1000.0,
            fan_model=fan["model"],
            fan_count=int(fan.get("count", 1)),
            ventilation=fan.get("ventilation", "push"),
            impinge_gap_m=float(fan.get("impinge_gap_mm", 0.0)) / 1000.0,
            sources=[_src_to_si(s) for s in raw.get("sources", [])],
            t_inlet_k=t_inlet_c + 273.15,
            nx=int(grid.get("nx", 41)),
            ny=int(grid.get("ny", 41)),
            n_fourier=int(grid.get("n_fourier", 25)),
        )

        result = run_forced_conv_sim(cfg)

        typer.echo(f"t_base_max    = {result.t_base_max_k - 273.15:.2f} °C")
        typer.echo(f"t_fluid_out   = {result.t_fluid_out_k - 273.15:.2f} °C")
        typer.echo(f"q_operating   = {result.q_operating_m3s:.6f} m³/s")
        typer.echo(f"re_hydraulic  = {result.re_hydraulic:.1f}")
        typer.echo(f"rth_fin       = {result.rth_fin_kw:.4f} K/W")
        typer.echo(f"h_eq          = {result.h_eq_wm2k:.2f} W/(m²·K)")
