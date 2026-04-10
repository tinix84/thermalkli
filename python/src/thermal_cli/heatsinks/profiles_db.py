"""Heatsink profiles, materials, and fan-curve database lookups.

CSVs live in the repo-root ``db/`` directory:
- ``db/hs_profiles.csv``   — extruded-fin geometry (mm)
- ``db/hs_materials.csv``  — material conductivity / density
- ``db/fans.csv``          — fan P-Q curves (SI units: m³/s, Pa)
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HsProfile:
    """Extruded-fin heatsink geometric profile (all dimensions in mm)."""

    name: str
    tb_mm: float  # base plate thickness
    hf_mm: float  # fin height
    tf_mm: float  # fin thickness
    bch_mm: float  # channel width


@dataclass(frozen=True)
class HsMaterial:
    """Heatsink material thermal and physical properties."""

    name: str
    k_fin: float  # fin thermal conductivity [W/(m·K)]
    k_plate: float  # base-plate thermal conductivity [W/(m·K)]


@dataclass
class FanCurve:
    """Fan pressure-flow curve."""

    name: str
    qv: np.ndarray  # volumetric flow rate [m³/s]
    hv: np.ndarray  # static pressure [Pa]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_db_dir() -> Path:
    """Locate the ``db/`` directory by walking up from this file's location."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "db"
        if (candidate / "hs_profiles.csv").exists():
            return candidate
    raise FileNotFoundError(f"db/hs_profiles.csv not found in any parent directory of {__file__}")


# ---------------------------------------------------------------------------
# Public lookup functions
# ---------------------------------------------------------------------------


def lookup_hs_profile(name: str) -> HsProfile:
    """Return the heatsink profile matching *name* from ``db/hs_profiles.csv``.

    Parameters
    ----------
    name : str
        Profile name, e.g. ``'I117'`` or ``'Pada SF'``.

    Raises
    ------
    ValueError
        If *name* is not found in the database.
    """
    db_dir = _find_db_dir()
    with open(db_dir / "hs_profiles.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["name"] == name:
                return HsProfile(
                    name=row["name"],
                    tb_mm=float(row["tb_mm"]),
                    hf_mm=float(row["hf_mm"]),
                    tf_mm=float(row["tf_mm"]),
                    bch_mm=float(row["bch_mm"]),
                )
    raise ValueError(f"Heatsink profile '{name}' not found in database. Check db/hs_profiles.csv.")


def lookup_hs_material(name: str) -> HsMaterial:
    """Return the heatsink material matching *name* from ``db/hs_materials.csv``.

    Parameters
    ----------
    name : str
        Material name, e.g. ``'all_aluminum'``.

    Raises
    ------
    ValueError
        If *name* is not found in the database.
    """
    db_dir = _find_db_dir()
    with open(db_dir / "hs_materials.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["name"] == name:
                return HsMaterial(
                    name=row["name"],
                    k_fin=float(row["k_fin"]),
                    k_plate=float(row["k_plate"]),
                )
    raise ValueError(
        f"Heatsink material '{name}' not found in database. Check db/hs_materials.csv."
    )


def lookup_fan(name: str) -> FanCurve:
    """Return the fan curve matching *name* from ``db/fans.csv``.

    Flow-rate values are stored in m³/s and pressure in Pa.

    Parameters
    ----------
    name : str
        Fan name, e.g. ``'EBMW2E200_axial_AC_50Hz'``.

    Raises
    ------
    ValueError
        If *name* is not found in the database.
    """
    db_dir = _find_db_dir()
    with open(db_dir / "fans.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["name"] == name:
                qv = np.array(json.loads(row["qv_m3s"]), dtype=float)
                hv = np.array(json.loads(row["hv_pa"]), dtype=float)
                return FanCurve(name=row["name"], qv=qv, hv=hv)
    raise ValueError(f"Fan '{name}' not found in database. Check db/fans.csv.")
