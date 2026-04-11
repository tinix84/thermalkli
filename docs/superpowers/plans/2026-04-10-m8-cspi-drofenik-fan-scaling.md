# M8 — CSPI / Drofenik / Fan Scaling

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the 4 M8 commands from the Octave thermal CLI to Python: `cspi`, `cspi-optimize`, `fan-fit`, `cspi-sweep`.

**Architecture:** A new `thermal_cli/cspi/` subpackage provides CSPI calculation (Drofenik eq. 41), fan scaling law fitting (eq. 29-31), single-channel thermal resistance (Gnielinski/VDI), and a geometry optimizer that sweeps channel width to maximize CSPI. CLI commands are wired into the existing Typer app.

**Tech Stack:** Python 3.11+, numpy, scipy, pytest, typer

**Octave source -> Python target mapping:**

| Octave source | Python target |
|---|---|
| `lib/cspi_calc.m` | `cspi/formulas.py::cspi_calc()` |
| `lib/fan_scaling_fit.m` | `cspi/formulas.py::fan_scaling_fit()` |
| `lib/channel_rth.m` | `cspi/formulas.py::channel_rth()` |
| `lib/air_properties.m` | `cspi/formulas.py::air_properties()` |
| `lib/cspi_optimize.m` | `cspi/optimizer.py::cspi_optimize()` |
| `lib/workflow_cspi_sweep.m` | `cspi/optimizer.py::cspi_sweep()` |
| `lib/cmd_cspi.m` | `cli/commands_m8.py` |
| `lib/cmd_cspi_optimize.m` | `cli/commands_m8.py` |
| `lib/cmd_fan_fit.m` | `cli/commands_m8.py` |
| `lib/workflow_cspi_sweep.m` | `cli/commands_m8.py` |

**Key design decisions:**

- Temperatures: `air_properties()` takes **Celsius** (matching Octave for regression parity; this function is internal to cspi, not part of the public formula API which uses K).
- `channel_rth()` takes a `FluidProps` dataclass (density, kinematic_viscosity, prandtl_number, thermal_conductivity, heat_capacity) matching the Octave `fluid` struct.
- Nusselt correlation in `channel_rth`: laminar uses the VDI Heat Atlas developing-flow formula; turbulent uses Gnielinski — different from the Muzychka-Yovanovich model in `heatsinks/channel_flow.py`.
- The `cspi-sweep` command is a workflow (prints a table), not a pure formula. It calls `cspi_optimize` in a loop over `lambda` and `c` arrays from config YAML.

---

## File Structure

### New files to create

```
python/src/thermal_cli/
├── cspi/
│   ├── __init__.py            # re-exports
│   ├── formulas.py            # cspi_calc, fan_scaling_fit, channel_rth, FluidProps, air_properties
│   └── optimizer.py           # cspi_optimize, cspi_sweep
├── cli/
│   └── commands_m8.py         # 4 CLI commands

python/tests/
├── unit/
│   ├── test_cspi_formulas.py
│   └── test_cspi_optimizer.py
├── literature/
│   └── test_lit_cspi.py
└── regression/fixtures/
    ├── cspi/basic.yaml
    ├── fan_fit/basic.yaml
    └── cspi_optimize/aluminum.yaml
```

### Files to modify

- `python/src/thermal_cli/cli/main.py` — register M8 commands
- `python/tests/regression/helpers.py` — add cspi regression wrappers

---

## Task 1: `cspi/formulas.py` — CSPI, fan scaling, channel Rth

**Files:**
- Create: `python/src/thermal_cli/cspi/__init__.py`
- Create: `python/src/thermal_cli/cspi/formulas.py`
- Test: `python/tests/unit/test_cspi_formulas.py`

- [ ] **Step 1: Write failing tests**

Create `python/tests/unit/test_cspi_formulas.py`:

