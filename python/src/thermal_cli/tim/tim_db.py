"""Thermal interface material (TIM) database loader.

Data lives in ``db/tim.csv`` — migrated from ``Thermal_Interface_Materials.xlsx``
in M11.

Units:
- thickness_mm: [mm]
- k_wm1k1: thermal conductivity [W/(m·K)]
- rth_area_*: Rth x Area [mm²·K/W]
- v_iso_kvac: isolation voltage [kVAC]
- max_pressure_ncm2: [N/cm²]
"""

from __future__ import annotations

import csv
from dataclasses import dataclass

from thermal_cli.database import open_database_csv


@dataclass(frozen=True)
class TimEntry:
    """Single TIM database record."""

    active: bool                        # preferred/selected in original DB
    manufacturer: str
    type: str
    description: str
    v_iso_kvac: float | None            # isolation voltage [kVAC]
    thickness_mm: float | None          # no-pressure thickness [mm]
    surface_interface: bool             # has surface interface treatment
    mounting: bool                      # adhesive mounting
    k_wm1k1: float | None              # thermal conductivity [W/(m·K)]
    rth_area_no_press: float | None    # Rth x Area at no pressure [mm²·K/W]
    rth_area_35n: float | None         # Rth x Area @ 35 N/cm² [mm²·K/W]
    rth_area_max: float | None         # Rth x Area at max pressure [mm²·K/W]
    max_pressure_ncm2: float | None    # max application pressure [N/cm²]
    eps_r: float | None                # relative dielectric constant
    notes: str                          # free-text notes


def _opt_float(s: str) -> float | None:
    """Parse an optional float from a CSV cell (empty string → None)."""
    s = s.strip()
    return float(s) if s else None


def _bool_yn(s: str) -> bool:
    """Parse 'yes'/'no' CSV cell to bool."""
    return s.strip().lower() == "yes"


def load_tim_db() -> list[TimEntry]:
    """Load all TIM entries from ``db/tim.csv``.

    Returns
    -------
    list[TimEntry]
        All 38 TIM database records.
    """
    entries: list[TimEntry] = []
    with open_database_csv("tim.csv") as fh:
        for row in csv.DictReader(fh):
            entries.append(
                TimEntry(
                    active=_bool_yn(row["active"]),
                    manufacturer=row["manufacturer"].strip(),
                    type=row["type"].strip(),
                    description=row["description"].strip(),
                    v_iso_kvac=_opt_float(row["v_iso_kvac"]),
                    thickness_mm=_opt_float(row["thickness_mm"]),
                    surface_interface=_bool_yn(row["surface_interface"]),
                    mounting=_bool_yn(row["mounting"]),
                    k_wm1k1=_opt_float(row["k_wm1k1"]),
                    rth_area_no_press=_opt_float(row["rth_area_no_press_mm2kw"]),
                    rth_area_35n=_opt_float(row["rth_area_35n_mm2kw"]),
                    rth_area_max=_opt_float(row["rth_area_max_mm2kw"]),
                    max_pressure_ncm2=_opt_float(row["max_pressure_ncm2"]),
                    eps_r=_opt_float(row["eps_r"]),
                    notes=row["notes"].strip(),
                )
            )
    return entries


def search_tim(keyword: str) -> list[TimEntry]:
    """Search TIM database by keyword (case-insensitive substring).

    Matches against ``manufacturer``, ``type``, and ``description``.

    Parameters
    ----------
    keyword : str
        Search term.

    Returns
    -------
    list[TimEntry]
        All entries where the keyword appears in any of the three fields.
    """
    kw = keyword.lower()
    return [
        e
        for e in load_tim_db()
        if kw in e.manufacturer.lower()
        or kw in e.type.lower()
        or kw in e.description.lower()
    ]
