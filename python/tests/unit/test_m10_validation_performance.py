from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from thermal_cli.benchmarks.performance import (
    benchmark_baseplate_suite,
    benchmark_pipeline,
)
from thermal_cli.cli.main import app
from thermal_cli.validation import workflow
from thermal_cli.validation.workflow import Scenario, run_scenarios

runner = CliRunner()


def test_validation_report_cli_writes_all_accepted_scenarios(tmp_path: Path) -> None:
    destination = tmp_path / "registry.json"
    result = runner.invoke(app, ["validation-report", "--output", str(destination)])

    assert result.exit_code == 0, result.output
    payload = json.loads(destination.read_text(encoding="utf-8"))
    rows = {row["case_id"]: row for row in payload["records"]}
    assert {"B01", "B02", "B03", "B05", "B06", "B07", "B08", "M8-ENERGY", "M9-DYNAMICS"} <= {*rows}
    assert rows["B05"]["acceptance_status"] == "passed"
    assert rows["B05"]["status"] == "passed"
    assert rows["B05"]["outputs"]["flow_area_rth_k_w"] is not None
    assert rows["B05"]["outputs"]["calibrated_plate_to_inlet_rth_k_w"] is not None
    assert rows["B03"]["status"] == "recorded"
    assert rows["B06"]["acceptance_status"] == "not_checked"
    assert rows["B07"]["acceptance_status"] == "passed"
    assert rows["B07"]["outputs"]["measured_resistance_relative_error"] <= 0.20
    assert rows["B08"]["acceptance_status"] == "passed"
    assert (
        rows["B08"]["outputs"]["unconstrained_model"]["resistance_k_w"]
        != rows["B08"]["outputs"]["source_reported_theoretical"]["resistance_k_w"]
    )
    assert "waveform_grid_refinement_delta_at_0_1_s_k" in rows["M9-DYNAMICS"]["outputs"]


def test_validation_report_cli_fails_after_acceptance_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenario = Scenario(
        case_id="synthetic-failure",
        capability="acceptance failure behavior",
        source="unit test",
        conditions={},
        run=lambda: {"accepted": False},
        evidence_status="executed",
        acceptance_criteria="accepted must be true",
        acceptance=lambda output: output["accepted"] is True,
    )
    monkeypatch.setattr(workflow, "built_in_reference_scenarios", lambda: (scenario,))
    destination = tmp_path / "failed.json"

    result = runner.invoke(app, ["validation-report", "--output", str(destination)])

    assert result.exit_code == 1
    assert destination.exists()
    row = json.loads(destination.read_text(encoding="utf-8"))["records"][0]
    assert row["execution_status"] == "passed"
    assert row["acceptance_status"] == "failed"
    assert row["status"] == "failed"


def test_run_scenarios_records_execution_failure() -> None:
    scenario = Scenario(
        case_id="synthetic-error",
        capability="execution failure behavior",
        source="unit test",
        conditions={},
        run=lambda: (_ for _ in ()).throw(RuntimeError("fixture failed")),
        evidence_status="source evidence",
    )

    record = run_scenarios((scenario,)).records[0]

    assert record.execution_status == "failed"
    assert record.acceptance_status == "not_checked"
    assert record.status == "failed"
    assert record.error == "RuntimeError: fixture failed"


def test_run_scenarios_separates_acceptance_predicate_errors() -> None:
    scenario = Scenario(
        case_id="synthetic-acceptance-error",
        capability="acceptance error behavior",
        source="unit test",
        conditions={},
        run=lambda: {"executed": True},
        evidence_status="executed",
        acceptance_criteria="predicate raises if required output is missing",
        acceptance=lambda output: output["missing_key"] is True,
    )

    record = run_scenarios((scenario,)).records[0]

    assert record.execution_status == "passed"
    assert record.acceptance_status == "failed"
    assert record.status == "failed"
    assert record.outputs == {"executed": True}
    assert record.error is None
    assert "KeyError" in (record.acceptance_error or "")


def test_baseplate_benchmark_measures_real_phases() -> None:
    report = benchmark_baseplate_suite(
        grid_sizes=(9,),
        device_counts=(1,),
        scenario_count=2,
        iterations=1,
        warmups=0,
    )

    assert len(report.reports) == 1
    row = report.reports[0]
    phases = {phase.phase: phase for phase in row.phases}
    for phase in ("parsing", "source_mapping", "assembly", "factorization_solve", "orchestration"):
        assert phases[phase].status == "measured"
    assert phases["femm"].status == "not_measured"
    assert phases["orchestration"].operations_per_invocation == 2
    assert phases["orchestration"].operations_per_s is not None
    assert row.latency_target_s is None
    assert row.decision == "no_user_latency_target_declared; no Rust recommendation"


def test_performance_decision_retains_optimization_evidence() -> None:
    report = benchmark_pipeline(
        phases={"assembly": lambda: sum(range(100)), "orchestration": lambda: sum(range(100))},
        workload={"grid_points": 100, "device_count": 1, "scenario_count": 1},
        iterations=2,
        warmups=0,
        latency_target_s=1e-12,
        optimization_evidence={
            "optimized_phase": "assembly",
            "optimization_applied": "vectorized one repeated stencil operation",
            "python_parity_verified": True,
            "python_parity_evidence": "test_m10_validation_performance.py passed",
        },
    )

    assert report.optimization_evidence is not None
    assert report.to_dict()["optimization_evidence"]["python_parity_verified"] is True
    assert report.decision.startswith("consider_narrow_Rust_assembly")


def test_performance_decision_rejects_unverifiable_optimization_claim() -> None:
    with pytest.raises(ValueError, match="python_parity_verified"):
        benchmark_pipeline(
            phases={},
            workload={"grid_points": 1, "device_count": 1, "scenario_count": 1},
            iterations=1,
            warmups=0,
            optimization_evidence={
                "optimized_phase": "assembly",
                "optimization_applied": "changed loop",
                "python_parity_verified": False,
                "python_parity_evidence": "not verified",
            },
        )
