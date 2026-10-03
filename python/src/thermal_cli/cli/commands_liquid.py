"""CLI for the pump-limited liquid-cooler model."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer
import yaml


def _out(key: str, value: float) -> None:
    typer.echo(f"{key}={value:g}")


def register_liquid_commands(app: typer.Typer) -> None:
    @app.command("liquid-cooler")
    def liquid_cooler_cmd(
        config: Annotated[Path, typer.Option("--config", help="Liquid cooler YAML, SI units")],
    ) -> None:
        """Intersect a pump/system curve with a liquid channel and report bulk heating."""
        from thermal_cli.fluids.liquid import LiquidProperty
        from thermal_cli.liquid_cooling import (
            CalibratedPortLoss,
            CircularChannel,
            LiquidLoopVolume,
            PumpCurve,
            SlotChannel,
            evaluate_liquid_cooler,
            pesc2004_b05_curve,
            pesc2004_b05_flow_area_resistance_k_w,
        )

        if not config.exists():
            typer.echo(f"Error: config file not found: {config}", err=True)
            raise typer.Exit(1)
        try:
            raw: Any = yaml.safe_load(config.read_text(encoding="utf-8"))
            pump_raw = raw["pump_curve"]
            if pump_raw.get("source") == "pesc2004_b05":
                pump = pesc2004_b05_curve()
            else:
                pump = PumpCurve(
                    flow_m3_s=pump_raw["flow_m3_s"],
                    pressure_pa=pump_raw["pressure_pa"],
                    provenance=str(pump_raw.get("provenance", "config-supplied")),
                )
            geo = raw["geometry"]
            geometry_kind = geo["type"]
            common = {
                "length_m": float(geo["length_m"]),
                "roughness_m": float(geo.get("roughness_m", 0.0)),
                "minor_loss_k": float(geo.get("minor_loss_k", 0.0)),
            }
            geometry: SlotChannel | CircularChannel
            if geometry_kind == "slot":
                geometry = SlotChannel(
                    **common,
                    width_m=float(geo["width_m"]),
                    gap_m=float(geo["gap_m"]),
                )
            elif geometry_kind == "circular":
                geometry = CircularChannel(
                    **common,
                    diameter_m=float(geo["diameter_m"]),
                )
            else:
                raise ValueError("geometry.type must be 'slot' or 'circular'")
            calibration: CalibratedPortLoss | None = None
            cal_raw = raw.get("calibrated_port_loss")
            if cal_raw == "pesc2004":
                calibration = CalibratedPortLoss.pesc2004()
            elif isinstance(cal_raw, dict):
                calibration = CalibratedPortLoss(
                    a_q2_pa_s2_m6=float(cal_raw["a_q2_pa_s2_m6"]),
                    b_v2_pa_s2_m2=float(cal_raw["b_v2_pa_s2_m2"]),
                    calibration_reference=str(cal_raw["calibration_reference"]),
                )
            volume_raw = raw.get("volume")
            volume = (
                LiquidLoopVolume(
                    cold_plate_m3=float(volume_raw["cold_plate_m3"]),
                    pump_m3=float(volume_raw.get("pump_m3", 0.0)),
                    pipes_m3=float(volume_raw.get("pipes_m3", 0.0)),
                    heat_exchanger_m3=float(volume_raw.get("heat_exchanger_m3", 0.0)),
                )
                if volume_raw is not None
                else None
            )
            flow_area_rth: float | None = None
            flow_area_calibration = raw.get("flow_area_calibration")
            if flow_area_calibration is not None and "flow_area_rth_k_w" in raw:
                raise ValueError("set only one of flow_area_calibration and flow_area_rth_k_w")
            if flow_area_calibration is not None:
                if flow_area_calibration != "pesc2004_b05":
                    raise ValueError("flow_area_calibration must be 'pesc2004_b05'")
                if not isinstance(geometry, SlotChannel):
                    raise ValueError("pesc2004_b05 flow-area calibration requires slot geometry")
                flow_area_rth = pesc2004_b05_flow_area_resistance_k_w(geometry)
            elif "flow_area_rth_k_w" in raw:
                flow_area_rth = float(raw["flow_area_rth_k_w"])
            result = evaluate_liquid_cooler(
                pump_curve=pump,
                geometry=geometry,
                fluid=LiquidProperty(str(raw.get("fluid", "H2OGly50"))),
                inlet_temperature_k=float(raw["inlet_temperature_k"]),
                heat_w=float(raw["heat_w"]),
                channel_count=geo.get("channel_count", 1),
                calibrated_port_loss=calibration,
                flow_area_rth_k_w=flow_area_rth,
                volume=volume,
            )
        except (KeyError, TypeError, ValueError) as exc:
            typer.echo(f"Error: invalid liquid cooler config: {exc}", err=True)
            raise typer.Exit(2) from exc

        op = result.operating_point
        typer.echo(f"operating_point_status={op.status}")
        if op.status != "ok" or op.channel_state is None:
            typer.echo(f"reason={op.reason or 'unavailable'}")
            raise typer.Exit(1)
        _out("flow_total_m3_s", op.total_flow_m3_s or 0.0)
        _out("pressure_balance_Pa", op.pressure_pa or 0.0)
        state = op.channel_state
        _out("flow_per_channel_m3_s", state.per_channel_flow_m3_s)
        _out("channel_count", float(state.channel_count))
        _out("Re_channel", state.reynolds)
        _out("dp_channel_friction_Pa", state.friction_pressure_drop_pa)
        _out("dp_channel_minor_Pa", state.minor_pressure_drop_pa)
        _out("dp_calibrated_ports_Pa", state.calibrated_pressure_drop_pa)
        if result.energy is not None:
            energy = result.energy
            typer.echo(f"energy_status={energy.status}")
            if energy.reason is not None:
                typer.echo(f"energy_reason={energy.reason}")
            _out("Tin_K", energy.inlet_temperature_k)
            if energy.outlet_temperature_k is not None:
                _out("Tout_K", energy.outlet_temperature_k)
                _out("deltaT_coolant_K", energy.temperature_rise_k or 0.0)
                _out("energy_recovered_W", energy.energy_recovered_w or 0.0)
            if energy.mass_flow_kg_s is not None:
                _out("mass_flow_kg_s", energy.mass_flow_kg_s)
        for key, value in (
            ("R_slot_wall_to_bulk_K_W", result.ideal_slot_wall_to_bulk_rth_k_w),
            ("R_ideal_plate_to_inlet_K_W", result.ideal_slot_to_inlet_rth_k_w),
            ("R_calibrated_plate_to_inlet_K_W", result.calibrated_plate_to_inlet_rth_k_w),
        ):
            if value is not None:
                _out(key, value)
        if result.volume is not None:
            _out("cold_plate_volume_L", result.volume.cold_plate_l)
            _out("complete_loop_volume_L", result.volume.system_l)
            typer.echo("volume_boundary=cold plate + pump + pipes + heat exchanger")
        if result.flow_area_rth_k_w is not None:
            _out("R_flow_area_K_W", result.flow_area_rth_k_w)
        if flow_area_calibration is not None:
            typer.echo(f"flow_area_calibration={flow_area_calibration}")
        typer.echo("thermal_reference=bulk coolant; no room-air resistance conversion")
        if result.energy is not None and result.energy.status != "ok":
            raise typer.Exit(1)
