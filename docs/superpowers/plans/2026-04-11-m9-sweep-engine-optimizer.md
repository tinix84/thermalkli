# M9 — Parametric Sweep Engine + `optimize-fin` / `multi-sim`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the parametric sweep capability from `mfiles/Thermal/Optimizer/extrudedFinHeatsinkCalculations.m` and `mfiles/SoftwareTermico/Simulazione_multipla/` into a unified Python sweep engine and expose it via two new CLI commands: `optimize-fin` (grid-sweep extruded-fin geometry → find min Rth) and `multi-sim` (evaluate a list of baseplate scenarios via the existing M6 FDM solver).

**Architecture:** A new `thermal_cli/sweep/` subpackage provides:
1. `engine.py` — pure `run_sweep(func, axes, fixed)` that evaluates `func(**axis_values, **fixed)` over the Cartesian product of axis values and returns a `SweepResult` with the ndarray of outputs and axis metadata.
2. `dsl.py` — a YAML sweep DSL. Axis values can be given as `values: [...]`, `linspace: {start, stop, steps}`, or `range: {start, stop, step}`.
3. `optimize_fin.py` — thin adapter that wraps `ExtrudedFin(...).thermal_resistance(...)` for the sweep engine, picking `r_th_total` as the scalar output.
4. `multi_sim.py` — thin adapter that loads a list of `BaseplateConfig` scenarios from YAML and runs `baseplate.fdm_solver.solve_fdm` on each, reporting per-scenario `t_j_max`.

Two CLI commands wire into the existing Typer app through `cli/commands_m9.py`:
- `optimize-fin --config sweep.yaml` — prints a table of every combination plus the minimum.
- `multi-sim --config scenarios.yaml` — prints one row per scenario with `t_j_max` and per-device peaks.

The Octave `Simulazione_multipla`'s source-repositioning feedback loop (auto-move sources when `T > Tmax`) is **out of scope** — M9 ships only the static-evaluation loop, which matches the design-spec wording "parametric sims". Repositioning is filed as a follow-up in the PRD.

**Tech Stack:** Python 3.11+, numpy, pyyaml, pydantic v2, pytest, typer.

**Octave source → Python target mapping:**

| Octave source | Python target |
|---|---|
| `mfiles/Thermal/Optimizer/extrudedFinHeatsinkCalculations.m` (51×8 grid loop) | `thermal_cli/sweep/optimize_fin.py::optimize_fin_geometry()` |
| `mfiles/SoftwareTermico/Simulazione_multipla/Dati_multipla.m` (scenario list) | YAML scenarios in `multi_sim.py::load_scenarios()` |
| `mfiles/SoftwareTermico/Simulazione_multipla/Simulazione_Multipla.m` (main loop) | `thermal_cli/sweep/multi_sim.py::run_multi_sim()` |
| `cli/commands_m9.py::optimize_fin_cmd` | new CLI |
| `cli/commands_m9.py::multi_sim_cmd` | new CLI |

**Key design decisions (agreed 2026-04-11):**

- YAML-native sweep DSL. No new `.m` scripts, no interactive menus.
- Sweep engine is a pure function — no caching, no parallelism, no progress bar. Workloads in scope are small (grids ≤ 10³ combinations).
- Grid sweep only. SciPy-based gradient optimizers are filed for a later milestone.
- `optimize-fin` and `multi-sim` use the existing M4 (`ExtrudedFin`) and M6 (`solve_fdm`) entry points as-is; no new physics.
- Output format: human-readable tables on stdout + optional `--output <path.json>` to dump full SweepResult.
- The `SweepResult.values` ndarray has shape `(len(axis_0), len(axis_1), ..., len(axis_n))` (row-major, insertion order).

---

## File Structure

### New files

```
python/src/thermal_cli/sweep/
├── __init__.py              # re-exports
├── engine.py                # SweepResult + run_sweep
├── dsl.py                   # YAML parser for sweep specs
├── optimize_fin.py          # ExtrudedFin wrapper + min-Rth finder
└── multi_sim.py             # BaseplateConfig list runner

python/src/thermal_cli/cli/commands_m9.py

python/tests/unit/
├── test_sweep_engine.py
├── test_sweep_dsl.py
├── test_optimize_fin.py
├── test_multi_sim.py
└── test_cli_m9.py

python/tests/literature/test_lit_sweep.py

python/tests/regression/fixtures/
├── optimize_fin/basic.yaml
└── multi_sim/two_scenarios.yaml

python/tests/regression/helpers.py    (modify: add 2 wrappers)
python/src/thermal_cli/cli/main.py    (modify: register_m9)
```

---

## Task 1: Sweep engine core (`engine.py`)

**Files:**
- Create: `python/src/thermal_cli/sweep/__init__.py`
- Create: `python/src/thermal_cli/sweep/engine.py`
- Test: `python/tests/unit/test_sweep_engine.py`

- [ ] **Step 1: Write failing tests**

Create `python/tests/unit/test_sweep_engine.py`:

```python
"""Tests for thermal_cli.sweep.engine."""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.sweep.engine import SweepResult, run_sweep


class TestRunSweep:
    def test_single_axis_scalar_output(self):
        """y = 2*x over x in [1, 2, 3]."""
        res = run_sweep(
            func=lambda x: 2 * x,
            axes={"x": [1.0, 2.0, 3.0]},
        )
        assert isinstance(res, SweepResult)
        assert res.axis_names == ("x",)
        assert res.values.shape == (3,)
        np.testing.assert_array_equal(res.values, [2.0, 4.0, 6.0])

    def test_two_axes_cartesian_product(self):
        """z = x + y over 2 x 3 grid."""
        res = run_sweep(
            func=lambda x, y: x + y,
            axes={"x": [1.0, 2.0], "y": [10.0, 20.0, 30.0]},
        )
        assert res.axis_names == ("x", "y")
        assert res.values.shape == (2, 3)
        np.testing.assert_array_equal(
            res.values,
            [[11.0, 21.0, 31.0], [12.0, 22.0, 32.0]],
        )

    def test_fixed_kwargs_forwarded(self):
        """func(x=..., k=5) — k is fixed, not swept."""
        res = run_sweep(
            func=lambda x, k: x * k,
            axes={"x": [1.0, 2.0]},
            fixed={"k": 5.0},
        )
        np.testing.assert_array_equal(res.values, [5.0, 10.0])

    def test_axis_values_stored(self):
        res = run_sweep(
            func=lambda x: x,
            axes={"x": [1.0, 2.0, 3.0]},
        )
        np.testing.assert_array_equal(res.axis_values[0], [1.0, 2.0, 3.0])

    def test_argmin_returns_dict_of_axis_values(self):
        """argmin() gives the axis values at the minimum output."""
        res = run_sweep(
            func=lambda x, y: (x - 2) ** 2 + (y - 5) ** 2,
            axes={"x": [0.0, 1.0, 2.0, 3.0], "y": [3.0, 4.0, 5.0, 6.0]},
        )
        assert res.argmin() == {"x": 2.0, "y": 5.0}

    def test_argmax_returns_dict_of_axis_values(self):
        res = run_sweep(
            func=lambda x: -((x - 3) ** 2),
            axes={"x": [0.0, 1.0, 2.0, 3.0, 4.0]},
        )
        assert res.argmax() == {"x": 3.0}

    def test_empty_axes_raises(self):
        with pytest.raises(ValueError, match="at least one axis"):
            run_sweep(func=lambda: 0.0, axes={})

    def test_empty_axis_values_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            run_sweep(func=lambda x: x, axes={"x": []})

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            run_sweep(lambda x: x, {"x": [1]})  # type: ignore[misc]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_sweep_engine.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Create `sweep/__init__.py`**

Create `python/src/thermal_cli/sweep/__init__.py`:

```python
"""Parametric sweep engine and optimizer (M9)."""

from thermal_cli.sweep.engine import SweepResult, run_sweep

