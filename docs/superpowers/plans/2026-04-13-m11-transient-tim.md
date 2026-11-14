# M11 — Transient + TIM + `db/tim.csv` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add thermal transient (Zth Foster network) and TIM database lookup to `thermal-cli`, with two CLI commands (`zth`, `tim-lookup`) and a migrated `db/tim.csv` from `Thermal_Interface_Materials.xlsx`.

**Architecture:** Two new subpackages — `thermal_cli/transient/` (pure-math Zth functions ported from `lib/zth_foster.m` + `lib/zth_pulsed.m`) and `thermal_cli/tim/` (CSV-backed TIM database, same pattern as `heatsinks/profiles_db.py`). A `commands_m11.py` wires both into the Typer app. All units SI where applicable (time in s, thermal resistance in K/W, conductivity in W/(m·K)); TIM thickness stays in mm and Rth×Area in mm²·K/W — the canonical industry units for TIM datasheets.

**Tech Stack:** Python 3.11+, numpy, pyyaml, pytest, typer, csv (stdlib). No new dependencies.

**Octave source → Python target mapping:**

| Octave source | Python target |
|---|---|
| `lib/zth_foster.m` | `thermal_cli/transient/zth_foster.py::zth_foster()` |
| `lib/zth_pulsed.m` | `thermal_cli/transient/zth_pulsed.py::zth_pulsed()` |
| `lib/cmd_zth.m` | `thermal_cli/cli/commands_m11.py` — `zth` command |
| `lib/cmd_tim_lookup.m` | `thermal_cli/cli/commands_m11.py` — `tim-lookup` command |
| `db/Thermal_Interface_Materials.xlsx` | `db/tim.csv` (38 rows, Task 1) |

---

## File Structure

### New files

```
db/tim.csv                                          # migrated TIM database (Task 1)

python/src/thermal_cli/transient/
├── __init__.py                                     # re-exports zth_foster, zth_pulsed
├── zth_foster.py                                   # Foster network Zth(t)
└── zth_pulsed.py                                   # pulsed duty-cycle Zth via superposition

python/src/thermal_cli/tim/
├── __init__.py                                     # re-exports TimEntry, load_tim_db, search_tim
└── tim_db.py                                       # TimEntry dataclass + CSV loader + search

python/src/thermal_cli/cli/commands_m11.py          # zth + tim-lookup CLI commands

python/tests/unit/
├── test_zth_foster.py
├── test_zth_pulsed.py
└── test_tim_db.py
python/tests/unit/test_cli_m11.py

python/tests/literature/test_lit_zth.py

python/tests/regression/fixtures/zth/single_rc.yaml
python/tests/regression/fixtures/zth/three_rc.yaml
python/tests/regression/fixtures/tim_lookup/list_all.yaml
python/tests/regression/fixtures/tim_lookup/search_kerafol.yaml
```

### Modified files

```
python/src/thermal_cli/cli/main.py                  # register_m11(app)
python/tests/regression/helpers.py                  # run_zth_single_rc, run_tim_list_all
```

---

## Task 1: Create `db/tim.csv`

Migrate `db/Thermal_Interface_Materials.xlsx` (38 data rows, rows 6–43 in xlsx) to a flat CSV.

**Files:**
- Create: `db/tim.csv`

- [ ] **Step 1: Write the CSV**

Create `db/tim.csv` with exactly this content (38 data rows + header):

