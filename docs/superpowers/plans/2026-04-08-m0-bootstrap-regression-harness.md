# M0 — Bootstrap + Regression Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the `python/` package skeleton (`thermal-cli`), port the smallest Octave function (`finEfficieny`) as a proof-of-life port, build the Octave↔Python regression harness that will govern all subsequent milestones, and prove the entire loop in CI.

**Architecture:** Standard Python src-layout under `python/`. Typer-based CLI stub with a single placeholder command. `pytest` with three directories: `unit/`, `literature/`, `regression/`. The regression harness invokes `octave --eval` via `subprocess`, captures JSON output from `jsonencode()`, and numerically diffs against the Python function's output. GitHub Actions CI installs `octave-cli` and runs all three test layers.

**Tech Stack:** Python 3.11+, Typer, Pydantic v2, NumPy, pytest, PyYAML, ruff, mypy, Octave 6+ (CI only), GitHub Actions.

**Parent spec:** `docs/superpowers/specs/2026-04-08-octave-to-python-migration-design.md` (M0 milestone)

---

## File Structure

**Files created in this milestone:**

```
python/
├── pyproject.toml                              # package metadata + deps + tool configs
├── README.md                                   # short blurb pointing to top-level docs
├── .gitignore                                  # __pycache__/, .venv/, *.egg-info/, .pytest_cache/
├── src/
│   └── thermal_cli/
│       ├── __init__.py                         # exports __version__
│       ├── formula/
│       │   ├── __init__.py                     # re-exports fin_efficiency
│       │   └── fin.py                          # fin_efficiency function
│       └── cli/
│           ├── __init__.py                     # empty
│           └── main.py                         # Typer app, --version, entry point
└── tests/
    ├── __init__.py                             # empty
    ├── unit/
    │   ├── __init__.py
    │   └── test_fin.py                         # pure pytest unit tests
    ├── literature/
    │   └── __init__.py                         # empty in M0 (populated M1+)
    └── regression/
        ├── __init__.py
        ├── conftest.py                         # octave runner, assert_close, fixture loader
        ├── test_regression.py                  # parametrized runner over fixtures/
        └── fixtures/
            └── fin_efficiency/
                └── basic.yaml                  # first proof-of-life fixture

.github/
└── workflows/
    └── python-ci.yml                           # lint + unit + literature + regression jobs
```

**Responsibilities:**

- `pyproject.toml` — package config; keeps dev and runtime deps minimal in M0; strict ruff/mypy configs apply to `src/thermal_cli/` only
- `thermal_cli/formula/fin.py` — the first ported function; a pure numerical function, no I/O
- `thermal_cli/cli/main.py` — Typer app stub so the `thermal` entry point is installable and testable from M0 onward
- `tests/unit/test_fin.py` — unit-level behavior tests (edge cases, known values) for `fin_efficiency`
- `tests/regression/conftest.py` — all shared regression plumbing: Octave subprocess runner, JSON parser, `assert_close` comparator, `load_fixture` YAML loader, `discover_fixtures` globber
- `tests/regression/test_regression.py` — a single parametrized test that iterates every fixture under `fixtures/`
- `tests/regression/fixtures/fin_efficiency/basic.yaml` — the proof-of-life fixture; validates the entire loop end-to-end
- `.github/workflows/python-ci.yml` — CI job matrix: lint, unit, regression (with `octave-cli` apt install)

---

## Task 1: Create `python/` package skeleton and `pyproject.toml`

**Files:**
- Create: `python/pyproject.toml`
- Create: `python/README.md`
- Create: `python/.gitignore`
- Create: `python/src/thermal_cli/__init__.py`
- Create: `python/src/thermal_cli/formula/__init__.py`
- Create: `python/src/thermal_cli/cli/__init__.py`
- Create: `python/tests/__init__.py`
- Create: `python/tests/unit/__init__.py`
- Create: `python/tests/literature/__init__.py`
- Create: `python/tests/regression/__init__.py`