```python
"""Unit tests for thermal_cli.cspi.formulas."""

from __future__ import annotations

import math

import pytest

from thermal_cli.cspi.formulas import (
    FluidProps,
    air_properties,
    channel_rth,
    cspi_calc,
    fan_scaling_fit,
)


# --- cspi_calc ---


class TestCspiCalc:
    def test_basic(self):
        """CSPI = 1 / (Rth * Vol). Rth=0.5 K/W, Vol=2 liters -> CSPI=1."""
        assert cspi_calc(rth=0.5, vol_cs=2.0) == pytest.approx(1.0)

    def test_low_rth_high_cspi(self):
        """Lower Rth -> higher CSPI."""
        assert cspi_calc(rth=0.1, vol_cs=1.0) == pytest.approx(10.0)

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            cspi_calc(0.5, 2.0)  # type: ignore[misc]


# --- fan_scaling_fit ---


class TestFanScalingFit:
    def test_drofenik_example(self):
        """Fit k1, k2, k3 from typical 120mm fan datasheet.
        V_max=0.085 m3/s, dp_max=120 Pa, P_fan=5 W, D=0.12 m, N=2500 rpm.
        N_rps = 2500/60 = 41.667 rev/s.
        k1 = 0.085 / (41.667 * 0.12^3) = 0.085 / 0.072 = 1.181e-3 -- wait, let me recompute.
        Actually: D^3 = 0.001728, N*D^3 = 41.667*0.001728 = 0.072.
        k1 = 0.085/0.072 = 1.1806.
        Hmm that's dimensionless, not matching survey range [0.5e-3..13.5e-3].
        The survey range IS for k1 dimensionless. Let me verify with Drofenik paper values.
        Actually looking at cmd_fan_fit.m, speed is in rpm but fan_scaling_fit takes N directly.
        Let me check: cmd_fan_fit passes parsed.speed directly. The Octave help says --speed <rpm>.
        But fan_scaling_fit.m just uses N as-is. So N is in rpm in the Octave code.
        Drofenik eq. 29: V_MAX = k1 * N * D^3 where N is in rpm.
        k1 = V_max / (N * D^3) = 0.085 / (2500 * 0.001728) = 0.085 / 4.32 = 0.01968.
        That's ~19.7e-3, outside survey range. Let me use different values.
        Use: V_max=0.05, dp_max=50, P_fan=3, D=0.12, N=2500 rpm.
        k1 = 0.05 / (2500*0.001728) = 0.05/4.32 = 0.01157 -> 11.57e-3 (in range).
        k2 = 50 / (2500^2 * 0.12^2) = 50 / (6250000*0.0144) = 50/90000 = 5.556e-4 (in range).
        k3 = 3 / (2500^3 * 0.12^5) = 3 / (15625e6 * 2.488e-5) = 3/388800 = 7.716e-6 (in range).
        """
        k1, k2, k3 = fan_scaling_fit(
            v_max=0.05, dp_max=50.0, p_fan=3.0, d=0.12, n=2500.0
        )
        assert k1 == pytest.approx(0.05 / (2500 * 0.12**3), rel=1e-10)
        assert k2 == pytest.approx(50.0 / (2500**2 * 0.12**2), rel=1e-10)
        assert k3 == pytest.approx(3.0 / (2500**3 * 0.12**5), rel=1e-10)

    def test_returns_three_floats(self):
        k1, k2, k3 = fan_scaling_fit(v_max=0.05, dp_max=50.0, p_fan=3.0, d=0.12, n=2500.0)
        assert isinstance(k1, float)
        assert isinstance(k2, float)
        assert isinstance(k3, float)


# --- air_properties ---


class TestAirProperties:
    def test_at_80c(self):
        """Default Octave: air_properties(80).
        rho = 101325 / 287.058 / (80+273.15) = 101325/287.058/353.15 = 0.9994.
        """
        fp = air_properties(80.0)
        assert isinstance(fp, FluidProps)
        assert fp.density == pytest.approx(101325 / 287.058 / 353.15, rel=1e-6)
        assert fp.prandtl_number == pytest.approx(0.71)
        assert fp.heat_capacity == pytest.approx(1010.0)

    def test_viscosity_positive(self):
        fp = air_properties(25.0)
        assert fp.kinematic_viscosity > 0
        assert fp.thermal_conductivity > 0


# --- channel_rth ---


class TestChannelRth:
    def test_laminar_rectangular(self):
        """Rectangular channel, low flow -> laminar (Re < 2300).
        Width=2mm, height=20mm, length=100mm, low flow rate.
        """
        fp = air_properties(80.0)
        rth, re, nu, h = channel_rth(
            width=0.002, height=0.020, length=0.100, flow_rate=1e-5, fluid=fp
        )
        assert re < 2300
        assert rth > 0
        assert nu > 0
        assert h > 0

    def test_turbulent_rectangular(self):
        """Higher flow -> turbulent."""
        fp = air_properties(80.0)
        rth, re, nu, h = channel_rth(
            width=0.005, height=0.030, length=0.100, flow_rate=0.01, fluid=fp
        )
        assert re > 2300
        assert rth > 0

    def test_higher_flow_lower_rth(self):
        fp = air_properties(80.0)
        rth_low, *_ = channel_rth(
            width=0.003, height=0.020, length=0.100, flow_rate=1e-5, fluid=fp
        )
        rth_high, *_ = channel_rth(
            width=0.003, height=0.020, length=0.100, flow_rate=1e-4, fluid=fp
        )
        assert rth_high < rth_low

    def test_circular_channel(self):
        """Circular channel using diameter parameter."""
        fp = air_properties(80.0)
        rth, re, nu, h = channel_rth(
            diameter=0.005, length=0.100, flow_rate=1e-4, fluid=fp
        )
        assert rth > 0
        assert re > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_cspi_formulas.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Create `cspi/__init__.py`**

Create `python/src/thermal_cli/cspi/__init__.py`:

```python
"""CSPI (Cooling System Performance Index) module — Drofenik & Kolar CIPS06."""

from thermal_cli.cspi.formulas import (
    FluidProps,
    air_properties,
    channel_rth,
    cspi_calc,
    fan_scaling_fit,
)

