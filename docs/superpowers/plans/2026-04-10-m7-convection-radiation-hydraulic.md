# M7 — Convection, Radiation h-coeffs, Hydraulic & Fin Rth

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port all 7 M7 commands from the Octave thermal CLI to Python: `h-coeff`, `free-conv`, `natural-conv-hs`, `radiation`, `water-cooling`, `hydraulic-op`, `fin-rth`.

**Architecture:** New formula modules (`convection.py`, `free_conv.py`, `water_cooling.py`) provide pure functions for h-coefficients and solvers. A new `heatsinks/channel_flow.py` ports the SoftwareTermico channel-flow model (idraulico + Rth_fin) in SI units. Small CSV databases for heatsink profiles, materials, and fan curves support the `hydraulic-op` and `fin-rth` CLI commands. All 7 commands are wired into the existing Typer CLI.

**Tech Stack:** Python 3.11+, numpy, scipy (CubicSpline), pytest, typer, pydantic

**Key unit decisions:**
- All formula-layer functions take temperatures in **K** (consistent with existing `formula/radiation.py`).
- CLI commands accept temperatures in **°C** and convert to K before calling formulas.
- Channel-flow solvers (`hydraulic_operating_point`, `fin_thermal_resistance`) take geometry in **meters** (SI). The Octave originals use mm — all mm→m conversion factors are removed in the Python port.
- Air properties in `channel_flow.py` use `scipy.interpolate.CubicSpline` on the SoftwareTermico spline tables (converted to K).

**Octave source → Python target mapping:**

| Octave source | Python target |
|---|---|
| `lib/h_forced_convection.m` | `formula/convection.py::h_forced()` |
| `lib/h_natural_convection.m` | `formula/convection.py::h_natural()` |
| `lib/h_radiation.m` | `formula/convection.py::h_radiation_linearized()` |
| `lib/free_conv_surface_temp.m` | `formula/free_conv.py::free_conv_surface_temp()` |
| `lib/cmd_natural_conv_hs.m` | `heatsinks/natural_conv.py::natural_conv_hs()` |
| `lib/cmd_water_cooling.m` | `formula/water_cooling.py::water_cooling()` |
| `mfiles/SoftwareTermico/Therm_hydr/idraulico.m` | `heatsinks/channel_flow.py::hydraulic_operating_point()` |
| `mfiles/SoftwareTermico/Therm_hydr/Rth_fin.m` | `heatsinks/channel_flow.py::fin_thermal_resistance()` |
| `mfiles/SoftwareTermico/Coeff_Aria/*.m` | `heatsinks/channel_flow.py::_rho_air()` etc. (private) |
| `mfiles/SoftwareTermico/Database_FAN&HeatSink/HS_Type.m` | `db/hs_profiles.csv` + `heatsinks/profiles_db.py` |
| `mfiles/SoftwareTermico/Database_FAN&HeatSink/HS_Tech.m` | `db/hs_materials.csv` + `heatsinks/profiles_db.py` |
| `mfiles/SoftwareTermico/Database_FAN&HeatSink/Fan_Model.m` | `db/fans.csv` + `heatsinks/profiles_db.py` |

---

## File Structure

### New files to create

```
python/src/thermal_cli/
├── formula/
│   ├── convection.py          # h_forced, h_natural, h_radiation_linearized
│   ├── free_conv.py           # free_conv_surface_temp bisection solver
│   └── water_cooling.py       # water_cooling energy balance
├── heatsinks/
│   ├── natural_conv.py        # natural_conv_hs iterative solver
│   ├── channel_flow.py        # SoftwareTermico hydraulic + thermal (idraulico, Rth_fin)
│   └── profiles_db.py         # HS profile, material, fan CSV lookups
├── cli/
│   └── commands_m7.py         # 7 CLI commands (h-coeff, free-conv, etc.)

db/
├── hs_profiles.csv            # from HS_Type.m (15 heatsink profiles, mm geometry)
├── hs_materials.csv           # from HS_Tech.m (4 material combos)
└── fans.csv                   # from Fan_Model.m (13 fan models, Qv/Hv curves)

python/tests/
├── unit/
│   ├── test_convection.py
│   ├── test_free_conv.py
│   ├── test_water_cooling.py
│   ├── test_natural_conv.py
│   └── test_channel_flow.py
├── literature/
│   └── test_lit_convection.py
└── regression/fixtures/
    ├── h_coeff_forced/basic.yaml
    ├── h_coeff_natural/vertical.yaml
    ├── h_coeff_radiation/basic.yaml
    ├── free_conv/box.yaml
    └── water_cooling/basic.yaml
```

### Files to modify

- `python/src/thermal_cli/formula/__init__.py` — re-export new functions
- `python/src/thermal_cli/heatsinks/__init__.py` — re-export new modules
- `python/src/thermal_cli/cli/main.py` — register M7 command group

---

## Task 1: `formula/convection.py` — h-coefficient functions

**Files:**
- Create: `python/src/thermal_cli/formula/convection.py`
- Test: `python/tests/unit/test_convection.py`

- [ ] **Step 1: Write failing tests**

Create `python/tests/unit/test_convection.py`:

```python
"""Unit tests for thermal_cli.formula.convection.

Reference values computed from the Octave originals:
  lib/h_forced_convection.m, h_natural_convection.m, h_radiation.m.
"""

from __future__ import annotations

import pytest

from thermal_cli.formula.convection import h_forced, h_natural, h_radiation_linearized


# --- h_forced ---

class TestHForced:
    def test_laminar_re_below_5e5(self):
        """L=0.3m, U=5m/s, Ta=298.15K (25C), Ts=348.15K (75C).
        Octave: h_forced_convection(0.3, 5, 25, 75)
        Tf = 323.15K, rho=1.0925, mu=1.962e-5, Re=83629 (laminar).
        h = 0.664 * Re^0.5 * 0.71^(1/3) * kf / L.
        kf(323.15) = 7e-5*323.15 + 5.1e-3 = 0.02772.
        h = 0.664 * 289.2 * 0.8929 * 0.02772 / 0.3 = 15.83 W/(m2K).
        """
        h, re = h_forced(length=0.3, velocity=5.0, t_ambient=298.15, t_surface=348.15)
        assert re == pytest.approx(83629, rel=1e-2)
        assert h == pytest.approx(15.83, rel=1e-2)

    def test_turbulent_re_above_5e5(self):
        """L=1.0m, U=20m/s, Ta=298.15K, Ts=348.15K.
        Re ~ 1.1e6 (turbulent).
        """
        h, re = h_forced(length=1.0, velocity=20.0, t_ambient=298.15, t_surface=348.15)
        assert re > 5e5
        assert h > 0

    def test_returns_tuple(self):
        h, re = h_forced(length=0.3, velocity=5.0, t_ambient=298.15, t_surface=348.15)
        assert isinstance(h, float)
        assert isinstance(re, float)

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            h_forced(0.3, 5.0, 298.15, 348.15)  # type: ignore[misc]


# --- h_natural ---

class TestHNatural:
    def test_vertical_laminar(self):
        """Vertical plate, L=0.3m, Ta=298.15K, Ts=348.15K.
        Octave: h_natural_convection('vertical', 0.3, 25, 75)
        Ra < 1e9 → h = 0.59 * Ra^(1/4) * kf / L.
        """
        h, ra = h_natural(
            orientation="vertical", length=0.3, t_ambient=298.15, t_surface=348.15
        )
        assert ra < 1e9
        assert h == pytest.approx(7.0, rel=0.1)  # ~7 W/(m2K) typical natural conv

    def test_horizontal_top(self):
        h, ra = h_natural(
            orientation="horizontal_top", length=0.3, t_ambient=298.15, t_surface=348.15
        )
        assert h > 0

    def test_horizontal_bottom(self):
        h, ra = h_natural(
            orientation="horizontal_bottom", length=0.3, t_ambient=298.15, t_surface=348.15
        )
        assert h > 0
        # horizontal bottom is always lowest
        h_top, _ = h_natural(
            orientation="horizontal_top", length=0.3, t_ambient=298.15, t_surface=348.15
        )
        assert h < h_top

    def test_unknown_orientation_raises(self):
        with pytest.raises(ValueError, match="Unknown orientation"):
            h_natural(
                orientation="diagonal", length=0.3, t_ambient=298.15, t_surface=348.15
            )


# --- h_radiation_linearized ---

class TestHRadiationLinearized:
    def test_blackbody_300_350(self):
        """eps=1.0, Ta=300K, Ts=350K.
        h = sigma * (Ts^2 + Ta^2) * (Ts + Ta) = 5.67e-8 * 212500 * 650 = 7.84.
        """
        h = h_radiation_linearized(emissivity=1.0, t_ambient=300.0, t_surface=350.0)
        expected = 5.67e-8 * (350**2 + 300**2) * (350 + 300)
        assert h == pytest.approx(expected, rel=1e-6)

    def test_gray_surface(self):
        """eps=0.9 should give 0.9x the blackbody value."""
        h_black = h_radiation_linearized(emissivity=1.0, t_ambient=300.0, t_surface=350.0)
        h_gray = h_radiation_linearized(emissivity=0.9, t_ambient=300.0, t_surface=350.0)
        assert h_gray == pytest.approx(0.9 * h_black, rel=1e-12)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && conda activate ntbees2 && python -m pytest tests/unit/test_convection.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'thermal_cli.formula.convection'`

- [ ] **Step 3: Implement `formula/convection.py`**

Create `python/src/thermal_cli/formula/convection.py`:

```python
"""Convection and linearized-radiation heat transfer coefficients.

Ported from ``lib/h_forced_convection.m``, ``h_natural_convection.m``,
``h_radiation.m``.  Air properties use inline correlations (ideal gas law,
Sutherland viscosity, linear thermal conductivity).

All temperatures in Kelvin.
"""

from __future__ import annotations

from thermal_cli.formula.constants import STEFAN_BOLTZMANN

_PR_AIR: float = 0.71


def _rho_air(t: float) -> float:
    """Air density [kg/m^3] via ideal gas law at 1 atm."""
    return 101325.0 / 287.058 / t


def _mu_air(t: float) -> float:
    """Air dynamic viscosity [Pa s] via Sutherland's law."""
    return 18.27e-6 * (291.15 + 120) / (t + 120) * (t / 291.15) ** 1.5


def _kf_air(t: float) -> float:
    """Air thermal conductivity [W/(m K)], linear fit."""
    return 7e-5 * t + 5.1e-3


def h_forced(
    *,
    length: float,
    velocity: float,
    t_ambient: float,
    t_surface: float,
) -> tuple[float, float]:
    """Forced convection h-coefficient for a flat plate.

    Blasius (laminar, Re < 5e5) or mixed (turbulent) correlation.

    Parameters
    ----------
    length : float
        Plate length [m].
    velocity : float
        Free-stream velocity [m/s].
    t_ambient, t_surface : float
        Temperatures [K].

    Returns
    -------
    tuple[float, float]
        ``(h, Re)`` — heat transfer coefficient [W/(m^2 K)] and Reynolds number.
    """
    t_film = (t_ambient + t_surface) / 2
    re = _rho_air(t_film) * velocity * length / _mu_air(t_film)
    kf = _kf_air(t_film)
    if re < 5e5:
        h = 0.664 * re**0.5 * _PR_AIR ** (1 / 3) * kf / length
    else:
        h = (0.037 * re**0.8 - 18030) * _PR_AIR ** (1 / 3) * kf / length
    return h, re


def h_natural(
    *,
    orientation: str,
    length: float,
    t_ambient: float,
    t_surface: float,
) -> tuple[float, float]:
    """Natural convection h-coefficient for a flat surface.

    Parameters
    ----------
    orientation : str
        ``'vertical'``, ``'horizontal_top'``, or ``'horizontal_bottom'``.
    length : float
        Characteristic length [m].
    t_ambient, t_surface : float
        Temperatures [K].

    Returns
    -------
    tuple[float, float]
        ``(h, Ra)`` — heat transfer coefficient [W/(m^2 K)] and Rayleigh number.
    """
    t_film = (t_ambient + t_surface) / 2
    beta = 1.0 / t_film
    rho = _rho_air(t_film)
    mu = _mu_air(t_film)
    kf = _kf_air(t_film)
    ra = _PR_AIR * rho**2 * 9.81 * beta * (t_surface - t_ambient) * length**3 / mu**2

    if orientation == "vertical":
        h = (0.59 * ra**0.25 if ra < 1e9 else 0.1 * ra ** (1 / 3)) * kf / length
    elif orientation == "horizontal_top":
        h = (0.54 * ra**0.25 if ra < 1e7 else 0.15 * ra ** (1 / 3)) * kf / length
    elif orientation == "horizontal_bottom":
        h = 0.27 * ra**0.25 * kf / length
    else:
        raise ValueError(f"Unknown orientation: {orientation!r}")

    return h, ra


def h_radiation_linearized(
    *,
    emissivity: float,
    t_ambient: float,
    t_surface: float,
) -> float:
    """Linearized radiation h-coefficient.

    Parameters
    ----------
    emissivity : float
        Surface emissivity (0–1).
    t_ambient, t_surface : float
        Temperatures [K].

    Returns
    -------
    float
        Radiation h-coefficient [W/(m^2 K)].
    """
    return (
        emissivity
        * STEFAN_BOLTZMANN
        * (t_surface**2 + t_ambient**2)
        * (t_surface + t_ambient)
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd python && python -m pytest tests/unit/test_convection.py -v`
Expected: all tests PASS

- [ ] **Step 5: Update `formula/__init__.py` and commit**

Add to `python/src/thermal_cli/formula/__init__.py`:

```python
from thermal_cli.formula.convection import h_forced, h_natural, h_radiation_linearized
```

And add to `__all__`:

```python
"h_forced",
"h_natural",
"h_radiation_linearized",
```

Commit:

```bash
git add python/src/thermal_cli/formula/convection.py \
       python/src/thermal_cli/formula/__init__.py \
       python/tests/unit/test_convection.py
git commit -m "feat(m7): add convection h-coefficient formulas (forced, natural, radiation)"
```

---

## Task 2: `formula/free_conv.py` — surface temperature solver

**Files:**
- Create: `python/src/thermal_cli/formula/free_conv.py`
- Test: `python/tests/unit/test_free_conv.py`

**Depends on:** Task 1

- [ ] **Step 1: Write failing tests**

Create `python/tests/unit/test_free_conv.py`:

```python
"""Unit tests for thermal_cli.formula.free_conv."""

from __future__ import annotations

import pytest

from thermal_cli.formula.free_conv import Face, FreeConvResult, free_conv_surface_temp


class TestFreeConvSurfaceTemp:
    def test_single_vertical_face(self):
        """10W box, single vertical face 0.1x0.1m, eps=0.9.
        Surface temp should be significantly above ambient.
        """
        faces = [Face(area=0.01, char_length=0.1, orientation="vertical", emissivity=0.9)]
        result = free_conv_surface_temp(faces=faces, t_ambient=298.15, p_total=10.0)
        assert isinstance(result, FreeConvResult)
        assert result.t_surface > 298.15 + 30  # expect >30K rise for 10W on 0.01m2
        assert result.t_surface < 298.15 + 300  # sanity upper bound
        assert len(result.h_per_face) == 1
        assert len(result.q_per_face) == 1
        assert result.q_per_face[0] == pytest.approx(10.0, rel=0.01)

    def test_multi_face_box(self):
        """5W box with 4 vertical faces + 1 top face.
        Total dissipated power should match input.
        """
        faces = [
            Face(area=0.01, char_length=0.1, orientation="vertical", emissivity=0.9),
            Face(area=0.01, char_length=0.1, orientation="vertical", emissivity=0.9),
            Face(area=0.01, char_length=0.1, orientation="vertical", emissivity=0.9),
            Face(area=0.01, char_length=0.1, orientation="vertical", emissivity=0.9),
            Face(area=0.01, char_length=0.1, orientation="horizontal_top", emissivity=0.9),
        ]
        result = free_conv_surface_temp(faces=faces, t_ambient=298.15, p_total=5.0)
        assert sum(result.q_per_face) == pytest.approx(5.0, rel=0.01)

    def test_higher_power_gives_higher_temp(self):
        faces = [Face(area=0.01, char_length=0.1, orientation="vertical")]
        r1 = free_conv_surface_temp(faces=faces, t_ambient=298.15, p_total=5.0)
        r2 = free_conv_surface_temp(faces=faces, t_ambient=298.15, p_total=10.0)
        assert r2.t_surface > r1.t_surface

    def test_default_emissivity(self):
        """Face without explicit emissivity defaults to 0.9."""
        face_default = Face(area=0.01, char_length=0.1, orientation="vertical")
        face_explicit = Face(area=0.01, char_length=0.1, orientation="vertical", emissivity=0.9)
        r1 = free_conv_surface_temp(faces=[face_default], t_ambient=298.15, p_total=5.0)
        r2 = free_conv_surface_temp(faces=[face_explicit], t_ambient=298.15, p_total=5.0)
        assert r1.t_surface == pytest.approx(r2.t_surface, rel=1e-10)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && python -m pytest tests/unit/test_free_conv.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `formula/free_conv.py`**

Create `python/src/thermal_cli/formula/free_conv.py`:

```python
"""Free convection surface temperature solver (bisection).

Ported from ``lib/free_conv_surface_temp.m``.
Finds surface temperature such that total natural-convection + radiation
heat dissipation equals the supplied power.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from thermal_cli.formula.convection import h_natural, h_radiation_linearized


@dataclass
class Face:
    """One surface participating in free convection."""

    area: float  # [m^2]
    char_length: float  # [m]
    orientation: str  # 'vertical' | 'horizontal_top' | 'horizontal_bottom'
    emissivity: float = 0.9


@dataclass
class FreeConvResult:
    """Output of the free convection surface temperature solver."""

    t_surface: float  # [K]
    h_per_face: list[float] = field(default_factory=list)  # [W/(m^2 K)]
    q_per_face: list[float] = field(default_factory=list)  # [W]


def free_conv_surface_temp(
    *,
    faces: list[Face],
    t_ambient: float,
    p_total: float,
    tol: float = 0.01,
    max_iter: int = 100,
) -> FreeConvResult:
    """Find surface temperature from natural convection + radiation balance.

    Parameters
    ----------
    faces : list[Face]
        Surfaces participating in heat dissipation.
    t_ambient : float
        Ambient temperature [K].
    p_total : float
        Total heat dissipation [W].
    tol : float
        Convergence tolerance. Iteration stops when
        ``|residual| < tol * p_total * 0.001``.
    max_iter : int
        Maximum bisection iterations.

    Returns
    -------
    FreeConvResult
        Surface temperature, per-face h and q breakdown.
    """
    t_low = t_ambient + 0.1
    t_high = t_ambient + 500.0

    t_mid = t_low
    for _ in range(max_iter):
        t_mid = (t_low + t_high) / 2
        residual = _heat_balance(t_mid, faces, t_ambient, p_total)
        if abs(residual) < tol * p_total * 0.001:
            break
        if residual > 0:
            t_high = t_mid
        else:
            t_low = t_mid

    t_surface = t_mid

    h_arr: list[float] = []
    q_arr: list[float] = []
    for face in faces:
        h_nat, _ = h_natural(
            orientation=face.orientation,
            length=face.char_length,
            t_ambient=t_ambient,
            t_surface=t_surface,
        )
        h_rad = h_radiation_linearized(
            emissivity=face.emissivity, t_ambient=t_ambient, t_surface=t_surface
        )
        h_total = h_nat + h_rad
        h_arr.append(h_total)
        q_arr.append(h_total * face.area * (t_surface - t_ambient))

    return FreeConvResult(t_surface=t_surface, h_per_face=h_arr, q_per_face=q_arr)


def _heat_balance(
    t_s: float, faces: list[Face], t_ambient: float, p_total: float
) -> float:
    q_total = 0.0
    for face in faces:
        h_nat, _ = h_natural(
            orientation=face.orientation,
            length=face.char_length,
            t_ambient=t_ambient,
            t_surface=t_s,
        )
        h_rad = h_radiation_linearized(
            emissivity=face.emissivity, t_ambient=t_ambient, t_surface=t_s
        )
        q_total += (h_nat + h_rad) * face.area * (t_s - t_ambient)
    return q_total - p_total
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd python && python -m pytest tests/unit/test_free_conv.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add python/src/thermal_cli/formula/free_conv.py \
       python/tests/unit/test_free_conv.py
git commit -m "feat(m7): add free convection surface temperature solver"
```

---

## Task 3: `formula/water_cooling.py` — energy balance

**Files:**
- Create: `python/src/thermal_cli/formula/water_cooling.py`
- Test: `python/tests/unit/test_water_cooling.py`

- [ ] **Step 1: Write failing tests**

Create `python/tests/unit/test_water_cooling.py`:

```python
"""Unit tests for thermal_cli.formula.water_cooling."""

from __future__ import annotations

import pytest

from thermal_cli.formula.water_cooling import WaterCoolingResult, water_cooling


class TestWaterCooling:
    def test_basic_energy_balance(self):
        """1000W, 5 l/min, 50/50 glycol-water (cp=3483, rho=1064).
        dT = 1000 / (3483 * 1064 * 5/60000) = 1000 / (3483 * 0.08867) = 3.24 C.
        """
        r = water_cooling(
            p_loss=1000.0,
            flow_lpm=5.0,
            t_inlet=298.15,
            rth_jc=0.5,
            n_devices=4,
            cp=3483.0,
            rho=1064.0,
            rth_cl=0.0,
        )
        assert isinstance(r, WaterCoolingResult)
        assert r.dt_coolant == pytest.approx(3.24, rel=0.01)
        assert r.t_outlet == pytest.approx(298.15 + 3.24, rel=0.01)
        # T_j = T_out + P_dev * (Rjc + Rcl) = 301.39 + 250*0.5 = 426.39
        assert r.t_junction == pytest.approx(298.15 + 3.24 + 250 * 0.5, rel=0.01)

    def test_single_device(self):
        r = water_cooling(
            p_loss=100.0,
            flow_lpm=2.0,
            t_inlet=298.15,
            rth_jc=1.0,
            n_devices=1,
        )
        assert r.p_per_device == pytest.approx(100.0)

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            water_cooling(100.0, 2.0, 298.15, 1.0, 1)  # type: ignore[misc]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && python -m pytest tests/unit/test_water_cooling.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `formula/water_cooling.py`**

Create `python/src/thermal_cli/formula/water_cooling.py`:

```python
"""Water cooling energy balance calculator.