- [ ] **Step 1: Create `python/pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "thermal-cli"
version = "0.0.1"
description = "Thermal engineering library for power electronics (Python port of octave/thermal)"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "tinix84" }]
dependencies = [
    "typer>=0.12",
    "pydantic>=2.6",
    "pyyaml>=6.0",
    "numpy>=1.26",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "ruff>=0.5",
    "mypy>=1.10",
    "types-PyYAML",
]

[project.scripts]
thermal = "thermal_cli.cli.main:app"

[tool.hatch.build.targets.wheel]
packages = ["src/thermal_cli"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]
ignore = []

[tool.mypy]
python_version = "3.11"
strict = true
files = ["src/thermal_cli"]
```

- [ ] **Step 2: Create `python/README.md`**

```markdown
# thermal-cli

Python port of the Octave thermal engineering library. See
[`docs/superpowers/specs/2026-04-08-octave-to-python-migration-design.md`](../docs/superpowers/specs/2026-04-08-octave-to-python-migration-design.md)
for the migration plan.

## Install (dev)

```bash
cd python
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run tests

```bash
pytest                    # all tests (requires octave installed for regression)
pytest tests/unit         # unit only (no octave needed)
pytest tests/regression   # regression only (needs octave)
```
```

- [ ] **Step 3: Create `python/.gitignore`**

```gitignore
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
build/
dist/
*.egg
```

- [ ] **Step 4: Create all empty `__init__.py` files**

Create `python/src/thermal_cli/__init__.py`:

```python
"""thermal-cli — Python port of the Octave thermal engineering library."""

__version__ = "0.0.1"
```

Create `python/src/thermal_cli/formula/__init__.py`:

```python
"""Pure analytical formulas (fin efficiency, radiation, Nusselt helpers)."""
```

Create `python/src/thermal_cli/cli/__init__.py`:

```python
"""Typer-based CLI for the thermal-cli package."""
```

Create `python/tests/__init__.py`, `python/tests/unit/__init__.py`, `python/tests/literature/__init__.py`, `python/tests/regression/__init__.py` — all as empty files.

- [ ] **Step 5: Verify install works locally**

Run:
```bash
cd python && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```

Expected: install succeeds, no errors. `thermal --help` fails (not yet defined) — that's expected, we fix it in Task 2.

- [ ] **Step 6: Commit**

```bash
git add python/
git commit -m "feat(python): add package skeleton and pyproject.toml"
```

---

## Task 2: Minimal Typer CLI entry point

**Files:**
- Create: `python/src/thermal_cli/cli/main.py`
- Create: `python/tests/unit/test_cli_main.py`

- [ ] **Step 1: Write the failing test**

Create `python/tests/unit/test_cli_main.py`:

```python
"""Smoke tests for the Typer CLI entry point."""

from typer.testing import CliRunner

from thermal_cli import __version__
from thermal_cli.cli.main import app

runner = CliRunner()


def test_version_flag_prints_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_lists_thermal_cli():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "thermal-cli" in result.stdout.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd python && pytest tests/unit/test_cli_main.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'thermal_cli.cli.main'`.

- [ ] **Step 3: Write minimal implementation**

Create `python/src/thermal_cli/cli/main.py`:

```python
"""Typer entry point for the thermal-cli package."""

from __future__ import annotations

import typer

from thermal_cli import __version__

