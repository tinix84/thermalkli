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
        "lib",
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
    # Take the last line starting with { — Octave may emit warnings before it.
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
                        f"mismatch at '{key}[{i}]': octave={a} python={b} rtol={rtol} atol={atol}"
                    )
            continue
        if not math.isclose(float(ov), float(pv), rel_tol=rtol, abs_tol=atol):
            rel_err = abs(float(ov) - float(pv)) / max(abs(float(ov)), 1e-30)
            raise AssertionError(
                f"mismatch at '{key}': octave={ov} python={pv} "
                f"rel_err={rel_err:.2e} rtol={rtol} atol={atol}"
            )
