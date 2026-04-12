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
        Axis name -> values, insertion order preserved.
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