__all__ = [
    "FluidProps",
    "air_properties",
    "channel_rth",
    "cspi_calc",
    "fan_scaling_fit",
]
```

- [ ] **Step 4: Implement `cspi/formulas.py`**

Create `python/src/thermal_cli/cspi/formulas.py`:

```python
"""CSPI formulas: metric calculation, fan scaling laws, channel thermal resistance.

References:
  Drofenik & Kolar, "A General Scheme for Calculating Switching- and
  Conduction-Losses of Power Semiconductors in Numerical Circuit Simulations
  of Power Electronic Systems", CIPS 2006.

  Channel Rth uses the VDI Heat Atlas developing-flow Nusselt correlation
  (laminar) and Gnielinski (turbulent).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Fluid properties (inline air correlations matching lib/air_properties.m)
# ---------------------------------------------------------------------------


@dataclass
class FluidProps:
    """Air (or other fluid) properties at a reference temperature."""

    density: float  # [kg/m^3]
    kinematic_viscosity: float  # [m^2/s]
    prandtl_number: float  # [-]
    thermal_conductivity: float  # [W/(m K)]
    heat_capacity: float  # [J/(kg K)]


def air_properties(t_ref_c: float = 80.0) -> FluidProps:
    """Air properties at *t_ref_c* [deg C] using inline correlations.

    Matches ``lib/air_properties.m`` exactly: ideal-gas density, Sutherland
    viscosity, constant Pr=0.71, linear thermal conductivity, cp=1010.
    """
    t = t_ref_c + 273.15
    rho = 101325.0 / 287.058 / t
    mu = 18.27e-6 * (291.15 + 120) / (t + 120) * (t / 291.15) ** 1.5
    nu = mu / rho
    kf = 7e-5 * t + 5.1e-3
    return FluidProps(
        density=rho,
        kinematic_viscosity=nu,
        prandtl_number=0.71,
        thermal_conductivity=kf,
        heat_capacity=1010.0,
    )


# ---------------------------------------------------------------------------
# CSPI metric (Drofenik eq. 41)
# ---------------------------------------------------------------------------


def cspi_calc(*, rth: float, vol_cs: float) -> float:
    """CSPI = 1 / (Rth * Vol_CS).

    Parameters
    ----------
    rth : float
        Heatsink-to-ambient thermal resistance [K/W].
    vol_cs : float
        Cooling system volume [liters].

    Returns
    -------
    float
        CSPI [W/(K liter)].
    """
    return 1.0 / (rth * vol_cs)


# ---------------------------------------------------------------------------
# Fan scaling law fit (Drofenik eq. 29-31)
# ---------------------------------------------------------------------------


def fan_scaling_fit(
    *,
    v_max: float,
    dp_max: float,
    p_fan: float,
    d: float,
    n: float,
) -> tuple[float, float, float]:
    """Fit fan scaling constants k1, k2, k3 from datasheet values.

    Parameters
    ----------
    v_max : float
        Max volumetric flow at zero pressure [m^3/s].
    dp_max : float
        Max static pressure at zero flow [Pa].
    p_fan : float
        Fan shaft power [W].
    d : float
        Fan diameter [m].
    n : float
        Fan speed [rpm].

    Returns
    -------
    tuple[float, float, float]
        ``(k1, k2, k3)`` — dimensionless fan scaling constants.
    """
    k1 = v_max / (n * d**3)
    k2 = dp_max / (n**2 * d**2)
    k3 = p_fan / (n**3 * d**5)
    return float(k1), float(k2), float(k3)


# ---------------------------------------------------------------------------
# Channel thermal resistance (from lib/channel_rth.m)
# ---------------------------------------------------------------------------


def channel_rth(
    *,
    width: float | None = None,
    height: float | None = None,
    diameter: float | None = None,
    length: float,
    flow_rate: float,
    fluid: FluidProps,
) -> tuple[float, float, float, float]:
    """Single-channel convective thermal resistance.

    Supports rectangular (width + height) or circular (diameter) cross-sections.
    Nusselt: VDI Heat Atlas developing-flow (laminar, Re <= 2300) or
    Gnielinski (turbulent, Re > 2300).

    Parameters
    ----------
    width, height : float, optional
        Rectangular channel dimensions [m].
    diameter : float, optional
        Circular channel diameter [m] (alternative to width/height).
    length : float
        Channel length [m].
    flow_rate : float
        Volumetric flow rate through this channel [m^3/s].
    fluid : FluidProps
        Fluid properties at reference temperature.

    Returns
    -------
    tuple[float, float, float, float]
        ``(rth, Re, Nu, h)`` — thermal resistance [K/W], Reynolds number,
        Nusselt number, heat transfer coefficient [W/(m^2 K)].
    """
    if diameter is not None:
        dh = diameter
        ac = (diameter / 2) ** 2 * math.pi
        p = math.pi * diameter
    else:
        assert width is not None and height is not None
        dh = 4 * width * height / 2 / (height + width)
        ac = width * height
        p = 2 * (width + height)

    v = flow_rate / ac
    re = v * dh / fluid.kinematic_viscosity

    pr = fluid.prandtl_number

    if re <= 2300:
        # VDI Heat Atlas developing-flow correlation
        x = length / dh / re / pr if re > 0 else 1e30
        nu = (
            3.657 / math.tanh(2.264 * x ** (1 / 3) + 1.7 * x ** (2 / 3))
            + 0.0499 * math.tanh(x) / x
        ) / math.tanh(2.432 * pr ** (1 / 6) * x ** (1 / 6))
    else:
        # Gnielinski correlation
        f = (0.79 * math.log(re) - 1.64) ** 2
        nu = (
            (re - 1000) * pr * (1 + (dh / length) ** (2 / 3))
            / (8 * f)
            / (1 + 12.7 * math.sqrt(1 / (8 * f)) * (pr ** (2 / 3) - 1))
        )

    h = nu * fluid.thermal_conductivity / dh
    rth = 1 / (h * length * p) + 0.5 / (fluid.density * fluid.heat_capacity * flow_rate)

    return rth, re, nu, h
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_cspi_formulas.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add python/src/thermal_cli/cspi/__init__.py \
       python/src/thermal_cli/cspi/formulas.py \
       python/tests/unit/test_cspi_formulas.py
git commit -m "feat(m8): add CSPI formulas (cspi_calc, fan_scaling_fit, channel_rth)"
```

---

## Task 2: `cspi/optimizer.py` — CSPI geometry optimizer + sweep

**Files:**
- Create: `python/src/thermal_cli/cspi/optimizer.py`
- Modify: `python/src/thermal_cli/cspi/__init__.py`
- Test: `python/tests/unit/test_cspi_optimizer.py`

**Depends on:** Task 1

- [ ] **Step 1: Write failing tests**

Create `python/tests/unit/test_cspi_optimizer.py`:

```python
"""Unit tests for thermal_cli.cspi.optimizer."""

from __future__ import annotations

import pytest

from thermal_cli.cspi.optimizer import CspiOptResult, CspiSweepResult, cspi_optimize, cspi_sweep


class TestCspiOptimize:
    def test_aluminum_typical(self):
        """Aluminum HS (lambda=200), A_chip=10cm2, c=40mm, P_fan=5W.
        Should find a valid optimum with CSPI > 0.
        """
        r = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=0.040,
            p_fan_max=5.0,
        )
        assert isinstance(r, CspiOptResult)
        assert r.cspi > 0
        assert r.rth > 0
        assert r.n > 1
        assert r.s > 0
        assert r.t > 0

    def test_copper_better_than_aluminum(self):
        """Higher conductivity -> higher CSPI (better performance)."""
        kwargs = dict(a_chip=10e-4, c=0.040, p_fan_max=5.0)
        r_al = cspi_optimize(lambda_hs=200.0, **kwargs)
        r_cu = cspi_optimize(lambda_hs=385.0, **kwargs)
        assert r_cu.cspi > r_al.cspi

    def test_larger_fan_better_cspi(self):
        """More fan power -> lower Rth -> higher CSPI."""
        kwargs = dict(lambda_hs=200.0, a_chip=10e-4, c=0.040)
        r_low = cspi_optimize(p_fan_max=1.0, **kwargs)
        r_high = cspi_optimize(p_fan_max=10.0, **kwargs)
        assert r_high.cspi > r_low.cspi

    def test_custom_fan_constants(self):
        r = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=0.040,
            p_fan_max=5.0,
            k1=8e-3,
            k2=6e-4,
            k3=40e-6,
        )
        assert r.cspi > 0

    def test_with_min_thickness(self):
        r = cspi_optimize(
            lambda_hs=200.0,
            a_chip=10e-4,
            c=0.040,
            p_fan_max=5.0,
            t_min=0.5e-3,
        )
        assert r.t >= 0.5e-3 or r.t == pytest.approx(0.5e-3, abs=1e-6)

    def test_feasibility_flag(self):
        """Result includes a feasibility flag (Re<2300 and valid geometry)."""
        r = cspi_optimize(
            lambda_hs=200.0, a_chip=10e-4, c=0.040, p_fan_max=5.0
        )
        assert isinstance(r.feasible, bool)


class TestCspiSweep:
    def test_basic_sweep(self):
        """Sweep over 2 lambda values and 2 c values -> 2x2 result grid."""
        r = cspi_sweep(
            a_chip=10e-4,
            p_fan_max=5.0,
            lambdas=[200.0, 385.0],
            cs=[0.030, 0.050],
        )
        assert isinstance(r, CspiSweepResult)
        assert r.cspi.shape == (2, 2)
        assert r.rth.shape == (2, 2)
        assert all(c > 0 for c in r.cspi.flat)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_cspi_optimizer.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `cspi/optimizer.py`**

Create `python/src/thermal_cli/cspi/optimizer.py`:

```python
"""CSPI geometry optimizer (Drofenik & Kolar CIPS06).

