"""Consistent second-release reference-case reporting command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer


def register_validation_commands(app: typer.Typer) -> None:
    @app.command("validation-report")
    def validation_report_cmd(
        output: Annotated[
            Path,
            typer.Option("--output", help="JSON output path for executed reference cases"),
        ],
    ) -> None:
        """Run accepted reference and behavior cases and write a validation report."""
        from thermal_cli.validation.workflow import (
            built_in_reference_scenarios,
            run_scenarios,
            write_report,
        )

        report = run_scenarios(built_in_reference_scenarios())
        try:
            write_report(report, output)
        except OSError as exc:
            typer.echo(f"Error: could not write report: {exc}", err=True)
            raise typer.Exit(1) from exc
        typer.echo(f"report={output}")
        failed = False
        for row in report.records:
            typer.echo(
                f"{row.case_id}\tstatus={row.status}\texecution={row.execution_status}"
                f"\tacceptance={row.acceptance_status}\t{row.evidence_status}"
            )
            if row.error:
                typer.echo(f"  error={row.error}")
            if row.acceptance_error:
                typer.echo(f"  acceptance_error={row.acceptance_error}")
            failed = failed or row.execution_status == "failed" or row.acceptance_status == "failed"
        if failed:
            raise typer.Exit(1)

    @app.command("performance-report")
    def performance_report_cmd(
        output: Annotated[
            Path,
            typer.Option("--output", help="JSON output path for the workload benchmark matrix"),
        ],
        iterations: Annotated[
            int,
            typer.Option("--iterations", min=1, help="Timed samples per phase and workload"),
        ] = 5,
    ) -> None:
        """Benchmark the representative baseplate workload matrix by phase."""
        from thermal_cli.benchmarks.performance import (
            benchmark_baseplate_suite,
            write_performance_suite_report,
        )

        report = benchmark_baseplate_suite(iterations=iterations)
        try:
            write_performance_suite_report(report, output)
        except OSError as exc:
            typer.echo(f"Error: could not write report: {exc}", err=True)
            raise typer.Exit(1) from exc
        typer.echo(f"report={output}")
        for row in report.reports:
            orchestration_ms = (
                row.orchestration_p95_s * 1000.0 if row.orchestration_p95_s is not None else None
            )
            typer.echo(
                f"grid={row.workload['grid_shape']} devices={row.workload['device_count']} "
                f"scenarios={row.workload['scenario_count']} "
                f"orchestration_p95_ms={orchestration_ms}"
            )