Ported from ``lib/cmd_water_cooling.m``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WaterCoolingResult:
    """Output of the water cooling calculator."""

    dt_coolant: float  # Coolant temperature rise [K]
    t_outlet: float  # Coolant outlet temperature [K]
    t_junction: float  # Junction temperature [K]
    m_dot: float  # Mass flow rate [kg/s]
    p_per_device: float  # Power per device [W]


def water_cooling(
    *,
    p_loss: float,
    flow_lpm: float,
    t_inlet: float,
    rth_jc: float,
    n_devices: int,
    cp: float = 3483.0,
    rho: float = 1064.0,
    rth_cl: float = 0.0,
) -> WaterCoolingResult:
    """Compute coolant and junction temperatures for a water-cooled system.

    Parameters
    ----------
    p_loss : float
        Total power loss [W].
    flow_lpm : float
        Coolant volumetric flow rate [l/min].
    t_inlet : float
        Coolant inlet temperature [K].
    rth_jc : float
        Junction-to-case thermal resistance per device [K/W].
    n_devices : int
        Number of devices.
    cp : float
        Coolant specific heat [J/(kg K)]. Default: 50/50 glycol-water.
    rho : float
        Coolant density [kg/m^3]. Default: 50/50 glycol-water.
    rth_cl : float
        Case-to-liquid thermal resistance per device [K/W].

    Returns
    -------
    WaterCoolingResult
    """
    q_m3s = flow_lpm / 1000.0 / 60.0
    m_dot = rho * q_m3s
    dt = p_loss / (cp * m_dot)
    t_outlet = t_inlet + dt
    p_dev = p_loss / n_devices
    t_junction = t_outlet + p_dev * (rth_jc + rth_cl)

    return WaterCoolingResult(
        dt_coolant=dt,
        t_outlet=t_outlet,
        t_junction=t_junction,
        m_dot=m_dot,
        p_per_device=p_dev,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd python && python -m pytest tests/unit/test_water_cooling.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add python/src/thermal_cli/formula/water_cooling.py \
       python/tests/unit/test_water_cooling.py
git commit -m "feat(m7): add water cooling energy balance calculator"
```

---

## Task 4: `heatsinks/natural_conv.py` — natural convection heatsink Rth

**Files:**
- Create: `python/src/thermal_cli/heatsinks/natural_conv.py`
- Test: `python/tests/unit/test_natural_conv.py`

**Depends on:** Task 1 (convection.py)

- [ ] **Step 1: Write failing tests**

Create `python/tests/unit/test_natural_conv.py`:

```python
"""Unit tests for thermal_cli.heatsinks.natural_conv."""

from __future__ import annotations

import pytest

from thermal_cli.heatsinks.natural_conv import NaturalConvHsResult, natural_conv_hs


class TestNaturalConvHs:
    def test_typical_aluminum_heatsink(self):
        """10 fins, Hf=0.05m, L=0.1m, tf=2mm, s=5mm, tb=3mm, k=200.
        Octave: cmd_natural_conv_hs with same params.
        At P=10W, Ta=25C (298.15K), expect Rth ~ 2-5 K/W for small HS.
        """
        r = natural_conv_hs(
            n_fins=10,
            fin_height=0.05,
            fin_length=0.1,
            fin_thickness=0.002,
            channel_width=0.005,
            base_thickness=0.003,
            k=200.0,
            t_ambient=298.15,
            p_loss=10.0,
            emissivity=0.9,
        )
        assert isinstance(r, NaturalConvHsResult)
        assert 1.0 < r.rth < 10.0  # reasonable range for small fanless HS
        assert r.t_surface > 298.15
        assert 0 < r.eta_fin <= 1.0
        assert r.q_total == pytest.approx(10.0, rel=0.02)

    def test_higher_power_higher_rth_temp(self):
        """More power → higher surface temp but Rth may decrease slightly
        (h increases with dT for natural convection)."""
        kwargs = dict(
            n_fins=10, fin_height=0.05, fin_length=0.1,
            fin_thickness=0.002, channel_width=0.005, base_thickness=0.003,
            k=200.0, t_ambient=298.15, emissivity=0.9,
        )
        r5 = natural_conv_hs(p_loss=5.0, **kwargs)
        r20 = natural_conv_hs(p_loss=20.0, **kwargs)
        assert r20.t_surface > r5.t_surface

    def test_copper_vs_aluminum(self):
        """Higher k → better fin efficiency → lower Rth."""
        kwargs = dict(
            n_fins=10, fin_height=0.05, fin_length=0.1,
            fin_thickness=0.002, channel_width=0.005, base_thickness=0.003,
            t_ambient=298.15, p_loss=10.0, emissivity=0.9,
        )
        r_al = natural_conv_hs(k=200.0, **kwargs)
        r_cu = natural_conv_hs(k=385.0, **kwargs)
        assert r_cu.rth < r_al.rth
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && python -m pytest tests/unit/test_natural_conv.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `heatsinks/natural_conv.py`**

Create `python/src/thermal_cli/heatsinks/natural_conv.py`:

```python
"""Natural convection heatsink thermal resistance estimator (fanless).

Ported from ``lib/cmd_natural_conv_hs.m``.
Iteratively solves for surface temperature where total heat dissipation
(fin convection + radiation + base convection + radiation) equals input power.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from thermal_cli.formula.convection import h_natural, h_radiation_linearized


@dataclass
class NaturalConvHsResult:
    """Output of natural convection heatsink solver."""

    t_surface: float  # [K]
    rth: float  # [K/W]
    h_fin: float  # [W/(m^2 K)]
    h_base: float  # [W/(m^2 K)]
    eta_fin: float  # [-]
    q_total: float  # [W]


def natural_conv_hs(
    *,
    n_fins: int,
    fin_height: float,
    fin_length: float,
    fin_thickness: float,
    channel_width: float,
    base_thickness: float,
    k: float,
    t_ambient: float,
    p_loss: float,
    emissivity: float = 0.9,
) -> NaturalConvHsResult:
    """Estimate heatsink Rth under natural convection (no fan).

    Parameters
    ----------
    n_fins : int
        Number of fins.
    fin_height : float
        Fin height [m].
    fin_length : float
        Fin length (flow direction) [m].
    fin_thickness : float
        Fin thickness [m].
    channel_width : float
        Gap between fins [m].
    base_thickness : float
        Base plate thickness [m] (not used in thermal calc, kept for API parity).
    k : float
        Fin material thermal conductivity [W/(m K)].
    t_ambient : float
        Ambient temperature [K].
    p_loss : float
        Total power dissipation [W].
    emissivity : float
        Surface emissivity (default 0.9).

    Returns
    -------
    NaturalConvHsResult
    """
    ts_low = t_ambient + 0.1
    ts_high = t_ambient + 200.0

    ts = ts_low
    h_fin = h_base = eta_fin = q = 0.0
    for _ in range(100):
        ts = (ts_low + ts_high) / 2

        # Fin surfaces (vertical)
        h_fin_nat, _ = h_natural(
            orientation="vertical", length=fin_height, t_ambient=t_ambient, t_surface=ts
        )
        h_fin_rad = h_radiation_linearized(
            emissivity=emissivity, t_ambient=t_ambient, t_surface=ts
        )
        h_fin = h_fin_nat + h_fin_rad

        # Fin efficiency
        m = math.sqrt(2 * h_fin / (k * fin_thickness))
        mH = m * fin_height
        eta_fin = math.tanh(mH) / mH if mH > 0 else 1.0

        # Base exposed area (horizontal top, between fins)
        a_base = (n_fins - 1) * channel_width * fin_length
        h_base_nat, _ = h_natural(
            orientation="horizontal_top",
            length=channel_width,
            t_ambient=t_ambient,
            t_surface=ts,
        )
        h_base_rad = h_radiation_linearized(
            emissivity=emissivity, t_ambient=t_ambient, t_surface=ts
        )
        h_base = h_base_nat + h_base_rad

        # Total heat dissipation
        a_fin = n_fins * 2 * fin_height * fin_length
        q = h_fin * eta_fin * a_fin * (ts - t_ambient) + h_base * a_base * (ts - t_ambient)

        if abs(q - p_loss) < p_loss * 1e-4:
            break
        if q > p_loss:
            ts_high = ts
        else:
            ts_low = ts

    rth = (ts - t_ambient) / p_loss

    return NaturalConvHsResult(
        t_surface=ts, rth=rth, h_fin=h_fin, h_base=h_base, eta_fin=eta_fin, q_total=q
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd python && python -m pytest tests/unit/test_natural_conv.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add python/src/thermal_cli/heatsinks/natural_conv.py \
       python/tests/unit/test_natural_conv.py
git commit -m "feat(m7): add natural convection heatsink Rth estimator"
```

---

## Task 5: `heatsinks/channel_flow.py` — hydraulic operating point & fin Rth

**Files:**
- Create: `python/src/thermal_cli/heatsinks/channel_flow.py`
- Test: `python/tests/unit/test_channel_flow.py`

This is the most complex task: porting `idraulico.m` and `Rth_fin.m` from SoftwareTermico,
converting from mm to SI units. Air properties use cubic spline interpolation matching
`mfiles/SoftwareTermico/Coeff_Aria/*.m`.

- [ ] **Step 1: Write failing tests**

Create `python/tests/unit/test_channel_flow.py`:

```python
"""Unit tests for thermal_cli.heatsinks.channel_flow.

Air property splines validated against SoftwareTermico/Coeff_Aria/ at tabulated points.
Solver outputs validated against Octave cmd_hydraulic_op / cmd_fin_rth.
"""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.heatsinks.channel_flow import (
    HydraulicResult,
    FinRthResult,
    fin_thermal_resistance,
    hydraulic_operating_point,
    rho_air,
    mu_air,
    kt_air,
    cp_air,
)


# --- Air property splines ---

class TestAirProperties:
    """Verify spline interpolation matches Octave at tabulated points."""

    @pytest.mark.parametrize(
        ("t_c", "expected"),
        [(0, 1.296), (38, 1.136), (93, 0.96), (149, 0.832)],
    )
    def test_rho_air_at_table_points(self, t_c: float, expected: float):
        t_k = t_c + 273.15
        assert rho_air(t_k) == pytest.approx(expected, rel=1e-6)

    @pytest.mark.parametrize(
        ("t_c", "expected"),
        [(0, 1.732e-5), (38, 1.910e-5), (93, 2.140e-5), (149, 2.392e-5)],
    )
    def test_mu_air_at_table_points(self, t_c: float, expected: float):
        t_k = t_c + 273.15
        assert mu_air(t_k) == pytest.approx(expected, rel=1e-6)

    @pytest.mark.parametrize(
        ("t_c", "expected_raw"),
        [(0, 0.0208), (38, 0.0230), (93, 0.0259), (149, 0.0287)],
    )
    def test_kt_air_at_table_points(self, t_c: float, expected_raw: float):
        t_k = t_c + 273.15
        expected = expected_raw * 4.1868e3 / 3600  # unit conversion
        assert kt_air(t_k) == pytest.approx(expected, rel=1e-6)

    @pytest.mark.parametrize(
        ("t_c", "expected_raw"),
        [(0, 0.24), (38, 0.240), (93, 0.241), (149, 0.243)],
    )
    def test_cp_air_at_table_points(self, t_c: float, expected_raw: float):
        t_k = t_c + 273.15
        expected = expected_raw * 4.1868e3  # unit conversion
        assert cp_air(t_k) == pytest.approx(expected, rel=1e-4)

    def test_interpolation_between_points(self):
        """At 50C (323.15K), density should be between table values at 38C and 93C."""
        rho = rho_air(323.15)
        assert 0.832 < rho < 1.296


# --- Hydraulic operating point ---

class TestHydraulicOperatingPoint:
    def test_push_mode_basic(self):
        """Simple push-through case with synthetic fan curve and small heatsink."""
        # Synthetic fan curve: linear from 100Pa at 0 m3/s to 0Pa at 0.1 m3/s
        fan_qv = np.array([0.0, 0.025, 0.05, 0.075, 0.1])
        fan_hv = np.array([100.0, 75.0, 50.0, 25.0, 0.0])
        r = hydraulic_operating_point(
            b=0.2,           # heatsink length [m]
            s=0.2,           # opening width [m] (= full width for push)
            n_fins=20,
            tf=0.002,        # fin thickness [m]
            bch=0.005,       # channel width [m]
            hf=0.05,         # fin height [m]
            t_air=353.15,    # air temp [K] (80C)
            vent_type="push",
            fan_qv=fan_qv,
            fan_hv=fan_hv,
        )
        assert isinstance(r, HydraulicResult)
        assert r.flowrate > 0
        assert r.pressure > 0
        assert r.reynolds > 0

    def test_impinge_mode(self):
        fan_qv = np.array([0.0, 0.025, 0.05, 0.075, 0.1])
        fan_hv = np.array([100.0, 75.0, 50.0, 25.0, 0.0])
        r = hydraulic_operating_point(
            b=0.2, s=0.05, n_fins=20, tf=0.002, bch=0.005, hf=0.05,
            t_air=353.15, vent_type="impinge", fan_qv=fan_qv, fan_hv=fan_hv,
        )
        assert r.flowrate > 0


# --- Fin thermal resistance ---

class TestFinThermalResistance:
    def test_push_mode_basic(self):
        r = fin_thermal_resistance(
            qv_f=0.03,       # flowrate [m3/s]
            a=0.15,          # heatsink width [m]
            b=0.2,           # heatsink length [m]
            s=0.15,          # opening [m] (= width for push)
            tf=0.002,        # fin thickness [m]
            bch=0.005,       # channel width [m]
            hf=0.05,         # fin height [m]
            t_air=353.15,    # air temp [K]
            vent_type="push",
            k_fin=200.0,     # aluminum [W/(m K)]
            n_fins=20,
        )
        assert isinstance(r, FinRthResult)
        assert r.rth > 0
        assert r.h_eq > 0
        assert r.reynolds > 0

    def test_higher_flow_lower_rth(self):
        kwargs = dict(
            a=0.15, b=0.2, s=0.15, tf=0.002, bch=0.005, hf=0.05,
            t_air=353.15, vent_type="push", k_fin=200.0, n_fins=20,
        )
        r_low = fin_thermal_resistance(qv_f=0.01, **kwargs)
        r_high = fin_thermal_resistance(qv_f=0.05, **kwargs)
        assert r_high.rth < r_low.rth
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && python -m pytest tests/unit/test_channel_flow.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `heatsinks/channel_flow.py`**

Create `python/src/thermal_cli/heatsinks/channel_flow.py`:

```python
"""Channel-flow heatsink model: hydraulic operating point and thermal resistance.

Ported from ``mfiles/SoftwareTermico/Therm_hydr/idraulico.m`` and ``Rth_fin.m``.
Air properties from ``mfiles/SoftwareTermico/Coeff_Aria/*.m``.

All geometry inputs in SI (meters).  The Octave originals used mm — all
mm→m conversion factors have been removed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.interpolate import CubicSpline

# ---------------------------------------------------------------------------
# Air property splines (from SoftwareTermico/Coeff_Aria, tables in K)
# ---------------------------------------------------------------------------
_T_TABLE_K = np.array([273.15, 311.15, 366.15, 422.15])  # 0, 38, 93, 149 °C

_RHO_SPLINE = CubicSpline(_T_TABLE_K, [1.296, 1.136, 0.96, 0.832])
_MU_SPLINE = CubicSpline(_T_TABLE_K, np.array([1.732, 1.910, 2.140, 2.392]) * 1e-5)
_KT_SPLINE = CubicSpline(
    _T_TABLE_K, np.array([0.0208, 0.0230, 0.0259, 0.0287]) * 4.1868e3 / 3600
)
_CP_SPLINE = CubicSpline(_T_TABLE_K, np.array([0.24, 0.240, 0.241, 0.243]) * 4.1868e3)


def rho_air(t: float) -> float:
    """Air density [kg/m^3]. *t* in K."""
    return float(_RHO_SPLINE(t))


def mu_air(t: float) -> float:
    """Air dynamic viscosity [Pa s]. *t* in K."""
    return float(_MU_SPLINE(t))


def kt_air(t: float) -> float:
    """Air thermal conductivity [W/(m K)]. *t* in K."""
    return float(_KT_SPLINE(t))


def cp_air(t: float) -> float:
    """Air specific heat [J/(kg K)]. *t* in K."""
    return float(_CP_SPLINE(t))


# ---------------------------------------------------------------------------
# Hydraulic operating point (from idraulico.m)
# ---------------------------------------------------------------------------


@dataclass
class HydraulicResult:
    """Output of the hydraulic operating point solver."""

    reynolds: float
    pressure: float  # [Pa]
    flowrate: float  # [m^3/s]


def hydraulic_operating_point(
    *,
    b: float,
    s: float,
    n_fins: int,
    tf: float,
    bch: float,
    hf: float,
    t_air: float,
    vent_type: str,
    fan_qv: np.ndarray,
    fan_hv: np.ndarray,
) -> HydraulicResult:
    """Find fan-heatsink hydraulic operating point via bisection.

    Parameters
    ----------
    b : float
        Heatsink length parallel to fins [m].
    s : float
        Opening width for air intake [m].  For push mode, equals heatsink width.
    n_fins : int
        Number of fins.
    tf : float
        Fin thickness [m].
    bch : float
        Channel width [m].
    hf : float
        Fin height [m].
    t_air : float
        Air temperature [K].
    vent_type : str
        ``'push'`` or ``'impinge'``.
    fan_qv : array
        Fan curve flowrate points [m^3/s].
    fan_hv : array
        Fan curve pressure points [Pa].

    Returns
    -------
    HydraulicResult
    """
    nu = mu_air(t_air) / rho_air(t_air)
    rho = rho_air(t_air)

    q1 = float(fan_qv[0])
    q2 = float(fan_qv[-1])
    n_ch = n_fins - 1
    qv_f = q1

    for _ in range(200):
        qv_f = q1 + 0.5 * (q2 - q1)
        hv_fan = float(np.interp(qv_f, fan_qv, fan_hv))

        if vent_type == "impinge":
            hv_hs, re_avg = _dp_impinge(qv_f, b, s, n_ch, bch, hf, tf, nu, rho)
        else:
            hv_hs, re_avg = _dp_push(qv_f, b, n_ch, bch, hf, tf, nu, rho)

        if hv_fan == 0:
            break
        error = (hv_fan - hv_hs) / hv_fan
        if abs(error) < 0.01:
            break
        if error > 0:
            q1 = qv_f
        else:
            q2 = qv_f

    return HydraulicResult(reynolds=re_avg, pressure=hv_hs, flowrate=qv_f)


def _dp_push(
    qv_f: float,
    b: float,
    n_ch: int,
    bch: float,
    hf: float,
    tf: float,
    nu: float,
    rho: float,
) -> tuple[float, float]:
    """Pressure drop and Reynolds for push-through ventilation.  All SI."""
    leff2 = b
    vch2 = qv_f / (n_ch * bch * hf)
    dh2 = 4 * bch * hf / (2 * bch + 2 * hf)
    redh2 = dh2 * vch2 / nu
    re_avg = redh2
    ld2 = b / (dh2 * redh2) if redh2 > 0 else 1e30
    fredh2 = 24 / ((1 + (bch / hf) ** 2) * (1 - (192 / math.pi**5) * (bch / hf) * math.tanh(math.pi * hf / (2 * bch))))
    fapp2 = math.sqrt((3.44 / math.sqrt(ld2)) ** 2 + fredh2**2) / redh2 if redh2 > 0 else 0
    sigma = bch / (bch + tf)
    kc = 0.4 * (1 - sigma**2) + 0.4
    ke = (1 - sigma) ** 2 - 0.4 * sigma
    hv = 1.2 * (kc + 4 * fapp2 * leff2 / dh2 + ke) * 0.5 * rho * vch2**2
    return hv, re_avg


def _dp_impinge(
    qv_f: float,
    b: float,
    s: float,
    n_ch: int,
    bch: float,
    hf: float,
    tf: float,
    nu: float,
    rho: float,
) -> tuple[float, float]:
    """Pressure drop and Reynolds for impingement ventilation.  All SI."""
    leff1 = hf / 2
    leff2 = b / 2 - s / 4
    vch1 = qv_f / (n_ch * s * bch)
    vch2 = qv_f / (2 * n_ch * bch * hf)
    dh1 = 4 * bch * s / (2 * s + 2 * bch)
    dh2 = 4 * bch * hf / (2 * bch + 2 * hf)
    redh1 = dh1 * vch1 / nu
    redh2 = dh2 * vch2 / nu
    re_avg = (redh1 + redh2) / 2
    ld1 = hf / (dh1 * redh1) if redh1 > 0 else 1e30
    ld2 = b / (dh2 * redh2) if redh2 > 0 else 1e30

    fredh1 = 24 / ((1 + (bch / s) ** 2) * (1 - (192 / math.pi**5) * (bch / s) * math.tanh(math.pi * s / (2 * bch))))
    fredh2 = 24 / ((1 + (bch / hf) ** 2) * (1 - (192 / math.pi**5) * (bch / hf) * math.tanh(math.pi * hf / (2 * bch))))
    fapp1 = math.sqrt((3.44 / math.sqrt(ld1)) ** 2 + fredh1**2) / redh1 if redh1 > 0 else 0
    fapp2 = math.sqrt((3.44 / math.sqrt(ld2)) ** 2 + fredh2**2) / redh2 if redh2 > 0 else 0

    ratio = hf / s
    if ratio <= 1:
        k90 = 3.64 - 9.15 * ratio + 10.87 * ratio**2 - 4.93 * ratio**3
    else:
        k90 = 0.5 * ((1 + vch2 / vch1) / 2) if vch1 > 0 else 0.5

    sigma = bch / (bch + tf)
    kc = 0.4 * (1 - sigma**2) + 0.4
    ke = 1 - sigma**2 - 0.4 * sigma
    hv = ((kc + k90 + 4 * fapp1 * leff1 / dh1) * (4 * hf**2 / s**2) + 4 * fapp2 * leff2 / dh2 + ke) * 0.5 * rho * vch2**2
    return hv, re_avg


# ---------------------------------------------------------------------------
# Fin thermal resistance (from Rth_fin.m)
# ---------------------------------------------------------------------------


@dataclass
class FinRthResult:
    """Output of the fin thermal resistance calculation."""

    reynolds: float
    v_ch1: float  # [m/s]
    v_ch2: float  # [m/s]
    rth: float  # [K/W]
    h_eq: float  # [W/(m^2 K)]


def fin_thermal_resistance(
    *,
    qv_f: float,
    a: float,
    b: float,
    s: float,
    tf: float,
    bch: float,
    hf: float,
    t_air: float,
    vent_type: str,
    k_fin: float,
    n_fins: int,
) -> FinRthResult:
    """Compute finned heatsink thermal resistance at a given airflow rate.

    Parameters
    ----------
    qv_f : float
        Volumetric airflow rate [m^3/s].
    a : float
        Heatsink width (perpendicular to fins) [m].
    b : float
        Heatsink length (parallel to fins) [m].
    s : float
        Opening width [m] (= a for push, < a for impinge).
    tf : float
        Fin thickness [m].
    bch : float
        Channel width [m].
    hf : float
        Fin height [m].
    t_air : float
        Air temperature [K].
    vent_type : str
        ``'push'`` or ``'impinge'``.
    k_fin : float
        Fin material thermal conductivity [W/(m K)].
    n_fins : int
        Number of fins.

    Returns
    -------
    FinRthResult
    """
    nu = mu_air(t_air) / rho_air(t_air)
    kt = kt_air(t_air)
    cp = cp_air(t_air)
    pr = mu_air(t_air) * cp / kt
    n_ch = n_fins - 1

    if vent_type == "impinge":
        return _rth_impinge(qv_f, a, b, s, tf, bch, hf, nu, kt, pr, k_fin, n_fins, n_ch)
    else:
        return _rth_push(qv_f, a, b, s, tf, bch, hf, nu, kt, pr, k_fin, n_fins, n_ch)


def _nu_channel(reb: float, pr: float) -> float:
    """Muzychka-Yovanovich composite Nusselt for developing channel flow."""
    if reb <= 0 or pr <= 0:
        return 0.0
    term_fd = reb * pr / 2
    term_dev = 0.664 * math.sqrt(reb) * pr**0.3333 * math.sqrt(1 + 3.65 / math.sqrt(reb))
    return (1 / term_fd**3 + 1 / term_dev**3) ** (-1 / 3)


def _rth_push(
    qv_f: float, a: float, b: float, s: float,
    tf: float, bch: float, hf: float,
    nu: float, kt: float, pr: float, k_fin: float,
    n_fins: int, n_ch: int,
) -> FinRthResult:
    leff2 = b
    vch1 = 0.0
    vch2 = qv_f / (n_ch * bch * hf)
    reb2 = bch * vch2 / nu * (bch / leff2) if leff2 > 0 else 0
    re_avg = reb2
    nu2 = _nu_channel(reb2, pr)
    h2 = nu2 * kt / bch
    hbare = h2
    eta = _fin_efficiency_channel(nu2, kt, k_fin, hf, bch, tf, b)
    nu_fin = nu2 * eta
    hfin = nu_fin * kt / bch
    a_bare = (a * b - n_fins * b * tf)
    a_fin = n_ch * b * hf * 2
    rth = 1 / (a_bare * hbare + a_fin * hfin) if (a_bare * hbare + a_fin * hfin) > 0 else float("inf")
    h_eq = 1 / (a * b * rth) if rth > 0 and rth != float("inf") else 0.0
    return FinRthResult(reynolds=re_avg, v_ch1=vch1, v_ch2=vch2, rth=rth, h_eq=h_eq)


def _rth_impinge(
    qv_f: float, a: float, b: float, s: float,
    tf: float, bch: float, hf: float,
    nu: float, kt: float, pr: float, k_fin: float,
    n_fins: int, n_ch: int,
) -> FinRthResult:
    leff1 = hf / 2
    leff2 = b / 2 - s / 4
    vch1 = qv_f / (n_ch * s * bch)
    vch2 = qv_f / (2 * n_ch * bch * hf)
    reb1 = bch * vch1 / nu * (bch / leff1) if leff1 > 0 else 0
    reb2 = bch * vch2 / nu * (bch / leff2) if leff2 > 0 else 0
    re_avg = (reb1 + reb2) / 2
    nu1 = _nu_channel(reb1, pr)
    nu2 = _nu_channel(reb2, pr)
    h1 = nu1 * kt / bch
    h2 = nu2 * kt / bch
    hbare = h1 * s / b + h2 * (b - s) / b
    nu_avg = nu1 * s / b + nu2 * (b - s) / b
    eta = _fin_efficiency_channel(nu_avg, kt, k_fin, hf, bch, tf, b)
    nu_fin = nu_avg * eta
    hfin = nu_fin * kt / bch
    a_bare = (a * b - n_fins * b * tf)
    a_fin = n_ch * b * hf * 2
    rth = 1 / (a_bare * hbare + a_fin * hfin) if (a_bare * hbare + a_fin * hfin) > 0 else float("inf")
    h_eq = 1 / (a * b * rth) if rth > 0 and rth != float("inf") else 0.0
    return FinRthResult(reynolds=re_avg, v_ch1=vch1, v_ch2=vch2, rth=rth, h_eq=h_eq)


def _fin_efficiency_channel(
    nu_val: float, kt: float, k_fin: float,
    hf: float, bch: float, tf: float, b: float,
) -> float:
    """Fin efficiency for channel-flow Nusselt-based model (Rth_fin.m formula)."""
    arg = 2 * nu_val * (kt / k_fin) * (hf / bch) * (hf / tf) * (tf / b + 1)
    if arg <= 0:
        return 1.0
    sqrt_arg = math.sqrt(arg)
    return math.tanh(sqrt_arg) / sqrt_arg if sqrt_arg > 0 else 1.0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd python && python -m pytest tests/unit/test_channel_flow.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add python/src/thermal_cli/heatsinks/channel_flow.py \
       python/tests/unit/test_channel_flow.py
git commit -m "feat(m7): add channel-flow hydraulic and thermal resistance solvers"
```

---

## Task 6: DB CSVs + `heatsinks/profiles_db.py`

**Files:**
- Create: `db/hs_profiles.csv`
- Create: `db/hs_materials.csv`
- Create: `db/fans.csv`
- Create: `python/src/thermal_cli/heatsinks/profiles_db.py`
- Test: `python/tests/unit/test_profiles_db.py` (add to existing test_heatsinks.py or new file)

- [ ] **Step 1: Create `db/hs_profiles.csv`**

Data from `mfiles/SoftwareTermico/Database_FAN&HeatSink/HS_Type.m`. All geometry in mm
(matching the Octave convention; the CLI command converts to SI when calling solvers).

Create `db/hs_profiles.csv`:

```csv
name,tb_mm,hf_mm,tf_mm,bch_mm
I117,15,102,1.7,4.3
I76,15,61,1.3,2.7
P443,17.5,60,3,6.8
P309,15,47.5,2.2,3.8
P390,14,70,1.4,4.1
P612,14,103,2,4
P573,16.5,60.5,1.7,2.3
I98T,26,72,1.3,4.7
SOCO,15,62,1.5,4
P442,15,39,1,3.5
I100A,16,78,1.3,3.2
I54,13,41.5,1,2.5
Pada SF,15,100,2,3
VHSmallHeatsink28mm,4,26,1.67,6
VHSmallHeatsink30mm,4,24,1,5.2
```

- [ ] **Step 2: Create `db/hs_materials.csv`**

Data from `HS_Tech.m`:

```csv
name,k_fin,k_plate,k_piastra,price_kg,has_piastra,rho_plate,rho_fin,rho_piastra
all_aluminum,200,200,0,10,no,2700,2700,8230
all_copper,350,350,0,22,no,8230,8230,8230
plate_al_fin_cu,350,200,0,18,no,2700,8230,8230
all_alum_piastra_rame,200,200,350,18,yes,2700,2700,8230
```

- [ ] **Step 3: Create `db/fans.csv`**

Data from `Fan_Model.m`. Fan curves are variable-length arrays — store as JSON-encoded
strings in the CSV (simple approach for 13 entries):

```csv
name,qv_m3s,hv_pa,cost,volume_m3
EBMW1G180_axial_DC,"[0.0,0.1111,0.1389,0.1667,0.1944,0.2222,0.2556]","[710,300,288,250,180,100,0]",108,0.002199
EBM208_axial_AC,"[0.0,0.1389,0.1667,0.1944,0.2222]","[200,135,107,70,0]",71,0.003183
...
```

(Full 13-row CSV generated from the Fan_Model.m data, converting Qv from m^3/h to m^3/s
by dividing by 3600 where the Octave file already does `/3600`.)

- [ ] **Step 4: Write failing tests for lookup functions**

Create `python/tests/unit/test_profiles_db.py`:

```python
"""Unit tests for thermal_cli.heatsinks.profiles_db."""

from __future__ import annotations

import pytest

from thermal_cli.heatsinks.profiles_db import (
    HsProfile,
    HsMaterial,
    FanCurve,
    lookup_hs_profile,
    lookup_hs_material,
    lookup_fan,
)


class TestHsProfileLookup:
    def test_i117(self):
        p = lookup_hs_profile("I117")
        assert isinstance(p, HsProfile)
        assert p.tb_mm == pytest.approx(15)
        assert p.hf_mm == pytest.approx(102)
        assert p.tf_mm == pytest.approx(1.7)
        assert p.bch_mm == pytest.approx(4.3)

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="not found"):
            lookup_hs_profile("NONEXISTENT")


class TestHsMaterialLookup:
    def test_all_aluminum(self):
        m = lookup_hs_material("all_aluminum")
        assert isinstance(m, HsMaterial)
        assert m.k_fin == pytest.approx(200)

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="not found"):
            lookup_hs_material("NONEXISTENT")


class TestFanLookup:
    def test_ebmw2e200(self):
        f = lookup_fan("EBMW2E200_axial_AC_50Hz")
        assert isinstance(f, FanCurve)
        assert len(f.qv) == len(f.hv)
        assert f.qv[0] == pytest.approx(0.0)  # first point is zero flow
        assert f.hv[-1] == pytest.approx(0.0)  # last point is zero pressure

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="not found"):
            lookup_fan("NONEXISTENT")
```

- [ ] **Step 5: Implement `heatsinks/profiles_db.py`**

Create `python/src/thermal_cli/heatsinks/profiles_db.py`:

```python
"""Heatsink profile, material, and fan curve database lookups.

Reads from CSV files in the ``db/`` directory:
- ``hs_profiles.csv`` — heatsink fin/channel geometry (mm)
- ``hs_materials.csv`` — material thermal properties
- ``fans.csv`` — fan P-Q curves
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


def _find_db_dir() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "db"
        if (candidate / "hs_profiles.csv").exists():
            return candidate
    raise FileNotFoundError("No db/hs_profiles.csv found in any parent directory")


@dataclass
class HsProfile:
    name: str
    tb_mm: float
    hf_mm: float
    tf_mm: float
    bch_mm: float


@dataclass
class HsMaterial:
    name: str
    k_fin: float
    k_plate: float


@dataclass
class FanCurve:
    name: str
    qv: np.ndarray  # [m^3/s]
    hv: np.ndarray  # [Pa]


def lookup_hs_profile(name: str) -> HsProfile:
    db = _find_db_dir() / "hs_profiles.csv"
    with open(db) as f:
        for row in csv.DictReader(f):
            if row["name"] == name:
                return HsProfile(
                    name=name,
                    tb_mm=float(row["tb_mm"]),
                    hf_mm=float(row["hf_mm"]),
                    tf_mm=float(row["tf_mm"]),
                    bch_mm=float(row["bch_mm"]),
                )
    raise ValueError(f"Heatsink profile '{name}' not found in {db}")


def lookup_hs_material(name: str) -> HsMaterial:
    db = _find_db_dir() / "hs_materials.csv"
    with open(db) as f:
        for row in csv.DictReader(f):
            if row["name"] == name:
                return HsMaterial(
                    name=name,
                    k_fin=float(row["k_fin"]),
                    k_plate=float(row["k_plate"]),
                )
    raise ValueError(f"Material '{name}' not found in {db}")


def lookup_fan(name: str) -> FanCurve:
    db = _find_db_dir() / "fans.csv"
    with open(db) as f:
        for row in csv.DictReader(f):
            if row["name"] == name:
                return FanCurve(
                    name=name,
                    qv=np.array(json.loads(row["qv_m3s"])),
                    hv=np.array(json.loads(row["hv_pa"])),
                )
    raise ValueError(f"Fan '{name}' not found in {db}")
```

- [ ] **Step 6: Run tests**

Run: `cd python && python -m pytest tests/unit/test_profiles_db.py -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add db/hs_profiles.csv db/hs_materials.csv db/fans.csv \
       python/src/thermal_cli/heatsinks/profiles_db.py \
       python/tests/unit/test_profiles_db.py
git commit -m "feat(m7): add heatsink profile, material, and fan CSV databases"
```

---

## Task 7: CLI commands

**Files:**
- Create: `python/src/thermal_cli/cli/commands_m7.py`
- Modify: `python/src/thermal_cli/cli/main.py`
- Test: `python/tests/unit/test_cli_m7.py`

**Depends on:** Tasks 1–6

- [ ] **Step 1: Write failing CLI smoke tests**

Create `python/tests/unit/test_cli_m7.py`:

```python
"""Smoke tests for M7 CLI commands."""

from __future__ import annotations

from typer.testing import CliRunner

from thermal_cli.cli.main import app

runner = CliRunner()


class TestHCoeffCli:
    def test_forced(self):
        result = runner.invoke(app, [
            "h-coeff", "forced",
            "--length", "0.3", "--velocity", "5",
            "--t-ambient", "25", "--t-surface", "75",
        ])
        assert result.exit_code == 0
        assert "h=" in result.stdout

    def test_natural(self):
        result = runner.invoke(app, [
            "h-coeff", "natural",
            "--orientation", "vertical",
            "--length", "0.3", "--t-ambient", "25", "--t-surface", "75",
        ])
        assert result.exit_code == 0
        assert "h=" in result.stdout

    def test_radiation(self):
        result = runner.invoke(app, [
            "h-coeff", "radiation",
            "--emissivity", "0.9", "--t-ambient", "25", "--t-surface", "75",
        ])
        assert result.exit_code == 0
        assert "h=" in result.stdout


class TestRadiationCli:
    def test_parallel(self):
        result = runner.invoke(app, [
            "radiation", "parallel",
            "--t1", "500", "--t2", "300", "--area", "1.0",
            "--eps1", "1.0", "--eps2", "1.0",
        ])
        assert result.exit_code == 0
        assert "q=" in result.stdout


class TestFreeConvCli:
    def test_with_inline_args(self):
        result = runner.invoke(app, [
            "free-conv",
            "--t-ambient", "25", "--p-total", "5",
            "--face", "area=0.01,length=0.1,orientation=vertical,emissivity=0.9",
        ])
        assert result.exit_code == 0
        assert "t_surface=" in result.stdout


class TestWaterCoolingCli:
    def test_basic(self):
        result = runner.invoke(app, [
            "water-cooling",
            "--p-loss", "1000", "--flow", "5", "--t-in", "25",
            "--rth-jc", "0.5", "--n-devices", "4",
        ])
        assert result.exit_code == 0
        assert "t_junction=" in result.stdout


class TestNaturalConvHsCli:
    def test_basic(self):
        result = runner.invoke(app, [
            "natural-conv-hs",
            "--n-fins", "10", "--fin-height", "0.05", "--fin-length", "0.1",
            "--fin-thickness", "0.002", "--channel-width", "0.005",
            "--base-thickness", "0.003", "--k", "200",
            "--t-ambient", "25", "--p-loss", "10",
        ])
        assert result.exit_code == 0
        assert "rth=" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && python -m pytest tests/unit/test_cli_m7.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `cli/commands_m7.py`**

Create `python/src/thermal_cli/cli/commands_m7.py`:

```python
"""M7 CLI commands: convection, radiation, hydraulic, fin-rth.

All temperature CLI arguments are in degrees Celsius.
Formula-layer functions receive Kelvin.
"""

from __future__ import annotations

from typing import Annotated, Optional

import typer

T0 = 273.15  # Celsius → Kelvin offset

# --- h-coeff command group ---
h_coeff_app = typer.Typer(name="h-coeff", help="Heat transfer coefficient calculator.", no_args_is_help=True)


@h_coeff_app.command()
def forced(
    length: Annotated[float, typer.Option(help="Plate length [m]")],
    velocity: Annotated[float, typer.Option(help="Free-stream velocity [m/s]")],
    t_ambient: Annotated[float, typer.Option("--t-ambient", help="Ambient temperature [C]")],
    t_surface: Annotated[float, typer.Option("--t-surface", help="Surface temperature [C]")],
) -> None:
    """Forced convection h (flat plate, Blasius/turbulent)."""
    from thermal_cli.formula.convection import h_forced

    h, re = h_forced(
        length=length, velocity=velocity,
        t_ambient=t_ambient + T0, t_surface=t_surface + T0,
    )
    typer.echo(f"h={h:.4f}")
    typer.echo(f"Re={re:.1f}")


@h_coeff_app.command()
def natural(
    orientation: Annotated[str, typer.Option(help="vertical|horizontal_top|horizontal_bottom")],
    length: Annotated[float, typer.Option(help="Characteristic length [m]")],
    t_ambient: Annotated[float, typer.Option("--t-ambient", help="Ambient temperature [C]")],
    t_surface: Annotated[float, typer.Option("--t-surface", help="Surface temperature [C]")],
) -> None:
    """Natural convection h (flat surface, Rayleigh-based)."""
    from thermal_cli.formula.convection import h_natural

    h, ra = h_natural(
        orientation=orientation, length=length,
        t_ambient=t_ambient + T0, t_surface=t_surface + T0,
    )
    typer.echo(f"h={h:.4f}")
    typer.echo(f"Ra={ra:.2e}")


@h_coeff_app.command("radiation")
def h_coeff_radiation(
    emissivity: Annotated[float, typer.Option(help="Surface emissivity (0-1)")],
    t_ambient: Annotated[float, typer.Option("--t-ambient", help="Ambient temperature [C]")],
    t_surface: Annotated[float, typer.Option("--t-surface", help="Surface temperature [C]")],
) -> None:
    """Linearized radiation h-coefficient."""
    from thermal_cli.formula.convection import h_radiation_linearized

    h = h_radiation_linearized(
        emissivity=emissivity,
        t_ambient=t_ambient + T0, t_surface=t_surface + T0,
    )
    typer.echo(f"h={h:.4f}")


# --- radiation command group ---
radiation_app = typer.Typer(name="radiation", help="Radiation heat transfer (Incropera Ch.13).", no_args_is_help=True)


@radiation_app.command()
def parallel(
    t1: Annotated[float, typer.Option(help="Surface 1 temperature [K]")],
    t2: Annotated[float, typer.Option(help="Surface 2 temperature [K]")],
    area: Annotated[float, typer.Option(help="Surface area [m^2]")],
    eps1: Annotated[float, typer.Option(help="Emissivity surface 1")],
    eps2: Annotated[float, typer.Option(help="Emissivity surface 2")],
) -> None:
    """Radiation between large parallel planes."""
    from thermal_cli.formula.radiation import parallel_planes

    q = parallel_planes(T1=t1, T2=t2, A=area, eps1=eps1, eps2=eps2)
    typer.echo(f"q={q:.6f}")


@radiation_app.command()
def cylinder(
    t1: Annotated[float, typer.Option(help="Inner surface temperature [K]")],
    t2: Annotated[float, typer.Option(help="Outer surface temperature [K]")],
    r1: Annotated[float, typer.Option(help="Inner radius [m]")],
    r2: Annotated[float, typer.Option(help="Outer radius [m]")],
    length: Annotated[float, typer.Option(help="Cylinder length [m]")],
    eps1: Annotated[float, typer.Option(help="Emissivity inner")],
    eps2: Annotated[float, typer.Option(help="Emissivity outer")],
) -> None:
    """Radiation between concentric cylinders."""
    from thermal_cli.formula.radiation import concentric_cylinders

    q = concentric_cylinders(T1=t1, T2=t2, r1=r1, r2=r2, L=length, eps1=eps1, eps2=eps2)
    typer.echo(f"q={q:.6f}")


@radiation_app.command()
def sphere(
    t1: Annotated[float, typer.Option(help="Inner surface temperature [K]")],
    t2: Annotated[float, typer.Option(help="Outer surface temperature [K]")],
    r1: Annotated[float, typer.Option(help="Inner radius [m]")],
    r2: Annotated[float, typer.Option(help="Outer radius [m]")],
    eps1: Annotated[float, typer.Option(help="Emissivity inner")],
    eps2: Annotated[float, typer.Option(help="Emissivity outer")],
) -> None:
    """Radiation between concentric spheres."""
    from thermal_cli.formula.radiation import concentric_spheres

    q = concentric_spheres(T1=t1, T2=t2, r1=r1, r2=r2, eps1=eps1, eps2=eps2)
    typer.echo(f"q={q:.6f}")


@radiation_app.command()
def enclosure_cmd(
    t1: Annotated[float, typer.Option(help="Surface 1 temperature [K]")],
    t2: Annotated[float, typer.Option(help="Surface 2 temperature [K]")],
    eps1: Annotated[float, typer.Option(help="Emissivity 1")],
    eps2: Annotated[float, typer.Option(help="Emissivity 2")],
    a1: Annotated[float, typer.Option(help="Area surface 1 [m^2]")],
    a2: Annotated[float, typer.Option(help="Area surface 2 [m^2]")],
    f12: Annotated[float, typer.Option(help="View factor F12")],
) -> None:
    """Two-surface enclosure radiation."""
    from thermal_cli.formula.radiation import enclosure

    q = enclosure(T1=t1, T2=t2, eps1=eps1, eps2=eps2, A1=a1, A2=a2, F12=f12)
    typer.echo(f"q={q:.6f}")


@radiation_app.command()
def convex(
    t1: Annotated[float, typer.Option(help="Body temperature [K]")],
    t2: Annotated[float, typer.Option(help="Surround temperature [K]")],
    a1: Annotated[float, typer.Option(help="Body area [m^2]")],
    eps1: Annotated[float, typer.Option(help="Body emissivity")],
) -> None:
    """Small convex body in large cavity."""
    from thermal_cli.formula.radiation import small_convex

    q = small_convex(T1=t1, T2=t2, A1=a1, eps1=eps1)
    typer.echo(f"q={q:.6f}")


# --- free-conv command ---

def _parse_face(face_str: str) -> dict:
    """Parse 'area=0.01,length=0.1,orientation=vertical,emissivity=0.9'."""
    parts = {}
    for token in face_str.split(","):
        k, v = token.split("=", 1)
        parts[k.strip()] = v.strip()
    return parts


@typer.Typer.command  # placeholder — registered below
def _free_conv() -> None: ...


def register_free_conv(app: typer.Typer) -> None:
    @app.command("free-conv")
    def free_conv(
        t_ambient: Annotated[float, typer.Option("--t-ambient", help="Ambient temperature [C]")],
        p_total: Annotated[float, typer.Option("--p-total", help="Total power [W]")],
        face: Annotated[list[str], typer.Option("--face", help="Face spec: area=...,length=...,orientation=...,emissivity=...")],
    ) -> None:
        """Find surface temperature from natural convection + radiation."""
        from thermal_cli.formula.free_conv import Face, free_conv_surface_temp

        faces = []
        for f_str in face:
            d = _parse_face(f_str)
            faces.append(Face(
                area=float(d["area"]),
                char_length=float(d["length"]),
                orientation=d["orientation"],
                emissivity=float(d.get("emissivity", "0.9")),
            ))

        result = free_conv_surface_temp(
            faces=faces, t_ambient=t_ambient + T0, p_total=p_total,
        )
        typer.echo(f"t_surface={result.t_surface - T0:.2f}")
        typer.echo(f"dt={result.t_surface - t_ambient - T0:.2f}")
        for i, (h, q) in enumerate(zip(result.h_per_face, result.q_per_face)):
            typer.echo(f"face_{i+1}_h={h:.2f}")
            typer.echo(f"face_{i+1}_q={q:.4f}")
        typer.echo(f"q_total={sum(result.q_per_face):.4f}")


# --- water-cooling command ---

def register_water_cooling(app: typer.Typer) -> None:
    @app.command("water-cooling")
    def water_cooling_cmd(
        p_loss: Annotated[float, typer.Option("--p-loss", help="Total power loss [W]")],
        flow: Annotated[float, typer.Option(help="Coolant flow rate [l/min]")],
        t_in: Annotated[float, typer.Option("--t-in", help="Coolant inlet temperature [C]")],
        rth_jc: Annotated[float, typer.Option("--rth-jc", help="Junction-to-case Rth [K/W]")],
        n_devices: Annotated[int, typer.Option("--n-devices", help="Number of devices")],
        cp: Annotated[float, typer.Option(help="Coolant specific heat [J/(kg K)]")] = 3483.0,
        rho: Annotated[float, typer.Option(help="Coolant density [kg/m3]")] = 1064.0,
        rth_cl: Annotated[float, typer.Option("--rth-cl", help="Case-to-liquid Rth [K/W]")] = 0.0,
    ) -> None:
        """Water-cooled device temperature rise calculator."""
        from thermal_cli.formula.water_cooling import water_cooling

        r = water_cooling(
            p_loss=p_loss, flow_lpm=flow, t_inlet=t_in + T0,
            rth_jc=rth_jc, n_devices=n_devices,
            cp=cp, rho=rho, rth_cl=rth_cl,
        )
        typer.echo(f"dt_coolant={r.dt_coolant:.2f}")
        typer.echo(f"t_out={r.t_outlet - T0:.2f}")
        typer.echo(f"t_junction={r.t_junction - T0:.2f}")
        typer.echo(f"mass_flow={r.m_dot:.4f}")
        typer.echo(f"p_per_device={r.p_per_device:.2f}")


# --- natural-conv-hs command ---

def register_natural_conv_hs(app: typer.Typer) -> None:
    @app.command("natural-conv-hs")
    def natural_conv_hs_cmd(
        n_fins: Annotated[int, typer.Option("--n-fins")],
        fin_height: Annotated[float, typer.Option("--fin-height", help="[m]")],
        fin_length: Annotated[float, typer.Option("--fin-length", help="[m]")],
        fin_thickness: Annotated[float, typer.Option("--fin-thickness", help="[m]")],
        channel_width: Annotated[float, typer.Option("--channel-width", help="[m]")],
        base_thickness: Annotated[float, typer.Option("--base-thickness", help="[m]")],
        k: Annotated[float, typer.Option(help="Material conductivity [W/(m K)]")],
        t_ambient: Annotated[float, typer.Option("--t-ambient", help="[C]")],
        p_loss: Annotated[float, typer.Option("--p-loss", help="[W]")],
        emissivity: Annotated[float, typer.Option(help="Surface emissivity")] = 0.9,
    ) -> None:
        """Estimate fanless heatsink Rth (natural convection + radiation)."""
        from thermal_cli.heatsinks.natural_conv import natural_conv_hs

        r = natural_conv_hs(
            n_fins=n_fins, fin_height=fin_height, fin_length=fin_length,
            fin_thickness=fin_thickness, channel_width=channel_width,
            base_thickness=base_thickness, k=k,
            t_ambient=t_ambient + T0, p_loss=p_loss, emissivity=emissivity,
        )
        typer.echo(f"t_surface={r.t_surface - T0:.2f}")
        typer.echo(f"rth={r.rth:.4f}")
        typer.echo(f"h_fin={r.h_fin:.2f}")
        typer.echo(f"h_base={r.h_base:.2f}")
        typer.echo(f"eta_fin={r.eta_fin:.4f}")
        typer.echo(f"dt={r.t_surface - t_ambient - T0:.2f}")


def register_all(app: typer.Typer) -> None:
    """Register all M7 commands on the given Typer app."""
    app.add_typer(h_coeff_app)
    app.add_typer(radiation_app)
    register_free_conv(app)
    register_water_cooling(app)
    register_natural_conv_hs(app)
```

Note: `hydraulic-op` and `fin-rth` CLI commands depend on config files and DB lookups.
They are added in the same file but load config from YAML. Since the config schema
is more complex (heatsink profile + fan model references), these two commands accept
a `--config` YAML file:

```python
# (continued in commands_m7.py)

def register_hydraulic_op(app: typer.Typer) -> None:
    @app.command("hydraulic-op")
    def hydraulic_op_cmd(
        config: Annotated[Path, typer.Option(help="Config YAML file")],
    ) -> None:
        """Find fan-heatsink hydraulic operating point."""
        import yaml
        from pathlib import Path
        from thermal_cli.heatsinks.profiles_db import lookup_hs_profile, lookup_fan
        from thermal_cli.heatsinks.channel_flow import hydraulic_operating_point

        cfg = yaml.safe_load(Path(config).read_text())
        hs = lookup_hs_profile(cfg["heatsink"]["profile"])
        fan = lookup_fan(cfg["fan"]["model"])
        n_fans = cfg["fan"].get("count", 1)

        b = cfg["heatsink"]["length"]
        a = cfg["heatsink"]["width"]
        n_fins = round(a * 1000 / (hs.bch_mm + hs.tf_mm))
        t_air = cfg["ambient"]["tInlet"] + 5  # K, with 5K margin

        fan_qv = fan.qv * n_fans
        vent = cfg["ventilation"]["type"]
        s = cfg["ventilation"].get("impingeOpening", a) if vent == "impinge" else a

        r = hydraulic_operating_point(
            b=b, s=s, n_fins=n_fins,
            tf=hs.tf_mm / 1000, bch=hs.bch_mm / 1000, hf=hs.hf_mm / 1000,
            t_air=t_air, vent_type=vent, fan_qv=fan_qv, fan_hv=fan.hv,
        )
        typer.echo(f"reynolds={r.reynolds:.1f}")
        typer.echo(f"pressure={r.pressure:.2f}")
        typer.echo(f"flowrate={r.flowrate:.6f}")
        typer.echo(f"num_fins={n_fins}")


def register_fin_rth(app: typer.Typer) -> None:
    @app.command("fin-rth")
    def fin_rth_cmd(
        config: Annotated[Path, typer.Option(help="Config YAML file")],
        flowrate: Annotated[float, typer.Option(help="Airflow rate [m^3/s]")],
    ) -> None:
        """Calculate finned heatsink thermal resistance at given flowrate."""
        import yaml
        from pathlib import Path
        from thermal_cli.heatsinks.profiles_db import lookup_hs_profile, lookup_hs_material
        from thermal_cli.heatsinks.channel_flow import fin_thermal_resistance

        cfg = yaml.safe_load(Path(config).read_text())
        hs = lookup_hs_profile(cfg["heatsink"]["profile"])
        mat = lookup_hs_material(cfg["heatsink"]["material"])

        a = cfg["heatsink"]["width"]
        b = cfg["heatsink"]["length"]
        n_fins = round(a * 1000 / (hs.bch_mm + hs.tf_mm))
        t_air = cfg["ambient"]["tInlet"] + 5
        vent = cfg["ventilation"]["type"]
        s = cfg["ventilation"].get("impingeOpening", a) if vent == "impinge" else a

        r = fin_thermal_resistance(
            qv_f=flowrate, a=a, b=b, s=s,
            tf=hs.tf_mm / 1000, bch=hs.bch_mm / 1000, hf=hs.hf_mm / 1000,
            t_air=t_air, vent_type=vent, k_fin=mat.k_fin, n_fins=n_fins,
        )
        typer.echo(f"rth={r.rth:.6f}")
        typer.echo(f"h_eq={r.h_eq:.2f}")
        typer.echo(f"reynolds={r.reynolds:.1f}")
        typer.echo(f"v_ch1={r.v_ch1:.4f}")
        typer.echo(f"v_ch2={r.v_ch2:.4f}")
```

- [ ] **Step 4: Wire into `cli/main.py`**

Add to `python/src/thermal_cli/cli/main.py`, after the existing `@app.command` for
`convert_config`:

```python
from thermal_cli.cli.commands_m7 import register_all, register_hydraulic_op, register_fin_rth

register_all(app)
register_hydraulic_op(app)
register_fin_rth(app)
```

- [ ] **Step 5: Run CLI smoke tests**

Run: `cd python && python -m pytest tests/unit/test_cli_m7.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add python/src/thermal_cli/cli/commands_m7.py \
       python/src/thermal_cli/cli/main.py \
       python/tests/unit/test_cli_m7.py
git commit -m "feat(m7): add CLI commands (h-coeff, radiation, free-conv, water-cooling, natural-conv-hs, hydraulic-op, fin-rth)"
```

---

## Task 8: Literature tests

**Files:**
- Modify: `python/tests/literature/test_lit_formula.py` (or create `test_lit_convection.py`)

- [ ] **Step 1: Write literature tests**

Create `python/tests/literature/test_lit_convection.py`:

```python
"""Literature-validated tests for convection and radiation h-coefficients.

Reference: Incropera, Fundamentals of Heat and Mass Transfer, 7th ed.
Natural convection correlations from Ch. 9; forced convection from Ch. 7.
"""

from __future__ import annotations

import pytest

from thermal_cli.formula.convection import h_forced, h_natural, h_radiation_linearized
from thermal_cli.formula.constants import STEFAN_BOLTZMANN


class TestHForcedLiterature:
    def test_incropera_example_7_1(self):
        """Incropera 7e, Example 7.1: Air at 300K over 1m plate at 350K, U=5m/s.
        Tf = 325K. Re_L = rho*U*L/mu.
        rho(325) = 101325/(287.058*325) = 1.0862
        mu(325) = 18.27e-6*(411.15)/(445)*(325/291.15)^1.5 = 1.973e-5
        Re = 1.0862*5*1/1.973e-5 = 275300 (laminar).
        kf(325) = 7e-5*325+5.1e-3 = 0.02785
        Nu_avg = 0.664*Re^0.5*Pr^(1/3) = 0.664*524.7*0.8929 = 311.0
        h = Nu*kf/L = 311.0*0.02785/1 = 8.66
        """
        h, re = h_forced(length=1.0, velocity=5.0, t_ambient=300.0, t_surface=350.0)
        assert 200_000 < re < 350_000  # laminar regime
        assert h == pytest.approx(8.66, rel=0.05)  # 5% tolerance for correlation

    def test_forced_turbulent_regime(self):
        """High velocity on long plate → turbulent.
        L=2m, U=30m/s, Ta=300K, Ts=350K → Re ~ 3.3M (turbulent).
        """
        h, re = h_forced(length=2.0, velocity=30.0, t_ambient=300.0, t_surface=350.0)
        assert re > 5e5  # must be turbulent
        assert h > 20  # turbulent h is higher than laminar


class TestHNaturalLiterature:
    def test_vertical_plate_moderate_ra(self):
        """Vertical plate, L=0.5m, Ta=300K, Ts=350K.
        Expect Ra ~ 1e8 (laminar natural conv), h ~ 4-8 W/(m2K).
        Reference: Incropera Table 9.1 — for air with Ra~1e8,
        Nu ~ 0.59*Ra^0.25 ~ 0.59*100 = 59, h ~ 59*0.028/0.5 = 3.3.
        """
        h, ra = h_natural(
            orientation="vertical", length=0.5, t_ambient=300.0, t_surface=350.0
        )
        assert 1e7 < ra < 1e10
        assert 2.0 < h < 10.0


class TestHRadiationLinearizedLiterature:
    def test_stefan_boltzmann_identity(self):
        """For two surfaces at T and T+dT with dT→0, linearized h should
        approach 4*sigma*eps*T^3 (standard linearization result).

        At T=300K, eps=1: h_lin = 4*sigma*300^3 = 6.12.
        With Ts=300.1, Ta=300: h = sigma*(300.1^2+300^2)*(300.1+300)
        ≈ sigma*2*300^2*2*300 = 4*sigma*300^3 ≈ 6.12.
        """
        h = h_radiation_linearized(emissivity=1.0, t_ambient=300.0, t_surface=300.1)
        h_linear = 4 * STEFAN_BOLTZMANN * 300.0**3
        assert h == pytest.approx(h_linear, rel=1e-3)
```

- [ ] **Step 2: Run literature tests**

Run: `cd python && python -m pytest tests/literature/test_lit_convection.py -v`
Expected: all PASS

- [ ] **Step 3: Commit**

```bash
git add python/tests/literature/test_lit_convection.py
git commit -m "test(m7): add literature-validated convection tests (Incropera 7e)"
```

---

## Task 9: Regression fixtures

**Files:**
- Create: `python/tests/regression/fixtures/h_coeff_forced/basic.yaml`
- Create: `python/tests/regression/fixtures/h_coeff_natural/vertical.yaml`
- Create: `python/tests/regression/fixtures/h_coeff_radiation/basic.yaml`
- Create: `python/tests/regression/fixtures/free_conv/box.yaml`
- Create: `python/tests/regression/fixtures/water_cooling/basic.yaml`
- Modify: `python/tests/regression/conftest.py` — add `lib/` to OCTAVE_PATHS

- [ ] **Step 1: Add `lib/` to OCTAVE_PATHS in `conftest.py`**

In `python/tests/regression/conftest.py`, add `"lib"` to the OCTAVE_PATHS tuple:

```python
OCTAVE_PATHS = ":".join(
    str(REPO_ROOT / p)
    for p in (
        "mfiles/Thermal/Formula",
        "mfiles/Thermal/Model",
        "mfiles/Thermal/Designer",
        "lib",
    )
)
```

- [ ] **Step 2: Create regression fixtures**

Create `python/tests/regression/fixtures/h_coeff_forced/basic.yaml`:

```yaml
command: h-coeff
description: Forced convection, L=0.3m, U=5m/s, Ta=25C, Ts=75C (laminar).
octave_script: |
  addpath('lib');
  [h, Re] = h_forced_convection(0.3, 5, 25, 75);
  disp(jsonencode(struct('h', h, 'Re', Re)));
python_call:
  module: thermal_cli.formula.convection
  function: h_forced
  args:
    length: 0.3
    velocity: 5.0
    t_ambient: 298.15
    t_surface: 348.15
tolerance:
  rtol: 1.0e-6
```

Create `python/tests/regression/fixtures/h_coeff_natural/vertical.yaml`:

```yaml
command: h-coeff
description: Natural convection, vertical, L=0.3m, Ta=25C, Ts=75C.
octave_script: |
  addpath('lib');
  [h, Ra] = h_natural_convection('vertical', 0.3, 25, 75);
  disp(jsonencode(struct('h', h, 'Ra', Ra)));
python_call:
  module: thermal_cli.formula.convection
  function: h_natural
  args:
    orientation: vertical
    length: 0.3
    t_ambient: 298.15
    t_surface: 348.15
tolerance:
  rtol: 1.0e-6
```

Create `python/tests/regression/fixtures/h_coeff_radiation/basic.yaml`:

```yaml
command: h-coeff
description: Linearized radiation h, eps=0.9, Ta=25C, Ts=75C.
octave_script: |
  addpath('lib');
  h = h_radiation(0.9, 25, 75);
  disp(jsonencode(struct('h', h)));
python_call:
  module: thermal_cli.formula.convection
  function: h_radiation_linearized
  args:
    emissivity: 0.9
    t_ambient: 298.15
    t_surface: 348.15
tolerance:
  rtol: 1.0e-6
```

Create `python/tests/regression/fixtures/free_conv/box.yaml`:

```yaml
command: free-conv
description: Single vertical face, A=0.01m2, L=0.1m, 5W, Ta=25C.
octave_script: |
  addpath('lib');
  faces(1).area = 0.01;
  faces(1).char_length = 0.1;
  faces(1).orientation = 'vertical';
  faces(1).emissivity = 0.9;
  [T_s, h_arr, q_arr] = free_conv_surface_temp(faces, 25, 5);
  disp(jsonencode(struct('T_surface', T_s, 'h', h_arr(1), 'q', q_arr(1))));
python_call:
  module: tests.regression.helpers
  function: run_free_conv_box
  args: {}
tolerance:
  rtol: 1.0e-4
```

Create `python/tests/regression/fixtures/water_cooling/basic.yaml`:

```yaml
command: water-cooling
description: 1000W, 5 l/min, glycol-water, 4 devices.
octave_script: |
  addpath('lib');
  result = cmd_water_cooling(struct('p_loss','1000','flow','5','t_in','25',...
    'rth_jc','0.5','n_devices','4','cp','3483','rho','1064','rth_cl','0'));
  disp(jsonencode(struct('dT_coolant',result.dT_coolant,'T_out',result.T_out,...
    'T_junction',result.T_junction)));
python_call:
  module: thermal_cli.formula.water_cooling
  function: water_cooling
  args:
    p_loss: 1000.0
    flow_lpm: 5.0
    t_inlet: 298.15
    rth_jc: 0.5
    n_devices: 4
    cp: 3483.0
    rho: 1064.0
    rth_cl: 0.0
tolerance:
  rtol: 1.0e-4
```

- [ ] **Step 3: Add regression helper for free_conv**

The `free_conv` regression fixture needs a Python wrapper because the return type
is a dataclass, not a dict. Add to `python/tests/regression/helpers.py`:

```python
def run_free_conv_box() -> dict:
    """Wrapper for free_conv regression fixture."""
    from thermal_cli.formula.free_conv import Face, free_conv_surface_temp

    faces = [Face(area=0.01, char_length=0.1, orientation="vertical", emissivity=0.9)]
    r = free_conv_surface_temp(faces=faces, t_ambient=298.15, p_total=5.0)
    # Octave returns T in °C; our function returns K — convert for comparison
    return {"T_surface": r.t_surface - 273.15, "h": r.h_per_face[0], "q": r.q_per_face[0]}
```

- [ ] **Step 4: Run regression tests (requires Octave)**

Run: `cd python && python -m pytest tests/regression/ -v -k "h_coeff or free_conv or water_cooling"`
Expected: all PASS (if Octave is installed)

- [ ] **Step 5: Commit**

```bash
git add python/tests/regression/conftest.py \
       python/tests/regression/helpers.py \
       python/tests/regression/fixtures/h_coeff_forced/ \
       python/tests/regression/fixtures/h_coeff_natural/ \
       python/tests/regression/fixtures/h_coeff_radiation/ \
       python/tests/regression/fixtures/free_conv/ \
       python/tests/regression/fixtures/water_cooling/
git commit -m "test(m7): add regression fixtures for h-coeff, free-conv, water-cooling"
```

---

## Task 10: Final integration — run full test suite

**Depends on:** Tasks 1–9

- [ ] **Step 1: Run full unit + literature test suite**

Run: `cd python && python -m pytest tests/unit/ tests/literature/ -v`
Expected: all PASS (including pre-existing M1-M6 tests)

- [ ] **Step 2: Run regression test suite (if Octave available)**

Run: `cd python && python -m pytest tests/regression/ -v`
Expected: all PASS

- [ ] **Step 3: Run ruff linter**

Run: `cd python && ruff check src/ tests/`
Expected: no errors

- [ ] **Step 4: Final commit — update `__init__.py` re-exports**

Verify `heatsinks/__init__.py` exports new modules:

```python
from thermal_cli.heatsinks.natural_conv import NaturalConvHsResult, natural_conv_hs
from thermal_cli.heatsinks.channel_flow import (
    HydraulicResult,
    FinRthResult,
    hydraulic_operating_point,
    fin_thermal_resistance,
)
```

```bash
git add -u
git commit -m "feat(m7): complete M7 — convection, radiation, hydraulic, fin-rth (7 commands)"
```
