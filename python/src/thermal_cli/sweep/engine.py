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
        call_kw = {
            name: float(vals[i])
            for name, vals, i in zip(axis_names, axis_values, idx_tuple, strict=True)
        }
        out[idx_tuple] = float(func(**call_kw, **fixed_kw))

    return SweepResult(
        axis_names=axis_names,
        axis_values=axis_values,
        values=out,
        fixed=fixed_kw,
    )