__all__ = ["SweepResult", "run_sweep"]
```

- [ ] **Step 4: Implement `sweep/engine.py`**

Create `python/src/thermal_cli/sweep/engine.py`:

```python
"""Cartesian-product sweep engine.

Evaluates a callable over the Cartesian product of axis values and
packages the results as a ``SweepResult`` with axis metadata.

Scope is intentionally small: no caching, no parallelism, no progress
bar. Designed for grids up to ~10^3 combinations.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from itertools import product
from typing import Any

import numpy as np


@dataclass
class SweepResult:
    """Result of a grid sweep.

    Attributes
    ----------
    axis_names : tuple[str, ...]
        Names of the swept axes, in insertion order.
    axis_values : tuple[np.ndarray, ...]
        Values swept along each axis (same order as ``axis_names``).
    values : np.ndarray
        Output array with shape ``tuple(len(v) for v in axis_values)``.
    """

    axis_names: tuple[str, ...]
    axis_values: tuple[np.ndarray, ...]
    values: np.ndarray
    fixed: dict[str, Any] = field(default_factory=dict)

    def argmin(self) -> dict[str, float]:
        """Return axis values at the minimum output."""
        idx = np.unravel_index(int(np.argmin(self.values)), self.values.shape)
        return {
            name: float(vals[i])
            for name, vals, i in zip(self.axis_names, self.axis_values, idx, strict=True)
        }

    def argmax(self) -> dict[str, float]:
        """Return axis values at the maximum output."""
        idx = np.unravel_index(int(np.argmax(self.values)), self.values.shape)
        return {
            name: float(vals[i])
            for name, vals, i in zip(self.axis_names, self.axis_values, idx, strict=True)
        }

    def min(self) -> float:
        return float(np.min(self.values))

    def max(self) -> float:
        return float(np.max(self.values))


def run_sweep(
    *,
    func: Callable[..., float],
    axes: Mapping[str, Sequence[float]],
    fixed: Mapping[str, Any] | None = None,
) -> SweepResult:
    """Evaluate ``func`` over the Cartesian product of ``axes`` values.

    Parameters
    ----------
    func : Callable
        Takes one keyword argument per axis name plus any ``fixed`` kwargs.
        Must return a scalar float.
    axes : Mapping[str, Sequence[float]]
        Axis name → sequence of values. Insertion order defines the
        output array's axis order.
    fixed : Mapping[str, Any], optional
        Keyword arguments forwarded unchanged to every call.

    Returns
    -------
    SweepResult
    """
    if not axes:
        raise ValueError("run_sweep needs at least one axis")
    for name, vals in axes.items():
        if len(vals) == 0:
            raise ValueError(f"axis {name!r} must be non-empty")

    axis_names = tuple(axes.keys())
    axis_values = tuple(np.asarray(list(vals), dtype=float) for vals in axes.values())
    shape = tuple(len(v) for v in axis_values)

    fixed_kw = dict(fixed) if fixed else {}
    out = np.empty(shape, dtype=float)

    for idx_tuple in product(*[range(n) for n in shape]):
        call_kw = {name: float(vals[i]) for name, vals, i in zip(axis_names, axis_values, idx_tuple, strict=True)}
        out[idx_tuple] = float(func(**call_kw, **fixed_kw))

    return SweepResult(
        axis_names=axis_names,
        axis_values=axis_values,
        values=out,
        fixed=fixed_kw,
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_sweep_engine.py -v`
Expected: all PASS (9 tests)

- [ ] **Step 6: Commit**

```bash
git add python/src/thermal_cli/sweep/__init__.py \
       python/src/thermal_cli/sweep/engine.py \
       python/tests/unit/test_sweep_engine.py
git commit -m "feat(m9): add sweep engine core (run_sweep, SweepResult)"
```

---

## Task 2: Sweep YAML DSL (`dsl.py`)

**Files:**
- Create: `python/src/thermal_cli/sweep/dsl.py`
- Modify: `python/src/thermal_cli/sweep/__init__.py`
- Test: `python/tests/unit/test_sweep_dsl.py`

**Depends on:** Task 1

- [ ] **Step 1: Write failing tests**

Create `python/tests/unit/test_sweep_dsl.py`:

```python
"""Tests for thermal_cli.sweep.dsl."""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.sweep.dsl import parse_axis_spec, parse_sweep_config


class TestParseAxisSpec:
    def test_explicit_values(self):
        vals = parse_axis_spec({"values": [1.0, 2.0, 3.0]})
        np.testing.assert_array_equal(vals, [1.0, 2.0, 3.0])

    def test_linspace(self):
        vals = parse_axis_spec({"linspace": {"start": 0.0, "stop": 1.0, "steps": 5}})
        np.testing.assert_allclose(vals, [0.0, 0.25, 0.5, 0.75, 1.0])

    def test_range_inclusive_of_stop(self):
        """``range`` uses numpy.arange and then appends stop if absent."""
        vals = parse_axis_spec({"range": {"start": 0.0, "stop": 1.0, "step": 0.25}})
        np.testing.assert_allclose(vals, [0.0, 0.25, 0.5, 0.75, 1.0])

    def test_scalar_becomes_single_value(self):
        vals = parse_axis_spec(2.5)
        np.testing.assert_array_equal(vals, [2.5])

    def test_list_becomes_values(self):
        vals = parse_axis_spec([1, 2, 3])
        np.testing.assert_array_equal(vals, [1.0, 2.0, 3.0])

    def test_unknown_key_raises(self):
        with pytest.raises(ValueError, match="unknown"):
            parse_axis_spec({"banana": [1, 2]})

    def test_linspace_missing_key_raises(self):
        with pytest.raises(ValueError, match="start"):
            parse_axis_spec({"linspace": {"stop": 1.0, "steps": 5}})


class TestParseSweepConfig:
    def test_basic(self):
        cfg = {
            "axes": {
                "x": [1.0, 2.0],
                "y": {"linspace": {"start": 0.0, "stop": 10.0, "steps": 3}},
            },
            "fixed": {"k": 5.0},
        }
        axes, fixed = parse_sweep_config(cfg)
        assert list(axes.keys()) == ["x", "y"]
        np.testing.assert_array_equal(axes["x"], [1.0, 2.0])
        np.testing.assert_allclose(axes["y"], [0.0, 5.0, 10.0])
        assert fixed == {"k": 5.0}

    def test_missing_axes_raises(self):
        with pytest.raises(ValueError, match="axes"):
            parse_sweep_config({"fixed": {}})

    def test_missing_fixed_is_empty_dict(self):
        axes, fixed = parse_sweep_config({"axes": {"x": [1, 2]}})
        assert fixed == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_sweep_dsl.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `sweep/dsl.py`**

Create `python/src/thermal_cli/sweep/dsl.py`:

```python
"""YAML sweep DSL parser.

Supported axis specs::

    x: [1.0, 2.0, 3.0]                      # explicit list
    x: 2.5                                  # scalar (single-value axis)
    x: {values: [1.0, 2.0, 3.0]}            # explicit via dict
    x: {linspace: {start: 0, stop: 1, steps: 5}}
    x: {range: {start: 0, stop: 1, step: 0.25}}

A full sweep config::

    axes:
      thick_heatsink: {linspace: {start: 0.003, stop: 0.013, steps: 11}}
      thick_wall: [0.0005, 0.0006, 0.0007]
    fixed:
      width_channel: 0.00105
      k_sink: 180.0
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np


