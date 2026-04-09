"""One-shot converter for Octave .m struct config files to YAML.

Parses flat ``cfg.field = value;`` assignments from an Octave function
that returns a struct and emits an equivalent YAML dict.

Usage::

    thermal convert-config old_config.m new_config.yaml
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


def parse_m_config(text: str) -> dict[str, Any]:
    """Parse an Octave config function body into a nested dict.

    Handles:
    - ``cfg.x = 1.5;`` (scalar float/int)
    - ``cfg.x = 1e-3;`` (scientific notation)
    - ``cfg.x.y = 'foo';`` (nested struct, string)
    - ``cfg.x = [1 2 3];`` or ``cfg.x = [1, 2, 3];`` (numeric array)
    - ``% comment`` lines and inline ``% comment`` after values

    Does NOT handle:
    - Expressions (``cfg.x = 2*pi;``)
    - Conditional logic, loops, or function calls
    - Multi-line assignments
    """
    result: dict[str, Any] = {}

    # Match lines like:  cfg.a.b.c = <value>;
    pattern = re.compile(r"^\s*cfg\.(?P<path>[\w.]+)\s*=\s*(?P<value>.+?)\s*;\s*(?:%.*)?$")

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("%") or stripped.startswith("function"):
            continue
        if stripped == "end":
            continue

        m = pattern.match(stripped)
        if not m:
            continue

        path_str = m.group("path")
        raw_value = m.group("value").strip()
        value = _parse_value(raw_value)
        _set_nested(result, path_str.split("."), value)

    return result


def _parse_value(raw: str) -> Any:
    """Convert an Octave literal string to a Python value."""
    # String: 'foo'
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]

    # Array: [1 2 3] or [1, 2, 3]
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        # Split on whitespace or commas
        parts = re.split(r"[,\s]+", inner)
        return [_parse_scalar(p) for p in parts if p]

    return _parse_scalar(raw)


def _parse_scalar(raw: str) -> int | float | str:
    """Parse a single scalar token."""
    # Remove trailing % comment
    raw = re.sub(r"\s*%.*$", "", raw).strip()
    try:
        if "." in raw or "e" in raw.lower():
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _set_nested(d: dict[str, Any], keys: list[str], value: Any) -> None:
    """Set a value in a nested dict given a path like ['heatsink', 'width']."""
    for key in keys[:-1]:
        if key not in d:
            d[key] = {}
        d = d[key]
    d[keys[-1]] = value


def convert_m_to_yaml(m_path: Path, yaml_path: Path) -> None:
    """Read a .m config file and write an equivalent .yaml file."""
    text = m_path.read_text(encoding="utf-8", errors="replace")
    config = parse_m_config(text)
    yaml_path.write_text(
        yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