```
active,manufacturer,type,description,v_iso_kvac,thickness_mm,surface_interface,mounting,k_wm1k1,rth_area_no_press_mm2kw,rth_area_35n_mm2kw,rth_area_max_mm2kw,max_pressure_ncm2,eps_r,notes
yes,LairdTech,Tgard TNC-4,thermally conductive heat curable adhesive insulator foil,6.0,0.125,yes,yes,,,193.55,,,,,
yes,LairdTech,Tgard TNC-5,thermally conductive heat curable adhesive insulator foil,6.0,0.127,yes,yes,,,193.55,,,,,
yes,LairdTech,Tgard 5000,thermally conductive insulator foil with silicone @ 50psi,6.0,0.127,yes,no,,,258.0,148.0,276.0,,,
,Kerafol,Keratherm U90,thermally conductive insulator foil silicone free @ 50psi,4.0,0.2,yes,no,6.0,33.333,45.2,32.9,60.0,3.1,,
,Kerafol,Keratherm U85,thermally conductive insulator foil silicone free,6.0,0.2,yes,no,3.0,,60.2,58.064,60.0,1.96,,
,Kerafol,Keratherm 86/60,thermally conductive insulator foil,5.0,0.25,yes,no,4.5,,56.0,,60.0,1.47,,
,HALA,TFO-X200-SI-A1,thermally conductive insulator foil with silicone,3.0,0.2,yes,no,5.0,40.0,135.484,77.419,100.0,,,
,HALA,TFO-X300-SI-A1,thermally conductive insulator foil with silicone,6.0,0.3,yes,no,5.0,60.0,154.838,103.226,100.0,,,
,HALA,TPC-P051-KA,thermally conductive insulator foil with phase-change compound,5.5,0.051,yes,no,,,72.903,,100.0,4.2,,
,HALA,TPC-P077-KA,thermally conductive insulator foil with phase-change compound,9.2,0.077,yes,no,,,129.032,,100.0,4.2,,
,HALA,TPC-P102-KA,thermally conductive insulator foil with phase-change compound,12.3,0.102,yes,no,,,187.096,,100.0,4.2,,
,HALA,TPC-N051-PI,thermally conductive insulator foil with phase-change compound,5.4,0.051,yes,no,,,83.871,,100.0,4.0,,
,HALA,TPC-N077-PI,thermally conductive insulator foil with phase-change compound,9.0,0.077,yes,no,,,141.935,,100.0,4.0,,
,HALA,TPC-N102-PI,thermally conductive insulator foil with phase-change compound,13.5,0.102,yes,no,,,203.225,,100.0,4.0,,
,HALA,TPC-S050-KA,thermally conductive insulator foil with phase-change compound,4.2,0.05,yes,no,,,83.871,80.645,100.0,1.8,,
,HALA,TPC-S075-KA,thermally conductive insulator foil with phase-change compound,7.8,0.075,yes,no,,,145.161,145.161,100.0,1.8,,
,Bergquist,HF300P-0.001,thermally conductive insulator foil with phase-change compound,5.0,0.102,yes,no,,,77.419,77.419,137.931,4.5,,
,Bergquist,HF300P-0.002,thermally conductive insulator foil with phase-change compound,5.0,0.127,yes,no,,,122.580,116.129,137.931,,,
,Aavid Kunze,KU-ALC5/H,alu foil with phase-change compound,0.0,0.076,yes,no,,,14.839,12.258,70.0,,,
,Aavid Kunze,KU-ALF5/H2,alu foil with phase-change compound,0.0,0.076,yes,no,,,7.742,5.806,70.0,,,
,Aavid Kunze,KU-S30 7-724,thermally conductive silicone cap,6.0,0.3,yes,no,2.0,150.0,129.032,,,,6.3,
,Aavid Kunze,KU-C30 7-724,thermally conductive silicone cap,10.0,0.3,yes,no,1.5,200.0,193.548,,,,6.0,
,Wacker,P12,TIM paste (guarded hot plate),0.0,0.05,yes,no,0.8,62.5,,,,,
,Electrolube,HTC,TIM paste (guarded hot plate),0.0,0.05,yes,no,0.9,55.556,,,,,
,Electrolube,HTCX,TIM paste (guarded hot plate),0.0,0.05,yes,no,1.35,37.037,,,,,
,Electrolube,HTCP,TIM paste (guarded hot plate),0.0,0.05,yes,no,2.5,20.0,,,,,
,Electrolube,HTCPX-LV,TIM paste (guarded hot plate),0.0,0.05,yes,no,3.0,16.667,,,,,
,Electrolube,HTCPX,Gapfiller paste (guarded hot plate),0.0,0.3,yes,no,3.4,88.235,,,,,
,Kerafol,Softtherm 86/600,Gapfiller pad 0.5mm,1.5,0.5,yes,no,6.0,83.333,,,,,
,HALA,TGF-JXS1000-SI-A1,Gapfiller pad 1mm,10.0,1.0,yes,no,2.0,500.0,135.484,122.580,60.0,,quote,
,HALA,TGF-JXS2000-SI-A1,Gapfiller pad 2mm,20.0,2.0,yes,no,2.0,1000.0,174.193,135.484,60.0,,quote,
,LairdTech,Tflex 50000,Gapfiller pad 3mm,14.0,3.0,yes,no,2.8,1071.429,,,,,,
,,Ceramic,Ceramic Al2O3,7.6,0.38,no,no,24.0,15.833,,,,,
,,Ceramic,Ceramic AlN,12.6,0.63,no,no,170.0,3.706,,,,,
,,Ceramic,Ceramic Si3N4,,,,no,no,90.0,,,,,
,,Solder,Solder,0.0,0.1,no,yes,65.0,1.538,,,,,
,,Copper,Copper,0.0,0.3,no,no,385.0,0.779,,,,,
,,Aluminium,Aluminium,0.0,,no,no,235.0,,,,,
```

- [ ] **Step 2: Verify row count**

```bash
python3 -c "
import csv
with open('/home/tinix/claude_wsl/octave/thermal/db/tim.csv') as f:
    rows = list(csv.DictReader(f))
print(f'{len(rows)} rows')
assert len(rows) == 38, f'Expected 38, got {len(rows)}'
print('OK')
"
```
Expected: `38 rows` then `OK`.

- [ ] **Step 3: Commit**

```bash
cd /home/tinix/claude_wsl/octave/thermal
git add db/tim.csv
git commit -m "feat(m11): migrate Thermal_Interface_Materials.xlsx to db/tim.csv (38 rows)"
```

---

## Task 2: TIM database module (`tim_db.py`)

**Files:**
- Create: `python/src/thermal_cli/tim/__init__.py`
- Create: `python/src/thermal_cli/tim/tim_db.py`
- Test: `python/tests/unit/test_tim_db.py`

- [ ] **Step 1: Write failing tests**

Create `python/tests/unit/test_tim_db.py`:

```python
"""Tests for thermal_cli.tim.tim_db."""

from __future__ import annotations

import pytest

from thermal_cli.tim.tim_db import TimEntry, load_tim_db, search_tim


class TestLoadTimDb:
    def test_returns_38_entries(self):
        entries = load_tim_db()
        assert len(entries) == 38

    def test_first_entry_is_tgard_tnc4(self):
        entries = load_tim_db()
        e = entries[0]
        assert e.manufacturer == "LairdTech"
        assert e.type == "Tgard TNC-4"
        assert e.active is True

    def test_active_flag_false_for_kerafol(self):
        entries = load_tim_db()
        kerafol = [e for e in entries if e.manufacturer == "Kerafol"][0]
        assert kerafol.active is False

    def test_numeric_field_none_for_missing(self):
        """Ceramic Si3N4 has no thickness — must be None, not a string."""
        entries = load_tim_db()
        si3n4 = next(e for e in entries if "Si3N4" in e.description)
        assert si3n4.thickness_mm is None

    def test_k_wm1k1_kerafol_u90(self):
        entries = load_tim_db()
        u90 = next(e for e in entries if e.type == "Keratherm U90")
        assert u90.k_wm1k1 == pytest.approx(6.0)


class TestSearchTim:
    def test_search_kerafol_returns_3(self):
        results = search_tim("kerafol")
        assert len(results) == 3
        assert all(e.manufacturer == "Kerafol" for e in results)

    def test_search_case_insensitive(self):
        lower = search_tim("kerafol")
        upper = search_tim("KERAFOL")
        assert len(lower) == len(upper)

    def test_search_no_match_returns_empty(self):
        assert search_tim("xyzzy_does_not_exist") == []

    def test_search_matches_description(self):
        results = search_tim("gapfiller")
        assert len(results) >= 4  # pads + pastes with "Gapfiller" in description

    def test_search_paste_matches_wacker_and_electrolube(self):
        results = search_tim("paste")
        manufacturers = {e.manufacturer for e in results}
        assert "Wacker" in manufacturers
        assert "Electrolube" in manufacturers
```

- [ ] **Step 2: Run to confirm FAIL**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 python -m pytest tests/unit/test_tim_db.py -v 2>&1 | head -15
```
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create `tim/__init__.py`**

Create `python/src/thermal_cli/tim/__init__.py`:

```python
"""Thermal interface material (TIM) database (M11)."""

from thermal_cli.tim.tim_db import TimEntry, load_tim_db, search_tim

