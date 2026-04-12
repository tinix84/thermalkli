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
    if fx.python_only:
        # python_only fixture: verify callable runs and returns a value
        py_out = call_python(fx.python_module, fx.python_function, fx.python_args)
        assert py_out is not None, f"python_only fixture returned None: {fixture_path}"
        return
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