Sweeps channel width to find the heatsink geometry that maximizes CSPI.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from thermal_cli.cspi.formulas import air_properties, channel_rth, cspi_calc


@dataclass
class CspiOptResult:
    """Output of the CSPI geometry optimizer."""

    cspi: float  # [W/(K liter)]
    rth: float  # [K/W]
    vol: float  # [liters]
    n: int  # number of channels/fins
    s: float  # optimal channel width [m]
    t: float  # fin thickness [m]
    re: float  # Reynolds number at optimum
    n_fan: float  # fan speed [rpm]
    length: float  # heatsink length [m]
    v_max: float  # max fan flow [m^3/s]
    dp_max: float  # max fan pressure [Pa]
    feasible: bool  # True if Re<2300 and geometry is valid


def cspi_optimize(
    *,
    lambda_hs: float,
    a_chip: float,
    c: float,
    p_fan_max: float,
    t_min: float = 0.0,
    k1: float = 6e-3,
    k2: float = 5e-4,
    k3: float = 30e-6,
    t_air: float = 80.0,
    n_pts: int = 80,
) -> CspiOptResult:
    """Find optimal heatsink channel width maximizing CSPI.

    Parameters
    ----------
    lambda_hs : float
        Heatsink thermal conductivity [W/(m K)].
    a_chip : float
        Total chip footprint area [m^2].
    c : float
        Heatsink height = fan diameter [m].
    p_fan_max : float
        Maximum fan shaft power [W].
    t_min : float
        Minimum fin thickness [m] (default 0).
    k1, k2, k3 : float
        Fan scaling constants (Drofenik eq. 29-31).
    t_air : float
        Reference air temperature [deg C] (default 80).
    n_pts : int
        Number of sweep points (default 80).

    Returns
    -------
    CspiOptResult
    """
    length = a_chip / c

    # Fan operating point at max power
    n_fan = (p_fan_max / (k3 * c**5)) ** (1 / 3)
    v_max = k1 * n_fan * c**3
    dp_max = k2 * n_fan**2 * c**2

    fluid = air_properties(t_air)

    # Sweep channel width
    s_min = max(t_min * 0.5, 0.2e-3)
    s_max = c * 0.5
    s_arr = np.linspace(s_min, s_max, n_pts)
    cspi_arr = np.zeros(n_pts)

    for idx in range(n_pts):
        s_try = float(s_arr[idx])

        if t_min > 0:
            n_try = int(c // (s_try + t_min))
        else:
            n_try = int(c // (2 * s_try))

        if n_try < 2:
            continue

        t_try = c / n_try - s_try
        if t_try < t_min or t_try <= 0:
            continue

        v_total = v_max * 0.5
        v_ch = v_total / n_try
        if v_ch <= 0:
            continue

        try:
            rth_ch, _re, _nu, _h = channel_rth(
                width=s_try, height=c, length=length, flow_rate=v_ch, fluid=fluid
            )
        except Exception:
            continue

        if rth_ch <= 0 or not np.isfinite(rth_ch):
            continue

        rth_fin = (t_try / 2) / (lambda_hs * c * length)
        rth_total = (rth_fin + rth_ch) / n_try

        if rth_total <= 0 or not np.isfinite(rth_total):
            continue

        vol_cs = length * c * c * 1000  # liters
        cspi_arr[idx] = cspi_calc(rth=rth_total, vol_cs=vol_cs)

    best_idx = int(np.argmax(cspi_arr))
    s_opt = float(s_arr[best_idx])

    # Recompute final geometry at optimum
    if t_min > 0:
        n_fin = int(c // (s_opt + t_min))
    else:
        n_fin = int(c // (2 * s_opt))
    if n_fin < 2:
        n_fin = 2

    t_fin = c / n_fin - s_opt
    if t_fin < t_min:
        t_fin = t_min
        n_fin = int(c // (s_opt + t_fin))
        if n_fin < 2:
            n_fin = 2
        t_fin = c / n_fin - s_opt
    if t_fin <= 0:
        t_fin = 0.1e-3

    v_total = v_max * 0.5
    v_ch = v_total / n_fin

    rth_ch, re_fin, _nu, _h = channel_rth(
        width=s_opt, height=c, length=length, flow_rate=v_ch, fluid=fluid
    )
    rth_fin_cond = (t_fin / 2) / (lambda_hs * c * length)
    rth = (rth_fin_cond + rth_ch) / n_fin
    vol_cs = length * c * c * 1000

    return CspiOptResult(
        cspi=cspi_calc(rth=rth, vol_cs=vol_cs),
        rth=rth,
        vol=vol_cs,
        n=n_fin,
        s=s_opt,
        t=t_fin,
        re=re_fin,
        n_fan=n_fan,
        length=length,
        v_max=v_max,
        dp_max=dp_max,
        feasible=bool(re_fin < 2300 and t_fin > 0 and rth > 0 and np.isfinite(rth)),
    )


# ---------------------------------------------------------------------------
# Parametric sweep
# ---------------------------------------------------------------------------


@dataclass
class CspiSweepResult:
    """Output of the CSPI parametric sweep."""

    cs: list[float]  # [m]
    lambdas: list[float]  # [W/(m K)]
    cspi: np.ndarray  # shape (len(cs), len(lambdas))
    rth: np.ndarray  # shape (len(cs), len(lambdas))


def cspi_sweep(
    *,
    a_chip: float,
    p_fan_max: float,
    lambdas: list[float],
    cs: list[float],
    t_min: float = 0.0,
    **kwargs: float,
) -> CspiSweepResult:
    """Parametric CSPI sweep over conductivity and heatsink height.

    Parameters
    ----------
    a_chip : float
        Chip footprint area [m^2].
    p_fan_max : float
        Maximum fan power [W].
    lambdas : list[float]
        Thermal conductivities to sweep [W/(m K)].
    cs : list[float]
        Heatsink heights to sweep [m].
    t_min : float
        Minimum fin thickness [m].
    **kwargs
        Passed to ``cspi_optimize`` (k1, k2, k3, t_air).

    Returns
    -------
    CspiSweepResult
    """
    n_c = len(cs)
    n_l = len(lambdas)
    cspi_grid = np.zeros((n_c, n_l))
    rth_grid = np.zeros((n_c, n_l))

    for i, c_val in enumerate(cs):
        for j, lam in enumerate(lambdas):
            r = cspi_optimize(
                lambda_hs=lam,
                a_chip=a_chip,
                c=c_val,
                p_fan_max=p_fan_max,
                t_min=t_min,
                **kwargs,
            )
            cspi_grid[i, j] = r.cspi
            rth_grid[i, j] = r.rth

    return CspiSweepResult(cs=cs, lambdas=lambdas, cspi=cspi_grid, rth=rth_grid)
```

- [ ] **Step 4: Update `cspi/__init__.py`**

Add to `python/src/thermal_cli/cspi/__init__.py`:

```python
from thermal_cli.cspi.optimizer import (
    CspiOptResult,
    CspiSweepResult,
    cspi_optimize,
    cspi_sweep,
)
```

And extend `__all__`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_cspi_optimizer.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add python/src/thermal_cli/cspi/optimizer.py \
       python/src/thermal_cli/cspi/__init__.py \
       python/tests/unit/test_cspi_optimizer.py
git commit -m "feat(m8): add CSPI geometry optimizer and parametric sweep"
```

---

## Task 3: CLI commands (`cspi`, `cspi-optimize`, `fan-fit`, `cspi-sweep`)

**Files:**
- Create: `python/src/thermal_cli/cli/commands_m8.py`
- Modify: `python/src/thermal_cli/cli/main.py`
- Test: `python/tests/unit/test_cli_m8.py`

**Depends on:** Tasks 1-2

- [ ] **Step 1: Write failing CLI smoke tests**

Create `python/tests/unit/test_cli_m8.py`:

```python
"""Smoke tests for M8 CLI commands."""

from __future__ import annotations

from typer.testing import CliRunner

from thermal_cli.cli.main import app

runner = CliRunner()


class TestCspiCli:
    def test_basic(self):
        result = runner.invoke(app, ["cspi", "--rth", "0.5", "--vol", "2.0"])
        assert result.exit_code == 0
        assert "cspi=" in result.stdout


class TestCspiOptimizeCli:
    def test_basic(self):
        result = runner.invoke(app, [
            "cspi-optimize",
            "--lambda", "200",
            "--a-chip", "10e-4",
            "--c", "0.04",
            "--p-fan", "5",
        ])
        assert result.exit_code == 0
        assert "cspi=" in result.stdout
        assert "rth=" in result.stdout
        assert "n_fins=" in result.stdout


class TestFanFitCli:
    def test_basic(self):
        result = runner.invoke(app, [
            "fan-fit",
            "--v-max", "0.05",
            "--dp-max", "50",
            "--p-fan", "3",
            "--diameter", "0.12",
            "--speed", "2500",
        ])
        assert result.exit_code == 0
        assert "k1=" in result.stdout
        assert "k2=" in result.stdout
        assert "k3=" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_cli_m8.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `cli/commands_m8.py`**

Create `python/src/thermal_cli/cli/commands_m8.py`:

```python
"""M8 CLI commands: CSPI, fan scaling, optimizer, sweep."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer


def register_all(app: typer.Typer) -> None:
    """Register all M8 commands on the Typer app."""

    @app.command("cspi")
    def cspi_cmd(
        rth: Annotated[float, typer.Option("--rth", help="Thermal resistance [K/W]")],
        vol: Annotated[float, typer.Option("--vol", help="Heatsink volume [liters]")],
    ) -> None:
        """Compute CSPI = 1 / (Rth * Vol) [W/(K*liter)]."""
        from thermal_cli.cspi.formulas import cspi_calc

        cspi = cspi_calc(rth=rth, vol_cs=vol)
        typer.echo(f"cspi={cspi:.4f}")

    @app.command("cspi-optimize")
    def cspi_optimize_cmd(
        lambda_hs: Annotated[float, typer.Option("--lambda", help="Conductivity [W/(m K)]")],
        a_chip: Annotated[float, typer.Option("--a-chip", help="Chip area [m^2]")],
        c: Annotated[float, typer.Option("--c", help="Heatsink height = fan D [m]")],
        p_fan: Annotated[float, typer.Option("--p-fan", help="Max fan power [W]")],
        t_min: Annotated[float, typer.Option("--t-min", help="Min fin thickness [m]")] = 0.0,
        k1: Annotated[float, typer.Option(help="Fan k1")] = 6e-3,
        k2: Annotated[float, typer.Option(help="Fan k2")] = 5e-4,
        k3: Annotated[float, typer.Option(help="Fan k3")] = 30e-6,
        t_air: Annotated[float, typer.Option("--t-air", help="Air temp [C]")] = 80.0,
    ) -> None:
        """Find optimal heatsink geometry maximizing CSPI (Drofenik CIPS06)."""
        from thermal_cli.cspi.optimizer import cspi_optimize

        r = cspi_optimize(
            lambda_hs=lambda_hs,
            a_chip=a_chip,
            c=c,
            p_fan_max=p_fan,
            t_min=t_min,
            k1=k1,
            k2=k2,
            k3=k3,
            t_air=t_air,
        )
        typer.echo(f"cspi={r.cspi:.4f}")
        typer.echo(f"rth={r.rth:.6f}")
        typer.echo(f"vol={r.vol:.4f}")
        typer.echo(f"n_fins={r.n}")
        typer.echo(f"s_channel={r.s:.4e}")
        typer.echo(f"t_fin={r.t:.4e}")
        typer.echo(f"Re={r.re:.1f}")
        typer.echo(f"N_fan={r.n_fan:.0f}")
        typer.echo(f"V_MAX={r.v_max:.4e}")
        typer.echo(f"dp_MAX={r.dp_max:.2f}")
        typer.echo(f"feasible={int(r.feasible)}")

    @app.command("fan-fit")
    def fan_fit_cmd(
        v_max: Annotated[float, typer.Option("--v-max", help="Max flow [m^3/s]")],
        dp_max: Annotated[float, typer.Option("--dp-max", help="Max pressure [Pa]")],
        p_fan: Annotated[float, typer.Option("--p-fan", help="Fan power [W]")],
        diameter: Annotated[float, typer.Option(help="Fan diameter [m]")],
        speed: Annotated[float, typer.Option(help="Fan speed [rpm]")],
    ) -> None:
        """Fit fan scaling law constants k1, k2, k3 (Drofenik eq. 29-31)."""
        from thermal_cli.cspi.formulas import fan_scaling_fit

        k1, k2, k3 = fan_scaling_fit(
            v_max=v_max, dp_max=dp_max, p_fan=p_fan, d=diameter, n=speed
        )
        typer.echo(f"k1={k1:.4e}")
        typer.echo(f"k2={k2:.4e}")
        typer.echo(f"k3={k3:.4e}")

    @app.command("cspi-sweep")
    def cspi_sweep_cmd(
        config: Annotated[Path, typer.Option(help="Config YAML file")],
    ) -> None:
        """Parametric CSPI sweep over conductivity and heatsink height."""
        import yaml

        from thermal_cli.cspi.optimizer import cspi_sweep

        cfg = yaml.safe_load(config.read_text())
        r = cspi_sweep(
            a_chip=cfg["a_chip"],
            p_fan_max=cfg["p_fan_max"],
            lambdas=cfg["lambda"],
            cs=cfg["c"],
            t_min=cfg.get("t_min", 0.0),
        )
        # Print table header
        header = f"{'c [mm]':>10}"
        for lam in r.lambdas:
            header += f"  lambda={int(lam):>4}"
        typer.echo(header)
        typer.echo("-" * len(header))
        # Print rows
        for i, c_val in enumerate(r.cs):
            row = f"{c_val * 1e3:>10.0f}"
            for j in range(len(r.lambdas)):
                if r.cspi[i, j] > 0:
                    row += f"  {r.cspi[i, j]:>10.1f}"
                else:
                    row += f"  {'N/A':>10}"
            typer.echo(row)
```

- [ ] **Step 4: Wire into `cli/main.py`**

Add to `python/src/thermal_cli/cli/main.py`:

```python
from thermal_cli.cli.commands_m8 import register_all as register_m8
register_m8(app)
```

- [ ] **Step 5: Run CLI smoke tests**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/unit/test_cli_m8.py -v`
Expected: all PASS

- [ ] **Step 6: Run full suite**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/ --tb=short`
Expected: all PASS (no regressions)

- [ ] **Step 7: Commit**

```bash
git add python/src/thermal_cli/cli/commands_m8.py \
       python/src/thermal_cli/cli/main.py \
       python/tests/unit/test_cli_m8.py
git commit -m "feat(m8): add CLI commands (cspi, cspi-optimize, fan-fit, cspi-sweep)"
```

---

## Task 4: Literature tests + regression fixtures

**Files:**
- Create: `python/tests/literature/test_lit_cspi.py`
- Create: `python/tests/regression/fixtures/cspi/basic.yaml`
- Create: `python/tests/regression/fixtures/fan_fit/basic.yaml`
- Create: `python/tests/regression/fixtures/cspi_optimize/aluminum.yaml`
- Modify: `python/tests/regression/helpers.py`

**Depends on:** Tasks 1-3

- [ ] **Step 1: Write literature tests**

Create `python/tests/literature/test_lit_cspi.py`:

```python
"""Literature-validated tests for CSPI formulas.

Reference: Drofenik & Kolar, CIPS 2006.
"""

from __future__ import annotations

import pytest

from thermal_cli.cspi.formulas import cspi_calc, fan_scaling_fit


class TestCspiLiterature:
    def test_eq41_definition(self):
        """CSPI is defined as 1/(Rth * Vol) — eq. 41.
        A system with Rth=0.2 K/W and Vol=1 liter has CSPI=5."""
        assert cspi_calc(rth=0.2, vol_cs=1.0) == pytest.approx(5.0)

    def test_cspi_units_consistency(self):
        """CSPI units: [W/(K*liter)]. Verify dimensional consistency.
        Rth=1 K/W, Vol=1 liter -> CSPI=1 W/(K*liter)."""
        assert cspi_calc(rth=1.0, vol_cs=1.0) == pytest.approx(1.0)


class TestFanScalingLiterature:
    def test_drofenik_eq29_31_roundtrip(self):
        """Fan scaling law roundtrip: fit k1,k2,k3 then predict back.
        V_MAX = k1*N*D^3, dp_MAX = k2*N^2*D^2, P = k3*N^3*D^5.
        """
        v_max, dp_max, p_fan = 0.06, 80.0, 4.0
        d, n = 0.10, 3000.0
        k1, k2, k3 = fan_scaling_fit(
            v_max=v_max, dp_max=dp_max, p_fan=p_fan, d=d, n=n
        )
        # Reconstruct
        assert k1 * n * d**3 == pytest.approx(v_max, rel=1e-10)
        assert k2 * n**2 * d**2 == pytest.approx(dp_max, rel=1e-10)
        assert k3 * n**3 * d**5 == pytest.approx(p_fan, rel=1e-10)
```

- [ ] **Step 2: Create regression fixtures**

Create `python/tests/regression/fixtures/cspi/basic.yaml`:

```yaml
command: cspi
description: CSPI = 1/(0.5 * 2.0) = 1.0
octave_script: |
  addpath('lib');
  cspi = cspi_calc(0.5, 2.0);
  disp(jsonencode(struct('cspi', cspi)));
python_call:
  module: thermal_cli.cspi.formulas
  function: cspi_calc
  args:
    rth: 0.5
    vol_cs: 2.0
tolerance:
  rtol: 1.0e-12
```

Create `python/tests/regression/fixtures/fan_fit/basic.yaml`:

```yaml
command: fan-fit
description: Fan scaling constants for V=0.05, dp=50, P=3, D=0.12, N=2500.
octave_script: |
  addpath('lib');
  [k1, k2, k3] = fan_scaling_fit(0.05, 50, 3, 0.12, 2500);
  disp(jsonencode(struct('k1', k1, 'k2', k2, 'k3', k3)));
python_call:
  module: thermal_cli.cspi.formulas
  function: fan_scaling_fit
  args:
    v_max: 0.05
    dp_max: 50.0
    p_fan: 3.0
    d: 0.12
    n: 2500.0
tolerance:
  rtol: 1.0e-10
```

Create `python/tests/regression/fixtures/cspi_optimize/aluminum.yaml`:

```yaml
command: cspi-optimize
description: Aluminum HS, A_chip=10cm2, c=40mm, P_fan=5W.
octave_script: |
  addpath('lib');
  r = cspi_optimize(200, 10e-4, 0.040, 5);
  disp(jsonencode(struct('cspi', r.cspi, 'rth', r.rth, 'n', r.n, 's', r.s)));
python_call:
  module: tests.regression.helpers
  function: run_cspi_optimize_aluminum
  args: {}
tolerance:
  rtol: 1.0e-4
```

- [ ] **Step 3: Add regression helper**

Add to `python/tests/regression/helpers.py`:

```python
def run_cspi_optimize_aluminum() -> dict:
    """Wrapper for cspi_optimize regression fixture."""
    from thermal_cli.cspi.optimizer import cspi_optimize

    r = cspi_optimize(lambda_hs=200.0, a_chip=10e-4, c=0.040, p_fan_max=5.0)
    return {"cspi": r.cspi, "rth": r.rth, "n": float(r.n), "s": r.s}
```

- [ ] **Step 4: Run all tests**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/ --tb=short`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add python/tests/literature/test_lit_cspi.py \
       python/tests/regression/fixtures/cspi/ \
       python/tests/regression/fixtures/fan_fit/ \
       python/tests/regression/fixtures/cspi_optimize/ \
       python/tests/regression/helpers.py
git commit -m "test(m8): add literature + regression tests for CSPI commands"
```

---

## Task 5: Final integration — lint, format, full suite green

**Depends on:** Tasks 1-4

- [ ] **Step 1: Run ruff lint**

Run: `cd python && conda run -n ntbees2 ruff check src/ tests/`
Fix any errors.

- [ ] **Step 2: Run ruff format**

Run: `cd python && conda run -n ntbees2 ruff format src/ tests/`

- [ ] **Step 3: Run full test suite**

Run: `cd python && conda run -n ntbees2 python -m pytest tests/ -v --tb=short`
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add -u
git commit -m "feat(m8): complete M8 — CSPI, fan scaling, optimizer (4 commands)"
```