__all__ = ["TimEntry", "load_tim_db", "search_tim"]
```

- [ ] **Step 4: Implement `tim_db.py`**

Create `python/src/thermal_cli/tim/tim_db.py`:

```python
"""Thermal interface material (TIM) database loader.

Data lives in ``db/tim.csv`` — migrated from ``Thermal_Interface_Materials.xlsx``
in M11.

Units:
- thickness_mm: [mm]
- k_wm1k1: thermal conductivity [W/(m·K)]
- rth_area_*: Rth × Area [mm²·K/W]
- v_iso_kvac: isolation voltage [kVAC]
- max_pressure_ncm2: [N/cm²]
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


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
    rth_area_no_press: float | None    # Rth×Area at no pressure [mm²·K/W]
    rth_area_35n: float | None         # Rth×Area @ 35 N/cm² [mm²·K/W]
    rth_area_max: float | None         # Rth×Area at max pressure [mm²·K/W]
    max_pressure_ncm2: float | None    # max application pressure [N/cm²]
    eps_r: float | None                # relative dielectric constant
    notes: str                          # free-text notes


def _find_db_dir() -> Path:
    """Locate the ``db/`` directory by walking up from this file's location."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "db"
        if (candidate / "tim.csv").exists():
            return candidate
    raise FileNotFoundError(
        f"db/tim.csv not found in any parent directory of {__file__}"
    )


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
    db_dir = _find_db_dir()
    entries: list[TimEntry] = []
    with open(db_dir / "tim.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            entries.append(
                TimEntry(
                    active=row["active"].strip().lower() == "yes",
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
```

- [ ] **Step 5: Run tests**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 python -m pytest tests/unit/test_tim_db.py -v
```
All 10 must pass.

- [ ] **Step 6: Run ruff**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 ruff check src/thermal_cli/tim/ tests/unit/test_tim_db.py
```

- [ ] **Step 7: Commit**

```bash
cd /home/tinix/claude_wsl/octave/thermal
git add python/src/thermal_cli/tim/__init__.py \
       python/src/thermal_cli/tim/tim_db.py \
       python/tests/unit/test_tim_db.py
git commit -m "feat(m11): add TIM database module (TimEntry, load_tim_db, search_tim)"
```

---

## Task 3: Foster network Zth functions

**Files:**
- Create: `python/src/thermal_cli/transient/__init__.py`
- Create: `python/src/thermal_cli/transient/zth_foster.py`
- Create: `python/src/thermal_cli/transient/zth_pulsed.py`
- Test: `python/tests/unit/test_zth_foster.py`
- Test: `python/tests/unit/test_zth_pulsed.py`

- [ ] **Step 1: Write failing tests for `zth_foster`**

Create `python/tests/unit/test_zth_foster.py`:

```python
"""Tests for thermal_cli.transient.zth_foster."""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.transient.zth_foster import zth_foster


class TestZthFoster:
    def test_single_rc_at_t_end(self):
        """Zth(t_end) for single RC == R*(1 - exp(-t_end/tau))."""
        R = np.array([0.5])
        tau = np.array([0.01])
        zth, t = zth_foster(R, tau, t_end=0.1)
        expected = 0.5 * (1.0 - np.exp(-0.1 / 0.01))
        assert zth[-1] == pytest.approx(expected, rel=1e-6)

    def test_returns_correct_shapes(self):
        R = np.array([0.3, 0.2])
        tau = np.array([0.001, 0.01])
        zth, t = zth_foster(R, tau, t_end=1.0, n_points=50)
        assert zth.shape == (50,)
        assert t.shape == (50,)

    def test_time_axis_log_spaced(self):
        """t should be log-spaced from ~min(tau)/10 to t_end."""
        R = np.array([1.0])
        tau = np.array([0.01])
        _, t = zth_foster(R, tau, t_end=1.0, n_points=100)
        # Check log-spacing: consecutive ratios should be constant
        ratios = t[1:] / t[:-1]
        np.testing.assert_allclose(ratios, ratios[0], rtol=1e-9)

    def test_monotonically_increasing(self):
        """Zth must be monotonically non-decreasing."""
        R = np.array([0.2, 0.3, 0.1])
        tau = np.array([0.001, 0.01, 0.1])
        zth, _ = zth_foster(R, tau, t_end=10.0)
        assert np.all(np.diff(zth) >= 0)

    def test_saturates_at_sum_of_R(self):
        """For t >> max(tau), Zth → sum(R)."""
        R = np.array([0.2, 0.3, 0.1])
        tau = np.array([0.001, 0.002, 0.005])
        rth_total = float(np.sum(R))
        zth, _ = zth_foster(R, tau, t_end=1.0, n_points=200)
        assert zth[-1] == pytest.approx(rth_total, rel=1e-4)

    def test_zero_at_t_zero_approx(self):
        """Zth should be near zero at t << min(tau)."""
        R = np.array([1.0])
        tau = np.array([1.0])
        zth, t = zth_foster(R, tau, t_end=10.0, n_points=200)
        # First point is at min(tau)/10 = 0.1s
        assert zth[0] == pytest.approx(R[0] * (1 - np.exp(-t[0] / tau[0])), rel=1e-6)
```

- [ ] **Step 2: Write failing tests for `zth_pulsed`**

Create `python/tests/unit/test_zth_pulsed.py`:

```python
"""Tests for thermal_cli.transient.zth_pulsed."""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.transient.zth_foster import zth_foster
from thermal_cli.transient.zth_pulsed import zth_pulsed


class TestZthPulsed:
    def test_duty_1_equals_continuous(self):
        """Duty=1 (continuous) must equal the standard Foster Zth."""
        R = np.array([0.5])
        tau = np.array([0.01])
        zth_cont, t = zth_foster(R, tau, t_end=0.1, n_points=20)
        zth_p = zth_pulsed(R, tau, t, duty=1.0, period=1.0)
        np.testing.assert_allclose(zth_p, zth_cont, rtol=1e-4)

    def test_duty_less_than_1_lower_than_continuous(self):
        """Pulsed Zth (D<1) must be <= continuous Zth at all time points."""
        R = np.array([0.3, 0.2])
        tau = np.array([0.001, 0.01])
        _, t = zth_foster(R, tau, t_end=0.1, n_points=30)
        zth_cont, _ = zth_foster(R, tau, t_end=0.1, n_points=30)
        zth_p = zth_pulsed(R, tau, t, duty=0.5, period=0.02)
        assert np.all(zth_p <= zth_cont + 1e-10)

    def test_returns_correct_shape(self):
        R = np.array([0.5])
        tau = np.array([0.01])
        t = np.logspace(-4, -1, 15)
        zth_p = zth_pulsed(R, tau, t, duty=0.3, period=0.01)
        assert zth_p.shape == (15,)

    def test_nonnegative(self):
        R = np.array([0.2, 0.3])
        tau = np.array([0.001, 0.01])
        t = np.logspace(-4, 0, 40)
        zth_p = zth_pulsed(R, tau, t, duty=0.5, period=0.05)
        assert np.all(zth_p >= -1e-10)
```

- [ ] **Step 3: Run to confirm FAIL**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 python -m pytest tests/unit/test_zth_foster.py tests/unit/test_zth_pulsed.py -v 2>&1 | head -15
```
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Create `transient/__init__.py`**

Create `python/src/thermal_cli/transient/__init__.py`:

```python
"""Thermal transient analysis: Foster Zth network (M11)."""

from thermal_cli.transient.zth_foster import zth_foster
from thermal_cli.transient.zth_pulsed import zth_pulsed

__all__ = ["zth_foster", "zth_pulsed"]
```

- [ ] **Step 5: Implement `zth_foster.py`**

Create `python/src/thermal_cli/transient/zth_foster.py`:

```python
"""Foster thermal network transient impedance Zth(t).

Ports ``lib/zth_foster.m``.

Formula: ``Zth(t) = Σ_i R_i * (1 - exp(-t / τ_i))``

Time axis is log-spaced from ``min(τ) / 10`` to ``t_end``.
"""

from __future__ import annotations

import numpy as np


def zth_foster(
    r: np.ndarray,
    tau: np.ndarray,
    t_end: float,
    n_points: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute Foster-network transient thermal impedance Zth(t).

    Parameters
    ----------
    r : np.ndarray
        Array of Foster-branch thermal resistances [K/W].
    tau : np.ndarray
        Array of Foster-branch time constants τ_i = R_i·C_i [s].
    t_end : float
        End time of the Zth curve [s].
    n_points : int
        Number of log-spaced time points (default 200).

    Returns
    -------
    zth : np.ndarray
        Thermal impedance values [K/W], shape (n_points,).
    t : np.ndarray
        Time axis [s], log-spaced from min(τ)/10 to t_end, shape (n_points,).
    """
    r = np.asarray(r, dtype=float)
    tau = np.asarray(tau, dtype=float)
    t = np.logspace(np.log10(np.min(tau) / 10.0), np.log10(t_end), n_points)
    zth = np.zeros(n_points, dtype=float)
    for ri, taui in zip(r, tau):
        zth += ri * (1.0 - np.exp(-t / taui))
    return zth, t
```

- [ ] **Step 6: Implement `zth_pulsed.py`**

Create `python/src/thermal_cli/transient/zth_pulsed.py`:

```python
"""Pulsed-power transient thermal impedance via superposition.

Ports ``lib/zth_pulsed.m``.

For a periodic square pulse with duty cycle D and period T, the effective
transient thermal impedance at time t is computed by superposition of the
Foster step-response on and off transitions:

    Zth_pulsed(t) = Σ_{n=0}^{N} [Zth_step(t - n·T) - Zth_step(t - D·T - n·T)]

where terms with a negative time argument are zero, and N is limited to 100
pulses for computational efficiency.
"""

from __future__ import annotations

import numpy as np


def _foster_step(t_val: float, r: np.ndarray, tau: np.ndarray) -> float:
    """Foster Zth at a single time point (0 for t_val <= 0)."""
    if t_val <= 0.0:
        return 0.0
    return float(np.sum(r * (1.0 - np.exp(-t_val / tau))))


def zth_pulsed(
    r: np.ndarray,
    tau: np.ndarray,
    t: np.ndarray,
    duty: float,
    period: float,
) -> np.ndarray:
    """Effective pulsed transient thermal impedance Zth_pulsed(t).

    Parameters
    ----------
    r : np.ndarray
        Foster-branch thermal resistances [K/W].
    tau : np.ndarray
        Foster-branch time constants [s].
    t : np.ndarray
        Time points at which to evaluate [s].
    duty : float
        Pulse duty cycle D ∈ (0, 1].
    period : float
        Pulse period T [s].

    Returns
    -------
    np.ndarray
        Pulsed Zth values [K/W], same shape as ``t``.
    """
    r = np.asarray(r, dtype=float)
    tau = np.asarray(tau, dtype=float)
    zth = np.zeros(len(t), dtype=float)
    for k, tk in enumerate(t):
        n_pulses = min(int(tk / period) + 1, 100)
        val = 0.0
        for n in range(n_pulses):
            val += _foster_step(tk - n * period, r, tau)
            val -= _foster_step(tk - duty * period - n * period, r, tau)
        zth[k] = val
    return zth
```

- [ ] **Step 7: Run tests**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 python -m pytest tests/unit/test_zth_foster.py tests/unit/test_zth_pulsed.py -v
```
All 10 must pass.

- [ ] **Step 8: Run ruff**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 ruff check src/thermal_cli/transient/ tests/unit/test_zth_foster.py tests/unit/test_zth_pulsed.py
```

- [ ] **Step 9: Commit**

```bash
cd /home/tinix/claude_wsl/octave/thermal
git add python/src/thermal_cli/transient/__init__.py \
       python/src/thermal_cli/transient/zth_foster.py \
       python/src/thermal_cli/transient/zth_pulsed.py \
       python/tests/unit/test_zth_foster.py \
       python/tests/unit/test_zth_pulsed.py
git commit -m "feat(m11): add Foster Zth and pulsed Zth transient functions"
```

---

## Task 4: CLI commands `zth` and `tim-lookup`

**Files:**
- Create: `python/src/thermal_cli/cli/commands_m11.py`
- Modify: `python/src/thermal_cli/cli/main.py`
- Test: `python/tests/unit/test_cli_m11.py`

- [ ] **Step 1: Write failing CLI smoke tests**

Create `python/tests/unit/test_cli_m11.py`:

```python
"""Smoke tests for M11 CLI commands: zth and tim-lookup."""

from __future__ import annotations

import textwrap

from typer.testing import CliRunner

from thermal_cli.cli.main import app

runner = CliRunner()

_ZTH_YAML = textwrap.dedent(
    """\
    r: [0.3, 0.2]
    tau: [0.001, 0.01]
    t_end: 0.1
    n_points: 50
    """
)


class TestZthCommand:
    def test_zth_from_args_smoke(self, tmp_path):
        result = runner.invoke(
            app, ["zth", "--r", "0.3 0.2", "--tau", "0.001 0.01", "--t-end", "0.1"]
        )
        assert result.exit_code == 0, result.output
        assert "rth_total" in result.output
        assert "zth_at_end" in result.output

    def test_zth_from_config_smoke(self, tmp_path):
        cfg = tmp_path / "zth.yaml"
        cfg.write_text(_ZTH_YAML)
        result = runner.invoke(app, ["zth", "--config", str(cfg)])
        assert result.exit_code == 0, result.output
        assert "rth_total" in result.output

    def test_zth_save_csv(self, tmp_path):
        out = tmp_path / "out.csv"
        result = runner.invoke(
            app,
            ["zth", "--r", "0.5", "--tau", "0.01", "--t-end", "0.1",
             "--save-csv", str(out)],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()
        content = out.read_text()
        assert "time_s" in content
        assert "zth_kw" in content

    def test_zth_missing_r_raises(self):
        result = runner.invoke(app, ["zth", "--tau", "0.01", "--t-end", "0.1"])
        assert result.exit_code != 0

    def test_zth_pulsed_duty_period(self):
        result = runner.invoke(
            app,
            ["zth", "--r", "0.5", "--tau", "0.01", "--t-end", "0.1",
             "--duty", "0.5", "--period", "0.02"],
        )
        assert result.exit_code == 0, result.output
        assert "zth_pulsed_at_end" in result.output


class TestTimLookupCommand:
    def test_list_all(self):
        result = runner.invoke(app, ["tim-lookup", "--list"])
        assert result.exit_code == 0, result.output
        assert "LairdTech" in result.output
        assert "Kerafol" in result.output

    def test_search_kerafol(self):
        result = runner.invoke(app, ["tim-lookup", "--search", "kerafol"])
        assert result.exit_code == 0, result.output
        assert "Kerafol" in result.output

    def test_search_no_match(self):
        result = runner.invoke(app, ["tim-lookup", "--search", "xyzzy_nomatch"])
        assert result.exit_code == 0, result.output
        assert "No entries found" in result.output

    def test_list_and_search_mutually_exclusive(self):
        result = runner.invoke(
            app, ["tim-lookup", "--list", "--search", "kerafol"]
        )
        assert result.exit_code != 0
```

- [ ] **Step 2: Run to confirm FAIL**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 python -m pytest tests/unit/test_cli_m11.py -v 2>&1 | head -15
```
Expected: FAIL (`command not registered`).

- [ ] **Step 3: Create `commands_m11.py`**

Create `python/src/thermal_cli/cli/commands_m11.py`:

```python
"""M11 CLI commands: zth (Foster Zth) and tim-lookup."""

from __future__ import annotations

import csv as _csv
from pathlib import Path
from typing import Annotated, Optional

import numpy as np
import typer
import yaml


def register_all(app: typer.Typer) -> None:
    """Register M11 commands on the Typer app."""

    @app.command("zth")
    def zth_cmd(
        r_str: Annotated[Optional[str], typer.Option("--r", help="Space-separated Foster R values [K/W]")] = None,
        tau_str: Annotated[Optional[str], typer.Option("--tau", help="Space-separated Foster τ values [s]")] = None,
        t_end: Annotated[Optional[float], typer.Option("--t-end", help="End time [s]")] = None,
        n_points: Annotated[int, typer.Option("--n-points", help="Number of log-spaced time points")] = 200,
        duty: Annotated[Optional[float], typer.Option("--duty", help="Pulse duty cycle [0–1]")] = None,
        period: Annotated[Optional[float], typer.Option("--period", help="Pulse period [s]")] = None,
        config: Annotated[Optional[Path], typer.Option("--config", help="YAML config file")] = None,
        save_csv: Annotated[Optional[Path], typer.Option("--save-csv", help="Save Zth curve to CSV")] = None,
    ) -> None:
        """Compute Foster-network transient thermal impedance Zth(t)."""
        from thermal_cli.transient.zth_foster import zth_foster
        from thermal_cli.transient.zth_pulsed import zth_pulsed

        # Load from config file if provided
        if config is not None:
            if not config.exists():
                typer.echo(f"Error: config file not found: {config}", err=True)
                raise typer.Exit(1)
            with open(config) as fh:
                raw = yaml.safe_load(fh)
            r_vals = np.array(raw["r"], dtype=float)
            tau_vals = np.array(raw["tau"], dtype=float)
            t_end = float(raw.get("t_end", t_end or 1.0))
            n_points = int(raw.get("n_points", n_points))
            duty = raw.get("duty", duty)
            period = raw.get("period", period)
        else:
            if r_str is None:
                typer.echo("Error: --r is required (or use --config)", err=True)
                raise typer.Exit(1)
            if tau_str is None:
                typer.echo("Error: --tau is required (or use --config)", err=True)
                raise typer.Exit(1)
            if t_end is None:
                typer.echo("Error: --t-end is required (or use --config)", err=True)
                raise typer.Exit(1)
            r_vals = np.array([float(x) for x in r_str.split()])
            tau_vals = np.array([float(x) for x in tau_str.split()])

        if len(r_vals) != len(tau_vals):
            typer.echo("Error: --r and --tau must have the same number of values", err=True)
            raise typer.Exit(1)

        zth, t = zth_foster(r_vals, tau_vals, t_end=t_end, n_points=n_points)
        rth_total = float(np.sum(r_vals))

        typer.echo(f"rth_total     = {rth_total:.4f} K/W")
        typer.echo(f"zth_at_end    = {zth[-1]:.4f} K/W  (t={t[-1]:.4g} s)")

        # Spot values
        for target_ms in [1, 10, 100, 1000]:
            target_s = target_ms / 1000.0
            if target_s <= t[-1]:
                val = float(np.interp(target_s, t, zth))
                typer.echo(f"zth_at_{target_ms}ms   = {val:.4f} K/W")

        # Pulsed Zth
        if duty is not None and period is not None:
            duty = float(duty)
            period = float(period)
            zth_p = zth_pulsed(r_vals, tau_vals, t, duty=duty, period=period)
            typer.echo(f"zth_pulsed_at_end = {zth_p[-1]:.4f} K/W  (D={duty}, T={period} s)")

        # Save CSV
        if save_csv is not None:
            with open(save_csv, "w", newline="") as fh:
                writer = _csv.writer(fh)
                writer.writerow(["time_s", "zth_kw"])
                for ti, zi in zip(t, zth):
                    writer.writerow([f"{ti:.6e}", f"{zi:.6f}"])
            typer.echo(f"Saved: {save_csv}")

    @app.command("tim-lookup")
    def tim_lookup_cmd(
        list_all: Annotated[bool, typer.Option("--list", help="List all TIM entries")] = False,
        search: Annotated[Optional[str], typer.Option("--search", help="Search keyword")] = None,
    ) -> None:
        """Look up thermal interface materials from db/tim.csv."""
        from thermal_cli.tim.tim_db import load_tim_db, search_tim

        if list_all and search is not None:
            typer.echo("Error: --list and --search are mutually exclusive", err=True)
            raise typer.Exit(1)
        if not list_all and search is None:
            typer.echo("Error: specify --list or --search <keyword>", err=True)
            raise typer.Exit(1)

        entries = load_tim_db() if list_all else search_tim(search)

        if not entries:
            typer.echo("No entries found.")
            return

        # Header
        typer.echo(f"{'Manufacturer':<16} {'Type':<22} {'k [W/mK]':>10} {'Rth@35N [mm²K/W]':>18} {'Thickness [mm]':>15}")
        typer.echo("-" * 85)
        for e in entries:
            k_str = f"{e.k_wm1k1:.2f}" if e.k_wm1k1 is not None else "—"
            rth_str = f"{e.rth_area_35n:.1f}" if e.rth_area_35n is not None else "—"
            th_str = f"{e.thickness_mm:.3f}" if e.thickness_mm is not None else "—"
            typer.echo(f"{e.manufacturer:<16} {e.type:<22} {k_str:>10} {rth_str:>18} {th_str:>15}")
        typer.echo(f"\n{len(entries)} entries.")
```

- [ ] **Step 4: Wire into `main.py`**

Read `python/src/thermal_cli/cli/main.py`. Add after the M10 import+call:

```python
from thermal_cli.cli.commands_m11 import register_all as register_m11
```

```python
register_m11(app)
```

- [ ] **Step 5: Run tests**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 python -m pytest tests/unit/test_cli_m11.py -v
```
All 10 must pass.

- [ ] **Step 6: Run full suite**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 python -m pytest tests/ --tb=short -q 2>&1 | tail -5
```

- [ ] **Step 7: Run ruff**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 ruff check src/thermal_cli/cli/commands_m11.py src/thermal_cli/cli/main.py tests/unit/test_cli_m11.py
```

- [ ] **Step 8: Commit**

```bash
cd /home/tinix/claude_wsl/octave/thermal
git add python/src/thermal_cli/cli/commands_m11.py \
       python/src/thermal_cli/cli/main.py \
       python/tests/unit/test_cli_m11.py
git commit -m "feat(m11): add zth and tim-lookup CLI commands"
```

---

## Task 5: Literature tests + regression fixtures

**Files:**
- Create: `python/tests/literature/test_lit_zth.py`
- Create: `python/tests/regression/fixtures/zth/single_rc.yaml`
- Create: `python/tests/regression/fixtures/zth/three_rc.yaml`
- Create: `python/tests/regression/fixtures/tim_lookup/list_all.yaml`
- Create: `python/tests/regression/fixtures/tim_lookup/search_kerafol.yaml`
- Modify: `python/tests/regression/helpers.py`

- [ ] **Step 1: Write literature tests**

Create `python/tests/literature/test_lit_zth.py`:

```python
"""Analytic sanity checks for Foster Zth.

Reference: for a single RC element, Zth(t) = R*(1-exp(-t/tau)).
At t >> tau, Zth → R (saturation). At t = tau, Zth = R*(1-1/e) ≈ 0.632*R.
"""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.transient.zth_foster import zth_foster
from thermal_cli.transient.zth_pulsed import zth_pulsed


class TestZthLiterature:
    def test_single_rc_exact_at_tau(self):
        """At t = tau, Zth = R*(1 - 1/e)."""
        R = np.array([1.0])
        tau = np.array([0.01])
        zth, t = zth_foster(R, tau, t_end=0.1, n_points=500)
        val_at_tau = float(np.interp(0.01, t, zth))
        expected = 1.0 * (1.0 - np.exp(-1.0))  # ≈ 0.6321
        assert val_at_tau == pytest.approx(expected, rel=1e-3)

    def test_three_rc_saturation(self):
        """Zth saturates at sum(R) for t >> max(tau)."""
        R = np.array([0.1, 0.15, 0.05])
        tau = np.array([0.001, 0.005, 0.02])
        rth_total = float(np.sum(R))  # 0.3 K/W
        zth, _ = zth_foster(R, tau, t_end=1.0, n_points=300)
        assert zth[-1] == pytest.approx(rth_total, rel=1e-4)

    def test_superposition_two_elements_equals_sum(self):
        """Zth of two RC elements == sum of individual Zth curves."""
        R1, tau1 = np.array([0.3]), np.array([0.005])
        R2, tau2 = np.array([0.2]), np.array([0.05])
        zth1, t = zth_foster(R1, tau1, t_end=1.0, n_points=100)
        zth2, _ = zth_foster(R2, tau2, t_end=1.0, n_points=100)
        zth_both, _ = zth_foster(np.array([0.3, 0.2]), np.array([0.005, 0.05]), t_end=1.0, n_points=100)
        np.testing.assert_allclose(zth1 + zth2, zth_both, rtol=1e-10)

    def test_pulsed_duty_1_equals_continuous(self):
        """D=1 pulsed == continuous Foster Zth."""
        R = np.array([0.3, 0.2])
        tau = np.array([0.001, 0.01])
        zth_cont, t = zth_foster(R, tau, t_end=0.5, n_points=100)
        zth_p = zth_pulsed(R, tau, t, duty=1.0, period=1.0)
        np.testing.assert_allclose(zth_p, zth_cont, rtol=1e-4)
```

- [ ] **Step 2: Run literature tests**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 python -m pytest tests/literature/test_lit_zth.py -v
```
All 4 must pass.

- [ ] **Step 3: Add regression wrappers to `helpers.py`**

Read the end of `python/tests/regression/helpers.py`. Append:

```python
# ---------------------------------------------------------------------------
# M11 zth + tim-lookup wrappers
# ---------------------------------------------------------------------------


def run_zth_single_rc() -> dict:
    """Regression wrapper: single RC Foster element."""
    import numpy as np

    from thermal_cli.transient.zth_foster import zth_foster

    R = np.array([0.5])
    tau = np.array([0.01])
    zth, t = zth_foster(R, tau, t_end=0.1, n_points=200)
    return {
        "rth_total": float(np.sum(R)),
        "zth_at_end": float(zth[-1]),
    }


def run_zth_three_rc() -> dict:
    """Regression wrapper: three RC Foster elements."""
    import numpy as np

    from thermal_cli.transient.zth_foster import zth_foster

    R = np.array([0.1, 0.15, 0.05])
    tau = np.array([0.001, 0.005, 0.02])
    zth, t = zth_foster(R, tau, t_end=1.0, n_points=200)
    return {
        "rth_total": float(np.sum(R)),
        "zth_at_end": float(zth[-1]),
    }


def run_tim_list_all() -> dict:
    """Regression wrapper: load all TIM entries."""
    from thermal_cli.tim.tim_db import load_tim_db

    entries = load_tim_db()
    return {"count": len(entries)}


def run_tim_search_kerafol() -> dict:
    """Regression wrapper: search TIM for 'kerafol'."""
    from thermal_cli.tim.tim_db import search_tim

    results = search_tim("kerafol")
    return {"count": len(results)}
```

- [ ] **Step 4: Create regression fixture YAMLs**

Create `python/tests/regression/fixtures/zth/single_rc.yaml`:

```yaml
command: zth
description: Single RC Foster element — regression for zth_foster baseline.
python_only: true
python_call:
  module: tests.regression.helpers
  function: run_zth_single_rc
  args: {}
```

Create `python/tests/regression/fixtures/zth/three_rc.yaml`:

```yaml
command: zth
description: Three RC Foster elements — regression for zth_foster multi-element.
python_only: true
python_call:
  module: tests.regression.helpers
  function: run_zth_three_rc
  args: {}
```

Create `python/tests/regression/fixtures/tim_lookup/list_all.yaml`:

```yaml
command: tim-lookup
description: List all TIM entries — regression for load_tim_db row count (38).
python_only: true
python_call:
  module: tests.regression.helpers
  function: run_tim_list_all
  args: {}
```

Create `python/tests/regression/fixtures/tim_lookup/search_kerafol.yaml`:

```yaml
command: tim-lookup
description: Search TIM for 'kerafol' — regression for search_tim result count (3).
python_only: true
python_call:
  module: tests.regression.helpers
  function: run_tim_search_kerafol
  args: {}
```

- [ ] **Step 5: Run regression + literature suite**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 python -m pytest tests/regression/ tests/literature/test_lit_zth.py -v --tb=short 2>&1 | tail -15
```
All must pass.

- [ ] **Step 6: Run ruff**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 ruff check tests/literature/test_lit_zth.py tests/regression/helpers.py
```

- [ ] **Step 7: Commit**

```bash
cd /home/tinix/claude_wsl/octave/thermal
git add python/tests/literature/test_lit_zth.py \
       python/tests/regression/fixtures/zth/ \
       python/tests/regression/fixtures/tim_lookup/ \
       python/tests/regression/helpers.py
git commit -m "test(m11): add literature tests and regression fixtures for zth + tim-lookup"
```

---

## Task 6: Final integration — lint, format, full suite

- [ ] **Step 1: Run ruff lint**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 ruff check src tests
```
Fix any errors.

- [ ] **Step 2: Run ruff format**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 ruff format src tests
```

- [ ] **Step 3: Run full suite**

```bash
cd /home/tinix/claude_wsl/octave/thermal/python && conda run -n ntbees2 python -m pytest tests/ --tb=short -q 2>&1 | tail -5
```
Expected: all pass (≈ 404+ tests: 380 existing + ~24 new M11 tests).

- [ ] **Step 4: Commit if changes from formatter**

```bash
cd /home/tinix/claude_wsl/octave/thermal && git diff --name-only
```
If any files changed:
```bash
git add -u
git commit -m "style(m11): apply ruff format"
```

---

## Self-Review

**Spec coverage:**

| Spec requirement | Task | Status |
|---|---|---|
| Migrate `Thermal_Interface_Materials.xlsx` → `db/tim.csv` | Task 1 | ✅ |
| `TimEntry` dataclass + `load_tim_db()` + `search_tim()` | Task 2 | ✅ |
| `zth_foster()` — Foster Zth(t) | Task 3 | ✅ |
| `zth_pulsed()` — pulsed duty-cycle Zth | Task 3 | ✅ |
| `zth` CLI command (`--r`, `--tau`, `--t-end`, `--duty`, `--period`, `--config`, `--save-csv`) | Task 4 | ✅ |
| `tim-lookup` CLI command (`--list`, `--search`) | Task 4 | ✅ |
| Literature tests for Zth | Task 5 | ✅ |
| Regression fixtures (4 python_only) | Task 5 | ✅ |
| Lint + format + full suite | Task 6 | ✅ |

**Type consistency:**
- `zth_foster(r, tau, t_end, n_points) -> tuple[np.ndarray, np.ndarray]` — used in `commands_m11.py` and `helpers.py` ✅
- `zth_pulsed(r, tau, t, duty, period) -> np.ndarray` — `t` is the time array from `zth_foster` ✅
- `TimEntry.rth_area_35n: float | None` — accessed in `tim-lookup` output as `e.rth_area_35n` ✅
- `search_tim(keyword: str) -> list[TimEntry]` — used in CLI and regression helper ✅
- CSV column `rth_area_35n_mm2kw` → `TimEntry.rth_area_35n` (field name is shorter; unit in docstring) ✅

**Placeholder scan:** No TBD/TODO patterns. All steps have complete code.

**`test_list_and_search_mutually_exclusive`:** The CLI raises `Exit(1)` before reaching the DB — tested correctly.

**Performance note:** `zth_pulsed` with 100 pulses × n_points × len(R) iterations is Python loops. For n_points=200 and 3 RC elements, this is ~60k iterations — well under 1s.
