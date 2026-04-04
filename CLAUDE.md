# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

MATLAB/Octave thermal engineering library for heatsink design, thermal resistance modeling, and semiconductor thermal analysis. Used in power electronics thermal management (inverters, rectifiers, thyristor bridges). Contains both an OOP-based English-language library (`mfiles/Thermal/`) and a legacy Italian-language simulation tool (`mfiles/SoftwareTermico/`).

## Running Code

```bash
# Run scripts in Octave
octave --path mfiles/Thermal/Designer:mfiles/Thermal/Model:mfiles/Thermal/Formula -q script.m

# Run a specific test/calculation script
octave mfiles/Thermal/Designer/testScript.m
```

Scripts expect `addpath` calls to resolve class dependencies. The `mfiles/Thermal/Designer/` scripts reference `W:\Technology\Functions\Thermal\` (Windows network path) for database access — adapt paths when running on Linux/WSL.

## Architecture

### `mfiles/Thermal/` — Core OOP Library

**Model layer** (`Model/`): Domain objects for heatsinks and fluid properties.
- `HeatsinkClass` — base class for all heatsinks (fluid, flowrate, thermal resistance)
- `extrudedFinModel < HeatsinkClass` — extruded-fin heatsink with channel geometry, Reynolds number, Nusselt correlations
- `GasProperty`, `LiquidProperty` — fluid property calculators (density, viscosity, conductivity, specific heat vs temperature), data sourced from `db/FluidData.xlsx`
- `fluidPropertyFactory` — returns appropriate fluid object by reference string (`'airDry'`, `'H2OGly50'`, `'SAE30'`)
- `heatsinkFactory` — creates heatsink from database reference in `db/heatsinks.xlsx`

**Designer layer** (`Designer/`): Thermal resistance network for semiconductor-on-PCB assemblies.
- `ThermalModelSemi` — main thermal model: builds a resistance network from junction through PCB/vias/spreader to fluid, supports 5 heat path cases (bottom-only, top+bottom, with/without vias)
- `ThermalModelSemiInput` / `ThermalModelSemiOutput` — input specification and results containers
- `ThermalLayer` — single material layer with thickness, out-of-plane and in-plane conductivity; computes thermal resistance with spreading (Lee/Simons/Ying models)
- `ThermalLayerStack` — composite of `ThermalLayer` objects; series resistance and spreading optimization across layers
- `ThermalPcb` — PCB model with via array thermal conductivity
- `LossTemperatureInteraction/` — iterative loss-temperature coupling for semiconductor operating point

**Formula** (`Formula/`): Standalone analytical formulas — fin efficiency, radiation heat transfer (parallel planes, concentric cylinders/spheres, enclosures).

**Optimizer** (`Optimizer/`): Parametric sweeps over extruded-fin heatsink geometry.

**Verifier** (`Verifier/`): Cross-validation scripts against FEMM finite-element results.

### `mfiles/SoftwareTermico/` — Legacy Simulation Tool (Italian)

GUI-driven heatsink thermal simulation with fan database, heatsink profile database, multi-source temperature distribution on a heatsink plane. Dimensions in mm, comments in Italian. Entry points: `Simulazione_singola/Simulazione_Singola.m` and `Simulazione_multipla/Simulazione_Multipla.m`.

### `db/` — Excel Databases

- `heatsinks.xlsx` — extruded heatsink profiles (geometry, material)
- `FluidData.xlsx` — fluid thermal properties vs temperature
- `Thermal_Interface_Materials.xlsx` — TIM thermal insulance data

## Key Conventions

- SI units throughout the OOP library (meters, Kelvin, Watts). The legacy `SoftwareTermico` uses mm.
- Thermal conductivity: `kOp` = out-of-plane, `kIp` = in-plane (for anisotropic materials like PCB laminates).
- Spreading resistance uses the Lee/Simons/Ying analytical model with circular-equivalent area substitution.
- Classes inherit from `handle` (reference semantics) where mutation is needed.
- `xlsread` calls reference a Windows network path `W:\Technology\Functions\Thermal\db\` — when running on WSL, database reads may need path adaptation or the `io` package.

## Active Project: CLI Unification

**Goal**: Unify all disconnected scripts into a single Octave CLI (`thermal_cli.m`) with independent commands and predefined workflows, plus a test suite with literature-verified reference values.

**Key decisions** (agreed 2026-04-03):

| Decision | Choice |
|----------|--------|
| Scope | Both `Thermal/` and `SoftwareTermico/` |
| CLI language | Pure Octave (.m) |
| CLI model | Single `thermal_cli.m` dispatcher — independent commands + predefined workflows |
| SoftwareTermico units | Refactor to SI (meters) + English variable names |
| Interactive menus | Replace with `.m` struct config files + CLI flag overrides |
| Test framework | Separate `tests/` directory with `test_*.m` scripts |
| Test reference values | Existing script outputs (regression) + literature values (proposed by Claude, validated by user) |
| Config format | `.m` struct files (native Octave) |
| Excel databases | Keep .xlsx as-is; Python loader planned later |
| FEMM Lua generation | 3 generators (semi-on-pcb axi, extruded-fin 2D, baseplate 2D) + compare-femm command. User runs Lua in FEMM manually, results extracted to CSV |
| CSPI (Drofenik/Kolar) | CSPI metric + optimizer (eq. 45/50), Drofenik channel model, fan scaling law fit, h-forced/natural/radiation commands. Ported from ntbees2 @channel code. |
| LossTemperatureInteraction/ | Out of scope (depends on external SVM_7 function) |
| GUI (prova_grafica.m) | Kept as optional separate concern, not part of CLI |

**Documents**:
- PRD: `docs/prd.md`
- Design spec: `docs/superpowers/specs/` (pending)
- Implementation plan: TBD
