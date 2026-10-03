"""Measured phase benchmarks for M10 performance decisions."""

from __future__ import annotations

import json
import os
import platform
import statistics
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from scipy.sparse.linalg import spsolve

from thermal_cli.baseplate.fdm_solver import (
    _assemble_fdm_matrix,
    _control_volume_bounds,
    _map_fdm_sources,
    solve_fdm,
)
from thermal_cli.baseplate.types import BaseplateConfig, Device

PHASE_NAMES = (
    "parsing",
    "source_mapping",
    "assembly",
    "factorization_solve",
    "femm",
    "orchestration",
)


@dataclass(frozen=True)
class PhaseTiming:
    phase: str
    status: str
    iterations: int
    median_s: float | None
    p95_s: float | None
    min_s: float | None
    operations_per_invocation: int
    operations_per_s: float | None


@dataclass(frozen=True)
class PerformanceReport:
    created_utc: str
    runtime: Mapping[str, Any]
    workload: Mapping[str, Any]
    iterations: int
    phases: tuple[PhaseTiming, ...]
    orchestration_p95_s: float | None
    latency_target_s: float | None
    optimization_evidence: Mapping[str, Any] | None
    decision: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PerformanceSuiteReport:
    created_utc: str
    workload_matrix: Mapping[str, Any]
    reports: tuple[PerformanceReport, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def benchmark_pipeline(
    *,
    phases: Mapping[str, Callable[[], object]],
    workload: Mapping[str, Any],
    iterations: int = 7,
    warmups: int = 1,
    latency_target_s: float | None = None,
    optimization_evidence: Mapping[str, Any] | None = None,
    phase_operations: Mapping[str, int] | None = None,
) -> PerformanceReport:
    """Measure supplied phases separately and record enough context to repeat them.

    Callbacks are deliberately supplied by the workload adapter so parsing,
    mapping, assembly, solve, FEMM, and orchestration are not conflated.
    Missing phases are recorded explicitly as not_measured.
    """
    _positive_int("iterations", iterations)
    if isinstance(warmups, bool) or int(warmups) != warmups or warmups < 0:
        raise ValueError("warmups must be a nonnegative integer")
    if latency_target_s is not None and (
        not np.isfinite(latency_target_s) or latency_target_s <= 0.0
    ):
        raise ValueError("latency_target_s must be finite and > 0")
    extra = set(phases) - set(PHASE_NAMES)
    if extra:
        raise ValueError(f"unknown benchmark phases: {sorted(extra)}")
    operations = dict(phase_operations or {})
    if set(operations) - set(PHASE_NAMES):
        raise ValueError(
            f"unknown phase operation counts: {sorted(set(operations) - set(PHASE_NAMES))}"
        )
    for phase, count in operations.items():
        _positive_int(f"{phase} operations", count)
    evidence = _validated_optimization_evidence(optimization_evidence)
    for key in ("grid_points", "device_count", "scenario_count"):
        _positive_int(key, workload.get(key))
    timings: list[PhaseTiming] = []
    for phase in PHASE_NAMES:
        callback = phases.get(phase)
        operation_count = operations.get(phase, 1)
        if callback is None:
            timings.append(
                PhaseTiming(phase, "not_measured", 0, None, None, None, operation_count, None)
            )
            continue
        for _ in range(int(warmups)):
            callback()
        samples = []
        for _ in range(int(iterations)):
            started = time.perf_counter()
            callback()
            samples.append(time.perf_counter() - started)
        median = float(statistics.median(samples))
        p95 = float(np.percentile(samples, 95))
        timings.append(
            PhaseTiming(
                phase,
                "measured",
                int(iterations),
                median,
                p95,
                min(samples),
                operation_count,
                operation_count / median if median > 0.0 else None,
            )
        )
    orchestration = next((item for item in timings if item.phase == "orchestration"), None)
    orchestration_p95 = (
        orchestration.p95_s
        if orchestration is not None and orchestration.status == "measured"
        else None
    )
    decision = _decision(timings, latency_target_s, orchestration_p95, evidence)
    return PerformanceReport(
        created_utc=datetime.now(UTC).isoformat(),
        runtime={
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "processor": platform.processor() or "unreported",
            "logical_cpu_count": os.cpu_count(),
            "numpy": np.__version__,
            "scipy": package_version("scipy"),
        },
        workload=dict(workload),
        iterations=int(iterations),
        phases=tuple(timings),
        orchestration_p95_s=orchestration_p95,
        latency_target_s=latency_target_s,
        optimization_evidence=evidence,
        decision=decision,
    )


def write_performance_report(report: PerformanceReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_performance_suite_report(report: PerformanceSuiteReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def benchmark_baseplate_suite(
    *,
    grid_sizes: tuple[int, ...] = (21, 41, 81),
    device_counts: tuple[int, ...] = (1, 4, 16),
    scenario_count: int = 3,
    iterations: int = 5,
    warmups: int = 1,
) -> PerformanceSuiteReport:
    """Measure real parsing/mapping/assembly/solve/orchestration across a workload matrix."""
    if not grid_sizes or not device_counts:
        raise ValueError("grid_sizes and device_counts must not be empty")
    for size in grid_sizes:
        _positive_int("grid size", size)
    for count in device_counts:
        _positive_int("device count", count)
    _positive_int("scenario_count", scenario_count)

    reports = []
    for grid_size in grid_sizes:
        for device_count in device_counts:
            yaml_text = _baseplate_yaml(grid_size, device_count)
            config = _config_from_yaml(yaml_text)
            lx, ly = config.lx, config.ly
            x_grid = np.linspace(0.0, lx, config.nx)
            y_grid = np.linspace(0.0, ly, config.ny)
            x_bounds = _control_volume_bounds(x_grid, lx)
            y_bounds = _control_volume_bounds(y_grid, ly)
            x_widths = np.diff(x_bounds)
            y_widths = np.diff(y_bounds)
            dx = lx / (config.nx - 1)
            dy = ly / (config.ny - 1)
            cell_areas = np.outer(y_widths, x_widths)
            sink_conductance = cell_areas / (config.r_sa * lx * ly)
            sheet_conductance = config.conductivity * config.thickness
            source_power, _, _ = _map_fdm_sources(
                config,
                lx=lx,
                ly=ly,
                x_bounds=x_bounds,
                y_bounds=y_bounds,
            )
            matrix = _assemble_fdm_matrix(
                nx=config.nx,
                ny=config.ny,
                sheet_conductance=sheet_conductance,
                x_widths=x_widths,
                y_widths=y_widths,
                dx=dx,
                dy=dy,
                sink_conductance=sink_conductance,
            )
            right_hand_side = source_power.ravel()

            def parse_phase(yaml_text: str = yaml_text) -> object:
                return _config_from_yaml(yaml_text)

            def mapping_phase(
                config: BaseplateConfig = config,
                lx: float = lx,
                ly: float = ly,
            ) -> object:
                fresh_x_grid = np.linspace(0.0, lx, config.nx)
                fresh_y_grid = np.linspace(0.0, ly, config.ny)
                return _map_fdm_sources(
                    config,
                    lx=lx,
                    ly=ly,
                    x_bounds=_control_volume_bounds(fresh_x_grid, lx),
                    y_bounds=_control_volume_bounds(fresh_y_grid, ly),
                )

            def assembly_phase(
                nx: int = config.nx,
                ny: int = config.ny,
                sheet_conductance: float = sheet_conductance,
                x_widths: np.ndarray = x_widths,
                y_widths: np.ndarray = y_widths,
                dx: float = dx,
                dy: float = dy,
                sink_conductance: np.ndarray = sink_conductance,
            ) -> object:
                return _assemble_fdm_matrix(
                    nx=nx,
                    ny=ny,
                    sheet_conductance=sheet_conductance,
                    x_widths=x_widths,
                    y_widths=y_widths,
                    dx=dx,
                    dy=dy,
                    sink_conductance=sink_conductance,
                )

            def solve_phase(
                matrix: Any = matrix, right_hand_side: np.ndarray = right_hand_side
            ) -> object:
                return spsolve(matrix, right_hand_side)

            def orchestration_phase(config: BaseplateConfig = config) -> object:
                return tuple(solve_fdm(config) for _ in range(scenario_count))

            reports.append(
                benchmark_pipeline(
                    phases={
                        "parsing": parse_phase,
                        "source_mapping": mapping_phase,
                        "assembly": assembly_phase,
                        "factorization_solve": solve_phase,
                        "orchestration": orchestration_phase,
                    },
                    workload={
                        "workload": "conservative 2.5D baseplate",
                        "grid_shape": [grid_size, grid_size],
                        "grid_points": grid_size * grid_size,
                        "device_count": device_count,
                        "scenario_count": scenario_count,
                        "orchestration_operation_unit": "complete baseplate scenarios",
                    },
                    iterations=iterations,
                    warmups=warmups,
                    phase_operations={"orchestration": scenario_count},
                )
            )
    return PerformanceSuiteReport(
        created_utc=datetime.now(UTC).isoformat(),
        workload_matrix={
            "grid_sizes": list(grid_sizes),
            "device_counts": list(device_counts),
            "repeated_scenarios_per_orchestration": scenario_count,
            "iterations": iterations,
            "warmups": warmups,
            "latency_target_s": None,
        },
        reports=tuple(reports),
    )


def _baseplate_yaml(grid_size: int, device_count: int) -> str:
    columns = int(np.ceil(np.sqrt(device_count)))
    rows = int(np.ceil(device_count / columns))
    devices = []
    for index in range(device_count):
        column, row = index % columns, index // columns
        cell_width, cell_height = 0.08 / columns, 0.04 / rows
        devices.append(
            {
                "name": f"Q{index + 1}",
                "x": (column + 0.5) * cell_width,
                "y": (row + 0.5) * cell_height,
                "width": min(0.008, cell_width * 0.5),
                "height": min(0.006, cell_height * 0.5),
                "power": 5.0,
                "r_jc": 0.1,
                "r_interface": 0.02,
            }
        )
    return yaml.safe_dump(
        {
            "lx": 0.08,
            "ly": 0.04,
            "thickness": 0.005,
            "conductivity": 210.0,
            "r_sa": 0.25,
            "t_ambient": 293.15,
            "nx": grid_size,
            "ny": grid_size,
            "devices": devices,
        },
        sort_keys=True,
    )


def _config_from_yaml(yaml_text: str) -> BaseplateConfig:
    data = yaml.safe_load(yaml_text)
    if not isinstance(data, dict):
        raise ValueError("baseplate benchmark YAML must contain a mapping")
    devices = [Device(**device) for device in data.pop("devices")]
    return BaseplateConfig(devices=devices, **data)


def _decision(
    timings: list[PhaseTiming],
    target_s: float | None,
    orchestration_p95_s: float | None,
    optimization_evidence: Mapping[str, Any] | None,
) -> str:
    if target_s is None:
        return "no_user_latency_target_declared; no Rust recommendation"
    if orchestration_p95_s is None:
        return "orchestration_not_measured; performance decision pending"
    if orchestration_p95_s <= target_s:
        return "Python_meets_declared_orchestration_latency_target"
    if optimization_evidence is None:
        return "target_missed; profile_and_optimize_Python_before_considering_Rust"
    optimized_phase = optimization_evidence["optimized_phase"]
    kernel = next(
        (
            timing
            for timing in timings
            if timing.phase == optimized_phase
            and timing.status == "measured"
            and timing.p95_s is not None
            and timing.p95_s > target_s
        ),
        None,
    )
    if kernel is None or kernel.p95_s is None or kernel.p95_s <= target_s:
        return "target_missed_without_narrow_numerical_kernel_evidence; no Rust recommendation"
    return f"consider_narrow_Rust_{kernel.phase}_only_with_same_interface_and_Python_parity"


def _validated_optimization_evidence(
    evidence: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    if evidence is None:
        return None
    applied = evidence.get("optimization_applied")
    parity = evidence.get("python_parity_verified")
    phase = evidence.get("optimized_phase")
    parity_evidence = evidence.get("python_parity_evidence")
    if (
        not isinstance(applied, str)
        or not applied.strip()
        or phase not in ("assembly", "factorization_solve")
        or parity is not True
        or not isinstance(parity_evidence, str)
        or not parity_evidence.strip()
    ):
        raise ValueError(
            "optimization_evidence requires an assembly or factorization_solve "
            "optimized_phase, nonempty optimization_applied and python_parity_evidence, "
            "and python_parity_verified=true"
        )
    serialized = dict(evidence)
    try:
        json.dumps(serialized, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("optimization_evidence must contain JSON-safe values") from exc
    return serialized


def _positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)
