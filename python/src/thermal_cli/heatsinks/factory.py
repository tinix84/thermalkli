"""Heatsink factory — create heatsink objects from CSV database.

Ported from ``mfiles/Thermal/Model/heatsinkFactory.m``.
"""

from __future__ import annotations

import csv
from pathlib import Path

from thermal_cli.heatsinks.extruded_fin import ExtrudedFin


def _find_db_dir() -> Path:
    """Locate the db/ directory at the repo root."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "db"
        if (candidate / "heatsinks_extruded.csv").exists():
            return candidate
    raise FileNotFoundError("No db/heatsinks_extruded.csv found in any parent directory")


def heatsink_factory(heatsink_ref: str) -> ExtrudedFin:
    """Create a heatsink from its database reference string.

    Currently supports extruded-fin heatsinks from ``db/heatsinks_extruded.csv``.

    Parameters
    ----------
    heatsink_ref : str
        Reference ID, e.g., ``'HS_EX_001'``.

    Raises
    ------
    ValueError
        If the reference is not found in the database.
    """
    db_dir = _find_db_dir()

    # Search extruded database
    extruded_path = db_dir / "heatsinks_extruded.csv"
    with open(extruded_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["heatsinkRef"] == heatsink_ref:
                return ExtrudedFin(
                    heatsink_ref=heatsink_ref,
                    num_channel=int(row["numChannel"]),
                    thick_heatsink=float(row["l_2"]),
                    thick_wall=float(row["l_3"]),
                    width_channel=float(row["l_5"]),
                    k_sink=float(row["k"]),
                    rho_sink=float(row["rho"]),
                )

    raise ValueError(
        f"Heatsink '{heatsink_ref}' not found in database. Check db/heatsinks_extruded.csv."
    )