def parse_axis_spec(spec: Any) -> np.ndarray:
    """Turn a YAML axis spec into a 1-D numpy array of axis values."""
    if isinstance(spec, (int, float)):
        return np.asarray([float(spec)])
    if isinstance(spec, list):
        return np.asarray([float(v) for v in spec])
    if not isinstance(spec, Mapping):
        raise ValueError(f"unknown axis spec type: {type(spec).__name__}")

    if "values" in spec:
        return np.asarray([float(v) for v in spec["values"]])
    if "linspace" in spec:
        ls = spec["linspace"]
        for key in ("start", "stop", "steps"):
            if key not in ls:
                raise ValueError(f"linspace missing required key: {key}")
        return np.linspace(float(ls["start"]), float(ls["stop"]), int(ls["steps"]))
    if "range" in spec:
        rg = spec["range"]
        for key in ("start", "stop", "step"):
            if key not in rg:
                raise ValueError(f"range missing required key: {key}")
        start = float(rg["start"])
        stop = float(rg["stop"])
        step = float(rg["step"])
        vals = np.arange(start, stop + 0.5 * step, step)
        return vals

    raise ValueError(f"unknown axis spec keys: {list(spec.keys())}")


def parse_sweep_config(cfg: Mapping[str, Any]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Parse a full sweep config into ``(axes, fixed)``.

    Returns
    -------
    axes : dict[str, np.ndarray]
        Axis name → values, insertion order preserved.
    fixed : dict[str, Any]
        Fixed keyword arguments.
    """
    if "axes" not in cfg:
        raise ValueError("sweep config requires an 'axes' key")
    axes_raw = cfg["axes"]
    if not isinstance(axes_raw, Mapping) or not axes_raw:
        raise ValueError("'axes' must be a non-empty mapping")

    axes: dict[str, np.ndarray] = {}
    for name, spec in axes_raw.items():
        axes[name] = parse_axis_spec(spec)

    fixed = dict(cfg.get("fixed", {}))
    return axes, fixed
```

- [ ] **Step 4: Update `sweep/__init__.py`**

Update `python/src/thermal_cli/sweep/__init__.py` to also re-export the DSL:

```python
"""Parametric sweep engine and optimizer (M9)."""

from thermal_cli.sweep.dsl import parse_axis_spec, parse_sweep_config
from thermal_cli.sweep.engine import SweepResult, run_sweep

__all__ = [
    "SweepResult",
    "parse_axis_spec",
    "parse_sweep_config",
    "run_sweep",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_sweep_dsl.py -v`
Expected: all PASS (10 tests)

- [ ] **Step 6: Commit**

```bash
git add python/src/thermal_cli/sweep/dsl.py \
       python/src/thermal_cli/sweep/__init__.py \
       python/tests/unit/test_sweep_dsl.py
git commit -m "feat(m9): add YAML sweep DSL parser"
```

---

## Task 3: `optimize_fin.py` — extruded-fin geometry sweep

**Files:**
- Create: `python/src/thermal_cli/sweep/optimize_fin.py`
- Test: `python/tests/unit/test_optimize_fin.py`

**Depends on:** Tasks 1-2

- [ ] **Step 1: Write failing tests**

Create `python/tests/unit/test_optimize_fin.py`:

```python
"""Tests for thermal_cli.sweep.optimize_fin."""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.sweep.optimize_fin import (
    FinGeometrySweepConfig,
    evaluate_extruded_fin_rth,
    optimize_fin_geometry,
)


class TestEvaluateExtrudedFinRth:
    """``evaluate_extruded_fin_rth`` is the scalar adapter used by run_sweep."""

    def test_returns_positive_rth(self):
        rth = evaluate_extruded_fin_rth(
            thick_heatsink=0.010,
            thick_wall=0.0008,
            width_channel=0.00105,
            k_sink=180.0,
            rho_sink=2698.9,
            l_heated=0.137,
            a_hot=16.9e-3 * 13.7e-3,
            flowrate_lpm=1.0,
            fluid_ref="H2OGly50",
            t_fluid_in=343.15,
            num_channel=18,
        )
        assert rth > 0
        assert np.isfinite(rth)

    def test_thicker_heatsink_lower_rth(self):
        """Deeper channel = more area -> lower Rth (flow dominates)."""
        kw = dict(
            thick_wall=0.0008,
            width_channel=0.00105,
            k_sink=180.0,
            rho_sink=2698.9,
            l_heated=0.137,
            a_hot=16.9e-3 * 13.7e-3,
            flowrate_lpm=1.0,
            fluid_ref="H2OGly50",
            t_fluid_in=343.15,
            num_channel=18,
        )
        rth_thin = evaluate_extruded_fin_rth(thick_heatsink=0.006, **kw)
        rth_thick = evaluate_extruded_fin_rth(thick_heatsink=0.012, **kw)
        assert rth_thick < rth_thin


class TestOptimizeFinGeometry:
    def test_basic_grid_sweep(self):
        """3x3 grid, returns SweepResult with shape (3, 3)."""
        cfg = FinGeometrySweepConfig(
            axes={
                "thick_heatsink": [0.006, 0.008, 0.010],
                "thick_wall": [0.0006, 0.0008, 0.0010],
            },
            fixed={
                "width_channel": 0.00105,
                "k_sink": 180.0,
                "rho_sink": 2698.9,
                "l_heated": 0.137,
                "a_hot": 16.9e-3 * 13.7e-3,
                "flowrate_lpm": 1.0,
                "fluid_ref": "H2OGly50",
                "t_fluid_in": 343.15,
                "num_channel": 18,
            },
        )
        result = optimize_fin_geometry(cfg)
        assert result.values.shape == (3, 3)
        assert (result.values > 0).all()

    def test_returns_argmin_geometry(self):
        cfg = FinGeometrySweepConfig(
            axes={"thick_heatsink": [0.006, 0.008, 0.010]},
            fixed={
                "thick_wall": 0.0008,
                "width_channel": 0.00105,
                "k_sink": 180.0,
                "rho_sink": 2698.9,
                "l_heated": 0.137,
                "a_hot": 16.9e-3 * 13.7e-3,
                "flowrate_lpm": 1.0,
                "fluid_ref": "H2OGly50",
                "t_fluid_in": 343.15,
                "num_channel": 18,
            },
        )
        result = optimize_fin_geometry(cfg)
        best = result.argmin()
        assert "thick_heatsink" in best
        assert best["thick_heatsink"] in [0.006, 0.008, 0.010]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_optimize_fin.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `sweep/optimize_fin.py`**

Create `python/src/thermal_cli/sweep/optimize_fin.py`:

```python
"""Extruded-fin geometry grid sweep.

Wraps ``ExtrudedFin.thermal_resistance`` in a scalar adapter and feeds
it through ``run_sweep`` to find the geometry that minimises total
thermal resistance.

Ported from ``mfiles/Thermal/Optimizer/extrudedFinHeatsinkCalculations.m``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from thermal_cli.fluids import fluid_registry
from thermal_cli.heatsinks.extruded_fin import ExtrudedFin
from thermal_cli.sweep.engine import SweepResult, run_sweep


@dataclass
class FinGeometrySweepConfig:
    """Configuration for ``optimize_fin_geometry``.

    ``axes`` entries can be any parameter accepted by
    ``evaluate_extruded_fin_rth``; ``fixed`` supplies the rest.
    """

    axes: Mapping[str, Sequence[float]]
    fixed: Mapping[str, Any] = field(default_factory=dict)


def evaluate_extruded_fin_rth(
    *,
    thick_heatsink: float,
    thick_wall: float,
    width_channel: float,
    k_sink: float,
    rho_sink: float,
    l_heated: float,
    a_hot: float,
    flowrate_lpm: float,
    fluid_ref: str,
    t_fluid_in: float,
    num_channel: int,
    num_heated_sides: int = 1,
) -> float:
    """Build an ``ExtrudedFin`` and return total thermal resistance [K/W].

    Parameters mirror ``ExtrudedFin.__init__`` plus the runtime inputs
    ``thermal_resistance`` needs. Returns ``r_th_total`` as a scalar,
    which is what ``run_sweep`` expects.

    ``flowrate_lpm`` is litres per minute (matches the Octave CLI); the
    adapter converts to m^3/s internally.
    """
    hs = ExtrudedFin(
        num_channel=int(num_channel),
        thick_heatsink=thick_heatsink,
        thick_wall=thick_wall,
        width_channel=width_channel,
        k_sink=k_sink,
        rho_sink=rho_sink,
    )
    fluid = fluid_registry(fluid_ref)
    flowrate_m3s = flowrate_lpm / 1000.0 / 60.0
    result = hs.thermal_resistance(
        fluid=fluid,
        flowrate=flowrate_m3s,
        l_heated=l_heated,
        a_hot=a_hot,
        num_heated_sides=num_heated_sides,
    )
    return float(result["r_th_total"])


def optimize_fin_geometry(cfg: FinGeometrySweepConfig) -> SweepResult:
    """Run a grid sweep over fin geometry and return a SweepResult."""
    return run_sweep(
        func=evaluate_extruded_fin_rth,
        axes=cfg.axes,
        fixed=dict(cfg.fixed),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_optimize_fin.py -v`
Expected: all PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add python/src/thermal_cli/sweep/optimize_fin.py \
       python/tests/unit/test_optimize_fin.py
git commit -m "feat(m9): add optimize_fin — grid sweep over ExtrudedFin geometry"
```

---

## Task 4: `multi_sim.py` — baseplate scenario runner

**Files:**
- Create: `python/src/thermal_cli/sweep/multi_sim.py`
- Test: `python/tests/unit/test_multi_sim.py`

**Depends on:** Task 1

- [ ] **Step 1: Write failing tests**

Create `python/tests/unit/test_multi_sim.py`:

```python
"""Tests for thermal_cli.sweep.multi_sim."""

from __future__ import annotations

import pytest

from thermal_cli.sweep.multi_sim import (
    MultiSimResult,
    MultiSimScenario,
    run_multi_sim,
)


def _sample_scenario(name: str, k: float) -> MultiSimScenario:
    """Small 2-device baseplate, parameterised only by conductivity."""
    return MultiSimScenario(
        name=name,
        lx=0.12,
        ly=0.08,
        thickness=0.005,
        conductivity=k,
        r_sa=0.1,
        t_ambient=298.15,
        devices=[
            {"name": "Q1", "x": 0.03, "y": 0.04, "width": 0.02, "height": 0.02, "power": 100.0},
            {"name": "Q2", "x": 0.09, "y": 0.04, "width": 0.02, "height": 0.02, "power": 100.0},
        ],
        nx=21,
        ny=21,
    )


class TestRunMultiSim:
    def test_runs_all_scenarios(self):
        scenarios = [
            _sample_scenario("Al", 200.0),
            _sample_scenario("Cu", 385.0),
        ]
        result = run_multi_sim(scenarios)
        assert isinstance(result, MultiSimResult)
        assert len(result.rows) == 2
        assert [r.name for r in result.rows] == ["Al", "Cu"]

    def test_higher_conductivity_lower_t_max(self):
        al = _sample_scenario("Al", 200.0)
        cu = _sample_scenario("Cu", 385.0)
        result = run_multi_sim([al, cu])
        row_al = next(r for r in result.rows if r.name == "Al")
        row_cu = next(r for r in result.rows if r.name == "Cu")
        assert row_cu.t_j_max < row_al.t_j_max

    def test_per_device_peaks_present(self):
        result = run_multi_sim([_sample_scenario("Al", 200.0)])
        row = result.rows[0]
        assert set(row.t_j_per_device.keys()) == {"Q1", "Q2"}
        assert all(v > row.t_ambient for v in row.t_j_per_device.values())

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            run_multi_sim([])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_multi_sim.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `sweep/multi_sim.py`**

Create `python/src/thermal_cli/sweep/multi_sim.py`:

```python
"""Baseplate multi-scenario runner.

Iterates a list of ``MultiSimScenario`` specs, runs each through the
M6 FDM baseplate solver, and returns a ``MultiSimResult`` with per-
scenario peak temperatures and per-device junction temperatures.

Ported from ``mfiles/SoftwareTermico/Simulazione_multipla/``. The
Octave source repositioning loop is out of scope for M9.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from thermal_cli.baseplate.fdm_solver import solve_fdm
from thermal_cli.baseplate.types import BaseplateConfig, Device


@dataclass
class MultiSimScenario:
    """One scenario in a multi-sim run.

    ``devices`` is a list of plain dicts with Device fields — this keeps
    YAML deserialisation trivial.
    """

    name: str
    lx: float
    ly: float
    thickness: float
    conductivity: float
    r_sa: float
    t_ambient: float
    devices: list[dict[str, Any]]
    nx: int = 41
    ny: int = 41

    def to_config(self) -> BaseplateConfig:
        devs = [Device(**d) for d in self.devices]
        return BaseplateConfig(
            lx=self.lx,
            ly=self.ly,
            thickness=self.thickness,
            conductivity=self.conductivity,
            r_sa=self.r_sa,
            t_ambient=self.t_ambient,
            devices=devs,
            nx=self.nx,
            ny=self.ny,
        )


@dataclass
class MultiSimRow:
    """Summary of one scenario's baseplate solve."""

    name: str
    t_ambient: float
    t_max: float          # [K] peak baseplate temperature
    t_mean: float         # [K] mean baseplate temperature
    t_j_max: float        # [K] peak junction temperature
    t_j_per_device: dict[str, float] = field(default_factory=dict)


@dataclass
class MultiSimResult:
    rows: list[MultiSimRow]


def run_multi_sim(scenarios: list[MultiSimScenario]) -> MultiSimResult:
    """Run baseplate FDM solver on each scenario."""
    if not scenarios:
        raise ValueError("run_multi_sim needs at least one scenario")

    rows: list[MultiSimRow] = []
    for sc in scenarios:
        cfg = sc.to_config()
        res = solve_fdm(cfg)
        rows.append(
            MultiSimRow(
                name=sc.name,
                t_ambient=sc.t_ambient,
                t_max=res.t_max,
                t_mean=res.t_mean,
                t_j_max=res.t_j_max,
                t_j_per_device={d.name: d.t_junction for d in res.devices},
            )
        )
    return MultiSimResult(rows=rows)


def load_scenarios_from_dict(data: dict[str, Any]) -> list[MultiSimScenario]:
    """Parse a YAML-loaded dict with a top-level ``scenarios`` list."""
    if "scenarios" not in data:
        raise ValueError("multi-sim config requires a 'scenarios' key")
    return [MultiSimScenario(**entry) for entry in data["scenarios"]]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_multi_sim.py -v`
Expected: all PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add python/src/thermal_cli/sweep/multi_sim.py \
       python/tests/unit/test_multi_sim.py
git commit -m "feat(m9): add multi_sim — baseplate scenario grid runner"
```

---

## Task 5: CLI commands (`optimize-fin`, `multi-sim`)

**Files:**
- Create: `python/src/thermal_cli/cli/commands_m9.py`
- Modify: `python/src/thermal_cli/cli/main.py`
- Test: `python/tests/unit/test_cli_m9.py`

**Depends on:** Tasks 1-4

- [ ] **Step 1: Write failing CLI smoke tests**

Create `python/tests/unit/test_cli_m9.py`:

```python
"""Smoke tests for M9 CLI commands."""

from __future__ import annotations

import textwrap

from typer.testing import CliRunner

from thermal_cli.cli.main import app

runner = CliRunner()


def test_optimize_fin_smoke(tmp_path):
    cfg = tmp_path / "opt.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            axes:
              thick_heatsink: [0.006, 0.008, 0.010]
              thick_wall: [0.0006, 0.0008]
            fixed:
              width_channel: 0.00105
              k_sink: 180.0
              rho_sink: 2698.9
              l_heated: 0.137
              a_hot: 0.00023153
              flowrate_lpm: 1.0
              fluid_ref: H2OGly50
              t_fluid_in: 343.15
              num_channel: 18
            """
        )
    )
    result = runner.invoke(app, ["optimize-fin", "--config", str(cfg)])
    assert result.exit_code == 0, result.output
    assert "best" in result.output.lower()
    assert "r_th_total" in result.output


def test_multi_sim_smoke(tmp_path):
    cfg = tmp_path / "msim.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            scenarios:
              - name: Al
                lx: 0.12
                ly: 0.08
                thickness: 0.005
                conductivity: 200.0
                r_sa: 0.1
                t_ambient: 298.15
                nx: 21
                ny: 21
                devices:
                  - {name: Q1, x: 0.03, y: 0.04, width: 0.02, height: 0.02, power: 100.0}
                  - {name: Q2, x: 0.09, y: 0.04, width: 0.02, height: 0.02, power: 100.0}
              - name: Cu
                lx: 0.12
                ly: 0.08
                thickness: 0.005
                conductivity: 385.0
                r_sa: 0.1
                t_ambient: 298.15
                nx: 21
                ny: 21
                devices:
                  - {name: Q1, x: 0.03, y: 0.04, width: 0.02, height: 0.02, power: 100.0}
                  - {name: Q2, x: 0.09, y: 0.04, width: 0.02, height: 0.02, power: 100.0}
            """
        )
    )
    result = runner.invoke(app, ["multi-sim", "--config", str(cfg)])
    assert result.exit_code == 0, result.output
    assert "Al" in result.output
    assert "Cu" in result.output
    assert "t_j_max" in result.output


def test_optimize_fin_missing_config_exits_nonzero():
    result = runner.invoke(app, ["optimize-fin", "--config", "/tmp/does_not_exist_m9.yaml"])
    assert result.exit_code != 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_cli_m9.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `cli/commands_m9.py`**

Create `python/src/thermal_cli/cli/commands_m9.py`:

```python
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
            typer.echo("\t".join(axis_cells + [out_cell]))

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
```

- [ ] **Step 4: Wire into `cli/main.py`**

Edit `python/src/thermal_cli/cli/main.py` to import and register M9 alongside M7/M8. Add the import near the existing M7/M8 imports:

```python
from thermal_cli.cli.commands_m9 import register_all as register_m9
```

And after `register_m8(app)` add:

```python
register_m9(app)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_cli_m9.py -v`
Expected: all PASS (3 tests)

- [ ] **Step 6: Run full suite**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/ --tb=short`
Expected: all PASS (no regressions)

- [ ] **Step 7: Commit**

```bash
git add python/src/thermal_cli/cli/commands_m9.py \
       python/src/thermal_cli/cli/main.py \
       python/tests/unit/test_cli_m9.py
git commit -m "feat(m9): add CLI commands (optimize-fin, multi-sim)"
```

---

## Task 6: Literature + regression fixtures

**Files:**
- Create: `python/tests/literature/test_lit_sweep.py`
- Create: `python/tests/regression/fixtures/optimize_fin/basic.yaml`
- Create: `python/tests/regression/fixtures/multi_sim/two_scenarios.yaml`
- Modify: `python/tests/regression/helpers.py`

**Depends on:** Tasks 1-5

- [ ] **Step 1: Add literature-style test**

Create `python/tests/literature/test_lit_sweep.py`:

```python
"""Sanity tests for the sweep engine using an analytic minimum."""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.sweep.engine import run_sweep


class TestSweepOnQuadratic:
    def test_finds_minimum_of_parabola(self):
        """f(x) = (x - 2.5)^2 — argmin over a dense grid should be near 2.5."""
        result = run_sweep(
            func=lambda x: (x - 2.5) ** 2,
            axes={"x": np.linspace(0.0, 5.0, 101)},
        )
        assert result.argmin()["x"] == pytest.approx(2.5, abs=0.05)
        assert result.min() == pytest.approx(0.0, abs=1e-3)

    def test_finds_2d_minimum(self):
        """f(x, y) = (x - 1)^2 + (y - 3)^2 over a dense grid."""
        result = run_sweep(
            func=lambda x, y: (x - 1.0) ** 2 + (y - 3.0) ** 2,
            axes={
                "x": np.linspace(-1.0, 3.0, 41),
                "y": np.linspace(1.0, 5.0, 41),
            },
        )
        best = result.argmin()
        assert best["x"] == pytest.approx(1.0, abs=0.05)
        assert best["y"] == pytest.approx(3.0, abs=0.05)
```

- [ ] **Step 2: Add regression helper for the optimize-fin fixture**

Append to `python/tests/regression/helpers.py`:

```python
# ---------------------------------------------------------------------------
# M9 sweep wrappers
# ---------------------------------------------------------------------------


def run_optimize_fin_basic() -> dict:
    """Regression fixture wrapper: 3x3 grid over fin thickness/wall thickness.

    Matches the toy grid used in ``optimize_fin/basic.yaml``. Returns
    scalar best Rth + argmin coordinates so it can be round-tripped via
    the JSON regression harness.
    """
    from thermal_cli.sweep.optimize_fin import (
        FinGeometrySweepConfig,
        optimize_fin_geometry,
    )

    cfg = FinGeometrySweepConfig(
        axes={
            "thick_heatsink": [0.006, 0.008, 0.010],
            "thick_wall": [0.0006, 0.0008, 0.0010],
        },
        fixed={
            "width_channel": 0.00105,
            "k_sink": 180.0,
            "rho_sink": 2698.9,
            "l_heated": 0.137,
            "a_hot": 16.9e-3 * 13.7e-3,
            "flowrate_lpm": 1.0,
            "fluid_ref": "H2OGly50",
            "t_fluid_in": 343.15,
            "num_channel": 18,
        },
    )
    result = optimize_fin_geometry(cfg)
    best = result.argmin()
    return {
        "best_r_th": result.min(),
        "best_thick_heatsink": best["thick_heatsink"],
        "best_thick_wall": best["thick_wall"],
    }


def run_multi_sim_two_scenarios() -> dict:
    """Regression wrapper: 2-scenario baseplate run (Al vs Cu)."""
    from thermal_cli.sweep.multi_sim import MultiSimScenario, run_multi_sim

    def _sc(name: str, k: float) -> MultiSimScenario:
        return MultiSimScenario(
            name=name,
            lx=0.12,
            ly=0.08,
            thickness=0.005,
            conductivity=k,
            r_sa=0.1,
            t_ambient=298.15,
            devices=[
                {"name": "Q1", "x": 0.03, "y": 0.04, "width": 0.02, "height": 0.02, "power": 100.0},
                {"name": "Q2", "x": 0.09, "y": 0.04, "width": 0.02, "height": 0.02, "power": 100.0},
            ],
            nx=21,
            ny=21,
        )

    result = run_multi_sim([_sc("Al", 200.0), _sc("Cu", 385.0)])
    row_al = next(r for r in result.rows if r.name == "Al")
    row_cu = next(r for r in result.rows if r.name == "Cu")
    return {
        "al_t_j_max": row_al.t_j_max,
        "cu_t_j_max": row_cu.t_j_max,
    }
```

- [ ] **Step 3: Create regression fixture YAML files**

Create `python/tests/regression/fixtures/optimize_fin/basic.yaml`:

```yaml
command: optimize-fin
description: 3x3 grid over extruded-fin thickness/wall thickness (H2OGly50 coolant)
python_call:
  module: tests.regression.helpers
  function: run_optimize_fin_basic
  args: {}
tolerance:
  rtol: 1.0e-6
```

Create `python/tests/regression/fixtures/multi_sim/two_scenarios.yaml`:

```yaml
command: multi-sim
description: 2 baseplate scenarios (Al vs Cu) with 2 devices each.
python_call:
  module: tests.regression.helpers
  function: run_multi_sim_two_scenarios
  args: {}
tolerance:
  rtol: 1.0e-6
```

- [ ] **Step 4: Run literature + regression tests**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/literature/test_lit_sweep.py tests/regression/ -v`
Expected: all PASS (literature tests + new regression fixtures)

- [ ] **Step 5: Commit**

```bash
git add python/tests/literature/test_lit_sweep.py \
       python/tests/regression/fixtures/optimize_fin/ \
       python/tests/regression/fixtures/multi_sim/ \
       python/tests/regression/helpers.py
git commit -m "test(m9): add literature + regression fixtures for sweep engine"
```

---

## Task 7: Final integration — lint, format, full suite

**Depends on:** Tasks 1-6

- [ ] **Step 1: Run ruff lint**

Run: `cd python && conda run -n ntbees2 ruff check src tests`
Fix any errors before proceeding.

- [ ] **Step 2: Run ruff format**

Run: `cd python && conda run -n ntbees2 ruff format src tests`

- [ ] **Step 3: Run full test suite**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/ -v --tb=short`
Expected: all PASS (approx 320 existing + ~27 new M9 tests).

- [ ] **Step 4: Commit**

```bash
git add -u
git commit -m "feat(m9): complete M9 — sweep engine + optimize-fin + multi-sim"
```

---

## Out of scope (filed for later)

- **Source repositioning loop** from `Simulazione_Multipla.m` — when a scenario violates `T > Tmax`, the Octave code moves sources and re-solves. M9 ships static evaluation only; the repositioning feedback loop is a follow-up.
- **SciPy gradient-based optimizers** — `optimize-fin` only does grid sweeps in M9.
- **Progress bars and parallelism** — grids in scope (≤ 10³ combinations) run in seconds serially.
- **`--output <path.json>`** dump of full SweepResult — consider for M12 when the Jupyter frontend needs it.
