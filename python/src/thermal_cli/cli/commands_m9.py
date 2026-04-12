"""M9 CLI commands: optimize-fin, multi-sim."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import yaml


def register_all(app: typer.Typer) -> None:
    """Register M9 commands on the Typer app."""

    @app.command("optimize-fin")
    def optimize_fin_cmd(
        config: Annotated[Path, typer.Option("--config", help="Sweep YAML config")],
    ) -> None:
        """Grid-sweep extruded-fin geometry and report the best Rth."""
        from thermal_cli.sweep.dsl import parse_sweep_config
        from thermal_cli.sweep.optimize_fin import (
            FinGeometrySweepConfig,
            optimize_fin_geometry,
        )

        if not config.exists():
            typer.echo(f"Error: config file not found: {config}", err=True)
            raise typer.Exit(1)

        with open(config) as fh:
            raw = yaml.safe_load(fh)

        axes, fixed = parse_sweep_config(raw)
        cfg = FinGeometrySweepConfig(
            axes={name: list(vals) for name, vals in axes.items()},
            fixed=fixed,
        )
        result = optimize_fin_geometry(cfg)

        # Print all combinations
        typer.echo("Sweep results:")
        header = "\t".join(result.axis_names) + "\tr_th_total"
        typer.echo(header)
        typer.echo("-" * len(header))
        for idx_tuple in _iter_indices(result.values.shape):
            axis_cells = [
                f"{vals[i]:g}"
                for vals, i in zip(result.axis_values, idx_tuple, strict=True)
            ]
            out_cell = f"{result.values[idx_tuple]:.6f}"
            typer.echo("\t".join([*axis_cells, out_cell]))

        best = result.argmin()
        typer.echo("")
        typer.echo(f"best r_th_total={result.min():.6f} at {best}")

    @app.command("multi-sim")
    def multi_sim_cmd(
        config: Annotated[Path, typer.Option("--config", help="Scenarios YAML config")],
    ) -> None:
        """Run baseplate FDM solver on each scenario and tabulate peak temperatures."""
        from thermal_cli.sweep.multi_sim import load_scenarios_from_dict, run_multi_sim

        if not config.exists():
            typer.echo(f"Error: config file not found: {config}", err=True)
            raise typer.Exit(1)

        with open(config) as fh:
            raw = yaml.safe_load(fh)

        scenarios = load_scenarios_from_dict(raw)
        result = run_multi_sim(scenarios)

        typer.echo("name\tt_max\tt_mean\tt_j_max")
        typer.echo("-" * 48)
        for row in result.rows:
            typer.echo(
                f"{row.name}\t{row.t_max:.2f}\t{row.t_mean:.2f}\t{row.t_j_max:.2f}"
            )


def _iter_indices(shape: tuple[int, ...]):
    """Yield every index tuple for the given shape (row-major order)."""
    from itertools import product

    yield from product(*[range(n) for n in shape])
