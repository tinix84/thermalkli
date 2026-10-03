"""M9 physical transient simulation commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import numpy as np
import typer
import yaml

from thermal_cli.transient.rc_network import (
    NodalRCNetwork,
    PowerWaveform,
    intelec2003_chip8_cauer,
    onsemi_and8215_b01_network,
)


def register_transient_commands(app: typer.Typer) -> None:
    @app.command("transient-sim")  # type: ignore[untyped-decorator]
    def transient_sim_cmd(
        config: Annotated[Path, typer.Option("--config", help="Transient simulation YAML")],
    ) -> None:
        """Run a grounded nodal RC/Cauer transient with independent power inputs."""
        if not config.exists():
            typer.echo(f"Error: config file not found: {config}", err=True)
            raise typer.Exit(1)
        try:
            raw: Any = yaml.safe_load(config.read_text(encoding="utf-8"))
            net_raw = raw["network"]
            kind = net_raw["kind"]
            if kind == "onsemi_and8215_b01":
                network = onsemi_and8215_b01_network(
                    ambient_k=float(net_raw.get("ambient_k", 293.15))
                )
            elif kind == "intelec2003_chip8_cauer":
                network = intelec2003_chip8_cauer(ambient_k=float(net_raw.get("ambient_k", 293.15)))
            elif kind == "cauer_ladder":
                network = NodalRCNetwork.cauer_ladder(
                    resistances_k_w=net_raw["resistances_k_w"],
                    capacitances_j_k=net_raw["capacitances_j_k"],
                    ambient_k=float(net_raw.get("ambient_k", 293.15)),
                    minimum_supported_pulse_s=(
                        float(net_raw["minimum_supported_pulse_s"])
                        if "minimum_supported_pulse_s" in net_raw
                        else None
                    ),
                    fit_reference=str(net_raw.get("fit_reference", "config-supplied Cauer ladder")),
                )
            else:
                raise ValueError(f"unsupported network kind: {kind}")
            waveform = PowerWaveform(
                times_s=np.asarray(raw["waveform"]["times_s"], dtype=float),
                powers_w=np.asarray(raw["waveform"]["powers_w"], dtype=float),
            )
            initial = raw.get("initial_temperatures_k")
            if raw.get("periodic", False):
                max_cycles = raw.get("max_cycles", 1000)
                if isinstance(max_cycles, bool) or not isinstance(max_cycles, int):
                    raise ValueError("max_cycles must be a positive integer")
                result = network.periodic_steady_state(
                    waveform,
                    initial_temperatures_k=initial,
                    absolute_tolerance_k=float(raw.get("absolute_tolerance_k", 1e-6)),
                    relative_tolerance=float(raw.get("relative_tolerance", 1e-6)),
                    max_cycles=max_cycles,
                )
                transient = result.transient
                typer.echo(f"periodic_converged={'true' if result.converged else 'false'}")
                typer.echo(f"cycles={result.cycles}")
                typer.echo(f"max_cycle_delta_K={result.max_cycle_delta_k:.9g}")
            else:
                transient = network.simulate(waveform, initial_temperatures_k=initial)
        except (KeyError, TypeError, ValueError) as exc:
            typer.echo(f"Error: invalid transient config: {exc}", err=True)
            raise typer.Exit(2) from exc

        typer.echo("time_s\t" + "\t".join(transient.output_nodes))
        for time_s, outputs in zip(transient.times_s, transient.output_temperatures_k, strict=True):
            typer.echo(f"{time_s:.9g}\t" + "\t".join(f"{float(value):.9g}" for value in outputs))