app = typer.Typer(
    name="thermal",
    help="thermal-cli — Python port of the Octave thermal engineering library.",
    add_completion=False,
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"thermal-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """thermal-cli root command."""


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd python && pytest tests/unit/test_cli_main.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add python/src/thermal_cli/cli/main.py python/tests/unit/test_cli_main.py
git commit -m "feat(cli): add Typer entry point with --version"
```

---

## Task 3: Port `finEfficieny` to `fin_efficiency` (TDD)

**Files:**
- Create: `python/src/thermal_cli/formula/fin.py`
- Create: `python/tests/unit/test_fin.py`

**Octave reference:** `mfiles/Thermal/Formula/finEfficieny.m` (note: Octave has a typo in the function name; Python uses the correct spelling).

Octave implementation:
```matlab
function [etaFin] = finEfficieny(L, h, A, k, Ac)
    mL = (h*A/(k*Ac*L))^0.5*L;
    etaFin = tanh(mL)/mL;
end
```

- [ ] **Step 1: Write the failing unit test**

Create `python/tests/unit/test_fin.py`:

```python
"""Unit tests for thermal_cli.formula.fin."""

import math

import pytest

from thermal_cli.formula.fin import fin_efficiency


def test_known_value_small_mL():
    """For small mL, efficiency approaches 1 (tanh(x)/x → 1 as x → 0)."""
    # L=0.001, very short fin → mL small → eta close to 1
    eta = fin_efficiency(L=0.001, h=10.0, A=1e-5, k=200.0, Ac=1e-6)
    assert 0.99 < eta <= 1.0


def test_known_value_large_mL():
    """For large mL, efficiency approaches 0 (tanh(x)/x → 0 as x → ∞)."""
    # Very long, thin, low-k fin → mL large → eta small
    eta = fin_efficiency(L=1.0, h=1000.0, A=1.0, k=1.0, Ac=1e-6)
    assert 0.0 < eta < 0.1


def test_matches_analytical_formula():
    """Explicit computation: L=0.05, h=30, A=0.01, k=200, Ac=1e-4.
    mL = sqrt(30*0.01 / (200*1e-4*0.05)) * 0.05 = sqrt(30) * 0.05
    """
    L, h, A, k, Ac = 0.05, 30.0, 0.01, 200.0, 1e-4
    mL = math.sqrt(h * A / (k * Ac * L)) * L
    expected = math.tanh(mL) / mL
    eta = fin_efficiency(L=L, h=h, A=A, k=k, Ac=Ac)
    assert eta == pytest.approx(expected, rel=1e-12)


def test_returns_float():
    eta = fin_efficiency(L=0.05, h=30.0, A=0.01, k=200.0, Ac=1e-4)
    assert isinstance(eta, float)
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd python && pytest tests/unit/test_fin.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'thermal_cli.formula.fin'`.

- [ ] **Step 3: Write minimal implementation**

Create `python/src/thermal_cli/formula/fin.py`:

```python
"""Fin efficiency for constant-cross-section fins.

Ported from ``mfiles/Thermal/Formula/finEfficieny.m``. Note the Octave source
has a typo in the function name (``finEfficieny`` → ``fin_efficiency``).
"""

from __future__ import annotations

import math


def fin_efficiency(*, L: float, h: float, A: float, k: float, Ac: float) -> float:
    """Compute the efficiency of a constant-cross-section fin.

    Uses the classical ``tanh(mL)/mL`` formula where
    ``mL = sqrt(h * A / (k * Ac * L)) * L``.

    Parameters
    ----------
    L : float
        Fin length [m].
    h : float
        Heat transfer coefficient fin surface → fluid [W/(m²·K)].
    A : float
        Fin surface area [m²].
    k : float
        Thermal conductivity of the fin material [W/(m·K)].
    Ac : float
        Fin cross-sectional area [m²].

    Returns
    -------
    float
        Fin efficiency (dimensionless, in (0, 1]).
    """
    mL = math.sqrt(h * A / (k * Ac * L)) * L
    return math.tanh(mL) / mL
```

- [ ] **Step 4: Re-export from the formula package**

Edit `python/src/thermal_cli/formula/__init__.py`:

```python
"""Pure analytical formulas (fin efficiency, radiation, Nusselt helpers)."""

from thermal_cli.formula.fin import fin_efficiency

__all__ = ["fin_efficiency"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
cd python && pytest tests/unit/test_fin.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add python/src/thermal_cli/formula/fin.py \
        python/src/thermal_cli/formula/__init__.py \
        python/tests/unit/test_fin.py
git commit -m "feat(formula): port fin_efficiency from Octave finEfficieny.m"
```

---

## Task 4: Regression harness infrastructure (`conftest.py`)

**Files:**
- Create: `python/tests/regression/conftest.py`

The harness has four responsibilities:
1. Invoke `octave --eval` in a subprocess and capture JSON-encoded stdout.
2. Load fixture YAML files into a structured dataclass.
3. Dynamically import and call the Python-side function described in a fixture.
4. Assert two (possibly nested) numeric structures are close within tolerance.

- [ ] **Step 1: Create `conftest.py` with all helpers**

Create `python/tests/regression/conftest.py`:

```python
"""Shared plumbing for the Octave↔Python regression harness.

Each fixture is a YAML file describing:
  - an Octave snippet that prints JSON via ``disp(jsonencode(...))``
  - a Python callable (module path + function name + kwargs)
  - a tolerance (rtol, atol) for numerical comparison.

The test runner discovers fixtures, executes both sides, and asserts
that the structures are numerically close.
"""

from __future__ import annotations

import importlib
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Path to the repo root (python/tests/regression/conftest.py → up 3)
REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = Path(__file__).parent / "fixtures"

OCTAVE_PATHS = ":".join(
    str(REPO_ROOT / p)
    for p in (
        "mfiles/Thermal/Formula",
        "mfiles/Thermal/Model",
        "mfiles/Thermal/Designer",
    )
)


@dataclass(frozen=True)
class Fixture:
    """A single regression fixture loaded from YAML."""

    path: Path
    command: str
    description: str
    octave_script: str
    python_module: str
    python_function: str
    python_args: dict[str, Any]
    rtol: float
    atol: float


def load_fixture(path: Path) -> Fixture:
    """Parse a fixture YAML into a Fixture dataclass."""
    data = yaml.safe_load(path.read_text())
    tol = data.get("tolerance", {})
    return Fixture(
        path=path,
        command=data["command"],
        description=data.get("description", ""),
        octave_script=data["octave_script"],
        python_module=data["python_call"]["module"],
        python_function=data["python_call"]["function"],
        python_args=data["python_call"].get("args", {}),
        rtol=float(tol.get("rtol", 1e-6)),
        atol=float(tol.get("atol", 1e-12)),
    )


def discover_fixtures() -> list[Path]:
    """Return every *.yaml file under tests/regression/fixtures/."""
    if not FIXTURES_DIR.exists():
        return []
    return sorted(FIXTURES_DIR.rglob("*.yaml"))


def run_octave(script: str, timeout: float = 60.0) -> dict[str, Any]:
    """Execute an Octave snippet and parse its JSON-encoded stdout.

    The snippet must end with ``disp(jsonencode(struct(...)))`` so this
    function can parse a single JSON object from stdout.
    """
    cmd = [
        "octave",
        "--no-gui",
        "--quiet",
        "--no-history",
        "--path",
        OCTAVE_PATHS,
        "--eval",
        script,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"octave failed (exit {result.returncode}):\n"
            f"--- stderr ---\n{result.stderr}\n"
            f"--- stdout ---\n{result.stdout}"
        )
    stdout = result.stdout.strip()
    if not stdout:
        raise RuntimeError(f"octave produced no stdout; stderr:\n{result.stderr}")
    # Take the last non-empty line — Octave may emit warnings before it.
    json_line = next(
        (ln for ln in reversed(stdout.splitlines()) if ln.strip().startswith("{")),
        None,
    )
    if json_line is None:
        raise RuntimeError(f"no JSON object found in octave stdout:\n{stdout}")
    return json.loads(json_line)


def call_python(module_path: str, function_name: str, args: dict[str, Any]) -> Any:
    """Import ``module_path`` and call ``function_name(**args)``."""
    module = importlib.import_module(module_path)
    func = getattr(module, function_name)
    return func(**args)


def _to_dict(result: Any) -> dict[str, Any]:
    """Normalize a Python function's return value to a dict for comparison.

    Scalars are wrapped as {"value": x} to match a corresponding
    ``struct('value', x)`` on the Octave side.
    """
    if isinstance(result, dict):
        return result
    if isinstance(result, (int, float)):
        return {"value": float(result)}
    if hasattr(result, "_asdict"):
        return dict(result._asdict())
    raise TypeError(f"cannot normalize {type(result).__name__} to dict")


def assert_close(
    oct_out: dict[str, Any],
    py_out: dict[str, Any],
    *,
    rtol: float,
    atol: float,
) -> None:
    """Recursively assert that two nested numeric structures are close."""
    if set(oct_out) != set(py_out):
        raise AssertionError(
            f"key mismatch:\n  octave: {sorted(oct_out)}\n  python: {sorted(py_out)}"
        )
    for key in oct_out:
        ov, pv = oct_out[key], py_out[key]
        if isinstance(ov, dict) and isinstance(pv, dict):
            assert_close(ov, pv, rtol=rtol, atol=atol)
            continue
        if isinstance(ov, list) and isinstance(pv, list):
            if len(ov) != len(pv):
                raise AssertionError(
                    f"length mismatch at '{key}': octave={len(ov)} python={len(pv)}"
                )
            for i, (a, b) in enumerate(zip(ov, pv, strict=True)):
                if not math.isclose(float(a), float(b), rel_tol=rtol, abs_tol=atol):
                    raise AssertionError(
                        f"mismatch at '{key}[{i}]': "
                        f"octave={a} python={b} rtol={rtol} atol={atol}"
                    )
            continue
        if not math.isclose(float(ov), float(pv), rel_tol=rtol, abs_tol=atol):
            rel_err = abs(float(ov) - float(pv)) / max(abs(float(ov)), 1e-30)
            raise AssertionError(
                f"mismatch at '{key}': octave={ov} python={pv} "
                f"rel_err={rel_err:.2e} rtol={rtol} atol={atol}"
            )
```

- [ ] **Step 2: Quick sanity check — run pytest to make sure nothing breaks**

Run:
```bash
cd python && pytest tests/ -v
```

Expected: unit tests still pass, regression directory has no tests yet (no test files), 6 total passed.

- [ ] **Step 3: Commit**

```bash
git add python/tests/regression/conftest.py
git commit -m "feat(regression): add octave runner and fixture loader infrastructure"
```

---

## Task 5: Regression test runner (parametrized over fixtures)

**Files:**
- Create: `python/tests/regression/test_regression.py`

- [ ] **Step 1: Create the parametrized runner**

Create `python/tests/regression/test_regression.py`:

```python
"""Parametrized Octave↔Python regression test.

Discovers every fixture under ``tests/regression/fixtures/`` and asserts
numerical parity between the Octave side and the Python side.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.regression.conftest import (
    assert_close,
    call_python,
    discover_fixtures,
    load_fixture,
    run_octave,
)


def _fixture_id(path: Path) -> str:
    """Human-readable test ID from fixture path, e.g. 'fin_efficiency/basic'."""
    return path.relative_to(path.parents[1]).with_suffix("").as_posix()


@pytest.mark.parametrize(
    "fixture_path",
    discover_fixtures(),
    ids=lambda p: _fixture_id(p),
)
def test_octave_python_parity(fixture_path: Path) -> None:
    fx = load_fixture(fixture_path)
    oct_out = run_octave(fx.octave_script)
    py_out = call_python(fx.python_module, fx.python_function, fx.python_args)
    # Normalize scalar Python results to a dict keyed by the single Octave field.
    if not isinstance(py_out, dict):
        # Octave side must emit struct with exactly one field.
        if len(oct_out) != 1:
            raise AssertionError(
                f"fixture {fixture_path} returns a scalar but octave struct has "
                f"{len(oct_out)} fields: {list(oct_out)}"
            )
        (key,) = oct_out.keys()
        py_out = {key: float(py_out)}
    assert_close(oct_out, py_out, rtol=fx.rtol, atol=fx.atol)
```

- [ ] **Step 2: Quick sanity check — no fixtures yet so the test is skipped/empty**

Run:
```bash
cd python && pytest tests/regression -v
```

Expected: `collected 0 items` (no fixtures yet). No errors.

- [ ] **Step 3: Commit**

```bash
git add python/tests/regression/test_regression.py
git commit -m "feat(regression): add parametrized octave-vs-python test runner"
```

---

## Task 6: First proof-of-life fixture (`fin_efficiency/basic.yaml`)

**Files:**
- Create: `python/tests/regression/fixtures/fin_efficiency/basic.yaml`

- [ ] **Step 1: Create the fixture**

Create `python/tests/regression/fixtures/fin_efficiency/basic.yaml`:

```yaml
command: fin-efficiency
description: |
  Proof-of-life regression for fin_efficiency / finEfficieny.
  Uses L=0.05, h=30, A=0.01, k=200, Ac=1e-4 — ordinary aluminum fin
  in forced air convection.
octave_script: |
  addpath('mfiles/Thermal/Formula');
  L = 0.05;
  h = 30.0;
  A = 0.01;
  k = 200.0;
  Ac = 1e-4;
  eta = finEfficieny(L, h, A, k, Ac);
  disp(jsonencode(struct('eta', eta)));
python_call:
  module: thermal_cli.formula.fin
  function: fin_efficiency
  args:
    L: 0.05
    h: 30.0
    A: 0.01
    k: 200.0
    Ac: 1.0e-4
tolerance:
  rtol: 1.0e-6
  atol: 1.0e-12
```

**Note on the key name**: Octave emits `struct('eta', eta)` → JSON `{"eta": <value>}`. The Python function returns a float, which the runner normalizes to `{"eta": <value>}` by taking the single Octave key. This is the documented scalar-result convention.

- [ ] **Step 2: Run the regression test locally (requires octave installed)**

Check whether octave is available:

```bash
which octave && octave --version | head -1
```

If octave is available, run:
```bash
cd python && pytest tests/regression -v
```

Expected: 1 passed — `test_octave_python_parity[fin_efficiency/basic]`.

If octave is **not** installed locally, skip to CI (Task 7) and validate there. Note this explicitly in the commit message.

- [ ] **Step 3: Commit**

```bash
git add python/tests/regression/fixtures/fin_efficiency/basic.yaml
git commit -m "test(regression): add fin_efficiency/basic proof-of-life fixture"
```

---

## Task 7: GitHub Actions CI workflow

**Files:**
- Create: `.github/workflows/python-ci.yml`

- [ ] **Step 1: Create the CI workflow**

Create `.github/workflows/python-ci.yml`:

```yaml
name: python-ci

on:
  push:
    branches: [main]
    paths:
      - "python/**"
      - ".github/workflows/python-ci.yml"
      - "mfiles/**"
  pull_request:
    paths:
      - "python/**"
      - ".github/workflows/python-ci.yml"
      - "mfiles/**"

jobs:
  lint:
    name: Lint (ruff)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install package (dev)
        working-directory: python
        run: pip install -e ".[dev]"
      - name: ruff check
        working-directory: python
        run: ruff check .
      - name: ruff format check
        working-directory: python
        run: ruff format --check .

  unit:
    name: Unit tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install package (dev)
        working-directory: python
        run: pip install -e ".[dev]"
      - name: pytest (unit)
        working-directory: python
        run: pytest tests/unit -v

  regression:
    name: Octave↔Python regression
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install octave
        run: |
          sudo apt-get update
          sudo apt-get install -y octave
          octave --version | head -1
      - name: Install package (dev)
        working-directory: python
        run: pip install -e ".[dev]"
      - name: pytest (regression)
        working-directory: python
        run: pytest tests/regression -v
```

- [ ] **Step 2: Verify the YAML is valid**

Run:
```bash
python -c "import yaml, sys; yaml.safe_load(open('.github/workflows/python-ci.yml')); print('ok')"
```

Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/python-ci.yml
git commit -m "ci: add python-ci workflow (lint + unit + octave regression)"
```

---

## Task 8: Push and verify CI is green

**Files:** none (verification only)

- [ ] **Step 1: Push the branch (or open a PR if working on a feature branch)**

If on `main` (not recommended but allowed per CLAUDE.md only for non-feature work), confirm with the user first. Otherwise, assume a feature branch like `feat/m0-bootstrap` was created before Task 1.

Check current branch:
```bash
git status -sb | head -1
```

If on a feature branch:
```bash
git push -u origin HEAD
```

- [ ] **Step 2: Watch CI**

Run:
```bash
gh run watch
```

Expected: `lint`, `unit`, `regression` all green.

- [ ] **Step 3: If regression fails in CI, triage**

Most likely failure modes:
1. **`octave: command not found`** — apt install step failed; check runner OS.
2. **`jsonencode: undefined`** — Octave version on CI is <5. Bump to `ubuntu-24.04` or use `sudo apt-get install -y octave liboctave-dev`.
3. **Path mismatch** — `OCTAVE_PATHS` in `conftest.py` uses `REPO_ROOT / 'mfiles/...'`; check CI working directory is the repo root, not `python/`.
4. **Numerical mismatch** — unlikely at `rtol=1e-6` for a tanh-based formula, but if it happens, print both values and investigate.

Fix inline and re-push until green.

- [ ] **Step 4: Open a PR if not already open**

```bash
gh pr create \
  --title "feat(m0): bootstrap python/ package + regression harness" \
  --body "$(cat <<'EOF'
## Summary
- Adds `python/` package skeleton (`thermal-cli`) with Typer CLI, src-layout
- Ports `finEfficieny` → `fin_efficiency` as the proof-of-life function
- Introduces the Octave↔Python regression harness (conftest, runner, fixture loader)
- Ships the first fixture (`fin_efficiency/basic.yaml`) proving end-to-end parity
- Adds `python-ci` GitHub Actions workflow (lint + unit + regression with `octave-cli`)

Implements **M0** of the Octave→Python migration plan
(`docs/superpowers/specs/2026-04-08-octave-to-python-migration-design.md`).

## Test plan
- [x] `pytest tests/unit` green locally
- [x] `pytest tests/regression` green locally (requires octave)
- [ ] `python-ci` workflow green on CI
EOF
)"
```

- [ ] **Step 5: Final verification**

All three CI jobs green, PR description lists the tasks completed. M0 done.

---

## Self-Review

**Spec coverage (against M0 row in the spec milestone table):**
- ✅ "python/ skeleton" → Task 1
- ✅ "pyproject.toml" → Task 1
- ✅ "CI (pytest + lint + octave install)" → Task 7
- ✅ "regression harness infra" → Tasks 4, 5
- ✅ "1 proof fixture (fin_efficiency)" → Task 6
- ✅ Gate: "Harness runs in CI, proof fixture green" → Task 8

**Placeholder scan:** no TBDs, no "implement later", no "add validation", no bare references to undefined functions. Every code block is complete and runnable.

**Type consistency check:**
- `Fixture` dataclass (Task 4) has fields `python_module`, `python_function`, `python_args` — consumed in Task 5 as `fx.python_module`, `fx.python_function`, `fx.python_args`. ✅
- `fin_efficiency(L, h, A, k, Ac)` signature (Task 3) matches the fixture `python_call.args` keys in Task 6. ✅
- `run_octave()` return type `dict[str, Any]` matches `assert_close()` input type. ✅
- `call_python()` may return `float` (non-dict); Task 5 runner handles that case by wrapping into `{key: value}` using the single Octave key — documented in the fixture (Task 6). ✅
- CI workflow paths (`.github/workflows/python-ci.yml`) run from repo root; `conftest.py`'s `REPO_ROOT = Path(__file__).resolve().parents[3]` resolves to the repo root given the file lives at `python/tests/regression/conftest.py`. ✅

No issues found.
