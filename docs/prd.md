# PRD: Thermal Toolbox CLI Unification

**Date**: 2026-04-03
**Status**: Draft

## Problem

The codebase contains ~53 MATLAB/Octave scripts spread across two independent subsystems (`mfiles/Thermal/` and `mfiles/SoftwareTermico/`) that:

1. **Don't connect to each other** — each script is standalone with hardcoded inputs, no shared interface
2. **Can't be composed** — output of one calculation can't feed into another without manual copy-paste of workspace variables
3. **Have no tests** — no way to verify that a formula or model produces correct results after changes
4. **Depend on Windows paths** — `W:\Technology\Functions\Thermal\` references and `xlsread` calls don't work on WSL/Linux
5. **Mix units and languages** — `Thermal/` uses SI+English, `SoftwareTermico/` uses mm+Italian
6. **Use interactive menus** — `menu()` calls make scripts impossible to automate or batch

## Goal

Create a single Octave CLI entry point (`thermal_cli.m`) that:

- Exposes each computation as an independent, composable command
- Provides predefined workflows chaining multiple commands
- Accepts configuration via `.m` struct files with CLI flag overrides
- Has a test suite (`tests/`) verifying each computation against literature and regression values
- Works on WSL/Linux without Windows dependencies

## Scope

### In Scope

| Module | What changes |
|--------|-------------|
| `Thermal/Model/` | Wrap as CLI commands (heatsink creation, fluid properties) |
| `Thermal/Designer/` | Wrap ThermalModelSemi pipeline, layer stack calculations, TO247 calculations as commands + workflow |
| `Thermal/Formula/` | Wrap 6 formula functions as commands; add literature-verified tests |
| `Thermal/Optimizer/` | Wrap parametric sweep as command |
| `Thermal/Verifier/` | FEMM Lua script generation + comparison command |
| `Thermal/Doc/WaterCooling.m` | Wrap as command |
| `SoftwareTermico/` | Refactor to SI+English; wrap Simulazione_singola and Simulazione_multipla as commands + workflow |
| `SoftwareTermico/Coeff_Aria/` | Keep as internal functions (air property correlations) |
| `SoftwareTermico/Therm_hydr/` | Keep as internal functions (hydraulic + thermal resistance) |
| `SoftwareTermico/Database_FAN&HeatSink/` | Keep as internal lookup functions |
| `SoftwareTermico/Visualizzazione_plane/` | Keep as internal functions; expose temperature distribution as command output |
| `db/*.xlsx` | Keep as-is (Python loader planned for future) |
| `tests/` | New directory with `test_*.m` scripts |
| Config files | New `.m` struct files for simulation scenarios |

### Out of Scope

| Module | Why |
|--------|-----|
| `LossTemperatureInteraction/` | Depends on external `SVM_7()` not in this repo |
| `prova_grafica.m` (GUI) | Kept as optional separate concern |
| `rms_da_file.m`, `spettro_da_file.m` | Signal analysis utilities, not thermal calculations |
| `Export_Excel/` | Export formatting, deferred |
| Automated FEMM execution | Lua scripts are generated, user runs them manually in FEMM |
| Database format migration | xlsx stays; Python loader is a future project |

## CLI Design

### Entry Point

```bash
octave thermal_cli.m <command> [--option value ...]
octave thermal_cli.m <workflow> [--config path/to/config.m] [--override value ...]
```

### Command Categories

**Standalone calculations** (independent, composable):

| Command | Source | Description |
|---------|--------|-------------|
| `calc-rth` | `calc_rth_from_power_temp.m` | Rth from power and temperatures |
| `fin-efficiency` | `Formula/finEfficieny.m` | Fin efficiency (tanh model) |
| `radiation-parallel` | `Formula/heatTransferParallelPlanesRadiation.m` | Radiation between parallel planes |
| `radiation-cylinder` | `Formula/heatTransferConcentricCylinderRadiation.m` | Radiation between concentric cylinders |
| `radiation-sphere` | `Formula/heatTransferConcentricSphereRadiation.m` | Radiation between concentric spheres |
| `radiation-enclosure` | `Formula/heatTransferEnclosureRadiation.m` | Radiation in enclosure |
| `radiation-convex` | `Formula/heatTransferSmallConvexRadiation.m` | Radiation from small convex body |
| `layer-rth` | `Designer/ThermalLayer` | Thermal resistance through layer with spreading |
| `stack-rth` | `Designer/ThermalLayerStack` | Thermal resistance through layer stack |
| `heatsink-create` | `Model/heatsinkFactory` | Create heatsink from database reference |
| `heatsink-rth` | `Model/extrudedFinModel` | Extruded fin heatsink thermal resistance |
| `free-conv` | `Designer/freeConvectionEstimation/` | Free convection surface temperature |
| `water-cooling` | `Doc/WaterCooling.m` | Water cooling system thermal analysis |
| `hydraulic-op` | `SoftwareTermico/Therm_hydr/idraulico.m` | Fan-heatsink hydraulic operating point |
| `fin-rth` | `SoftwareTermico/Therm_hydr/Rth_fin.m` | Finned heatsink thermal resistance |
| `temp-dist` | `SoftwareTermico/Visualizzazione_plane/` | Temperature distribution on heatsink plane |
| `gen-femm` | New Lua generator | Generate FEMM Lua script for a thermal model (--model semi-on-pcb\|extruded-fin\|baseplate) |
| `compare-femm` | New comparison utility | Compare FEMM CSV results against analytical CLI results, print % deviation |
| `cspi` | New (Drofenik) | Compute CSPI = 1/(Rth * Vol_CS) from heatsink design result |
| `cspi-optimize` | New (Drofenik eq. 45/50) | Find optimal fin geometry maximizing CSPI for given fan+material+chip area |
| `channel-rth` | Ported from ntbees2 | Drofenik channel model: Rth from channel geometry + flow rate |
| `channel-dp` | Ported from ntbees2 | Channel pressure drop from flow rate (laminar/turbulent) |
| `fan-fit` | New | Fit fan scaling law constants k1,k2,k3 from PQ curve data |
| `h-forced` | Ported from ntbees2 | Forced convection heat transfer coefficient (flat plate) |
| `h-natural` | Ported from ntbees2 | Natural convection heat transfer coefficient (vertical/horizontal) |
| `h-radiation` | Ported from ntbees2 | Radiation heat transfer coefficient (linearized) |

**FEMM integration flag**: Workflows `semi-on-pcb`, `extruded-fin-design`, and `forced-conv-sim` support `--femm-lua <path>` to also generate a FEMM Lua script alongside the analytical calculation.

**Predefined workflows** (chain commands):

| Workflow | Steps | Description |
|----------|-------|-------------|
| `semi-on-pcb` | Define layers -> PCB model -> Rth network -> Tjunction | Full ThermalModelSemi pipeline |
| `extruded-fin-design` | Create heatsink -> Define fluid -> Set geometry -> Compute Rth -> Tjunction | Extruded fin heatsink design |
| `optimize-fin` | Parameter sweep over fin geometry -> Best configuration | Optimizer workflow |
| `forced-conv-sim` | Hydraulic OP -> Fin Rth -> Temp distribution -> Results | SoftwareTermico single simulation |
| `multi-sim` | Parametric geometry sweep -> Best configuration per thermal limit | SoftwareTermico multi simulation |
| `cspi-sweep` | Sweep fan diameter/material -> CSPI vs parameters plot data | CSPI parametric study (Drofenik Fig.4/5) |

### Configuration

Scenario configs are `.m` files returning a struct:

```matlab
% configs/scenario_to247_u90.m
function cfg = scenario_to247_u90()
    cfg.heatsink.type = 'extruded';
    cfg.heatsink.ref = 'HS_EX_001';
    cfg.fluid.type = 'H2OGly50';
    cfg.fluid.flowrate = 5e-3;          % m^3/s
    cfg.heating.numComponents = 1;
    cfg.heating.pLoss = 50;             % W
    cfg.heating.areaContact = 1.5e-4;   % m^2
    cfg.tim.thickness = 0.329e-3;       % m
    cfg.tim.conductivity = 1.0;         % W/(m*K)
end
```

CLI flags override config values: `--fluid.flowrate 0.01`.

## SoftwareTermico Refactoring

### Unit Conversion

All dimensions converted from mm to m at the interface level. Internal functions adapted:

| Current (mm) | Target (m) | Variables affected |
|--------------|------------|-------------------|
| `a`, `b` (heatsink dims) | Divide by 1000 | Dati.m, Simulazione_*.m |
| `a_n`, `b_n` (source dims) | Divide by 1000 | Dati.m |
| `x_g`, `y_g` (positions) | Divide by 1000 | Dati.m |
| `tb`, `Hf`, `tf`, `bch` | Divide by 1000 | HS_Type.m outputs |

### Variable Renaming

Key renames (Italian -> English):

| Current | Target | Meaning |
|---------|--------|---------|
| `alette/Nf` | `numFins` | Number of fins |
| `dissipatore` | `heatsink` | Heatsink |
| `ventilatore/Nv` | `numFans` | Number of fans |
| `portata/Qv` | `flowRate` | Volumetric flow rate |
| `sorgenti` | `sources` | Heat sources |
| `Simulazione_Singola` | `single_simulation` | Single simulation |
| `Simulazione_Multipla` | `multi_simulation` | Multi simulation |

### Menu Replacement

All `menu()` calls replaced by config struct fields:

| Current menu | Config field |
|-------------|-------------|
| Heatsink profile selection | `cfg.heatsink.profile` (string, e.g. `'I117'`) |
| Fan model selection | `cfg.fan.model` (string, e.g. `'EBM208_axial_AC'`) |
| Ventilation type | `cfg.ventilation.type` (`'push'` or `'impinge'`) |
| Number of fans | `cfg.fan.count` (integer) |

## Test Suite

### Structure

```
tests/
  run_tests.m              # Test runner: discovers and runs all test_*.m
  test_formula.m           # Tests for Formula/ functions
  test_thermal_layer.m     # Tests for ThermalLayer/ThermalLayerStack
  test_thermal_model_semi.m # Tests for ThermalModelSemi pipeline
  test_heatsink_model.m    # Tests for extrudedFinModel
  test_fluid_properties.m  # Tests for GasProperty/LiquidProperty
  test_hydraulic.m         # Tests for idraulico/Rth_fin
  test_temp_distribution.m # Tests for Tplane_dist/Temp_calc
  test_air_properties.m    # Tests for Coeff_Aria functions
```

### Test Types

1. **Literature verification**: Compare formula outputs against published textbook/paper values
2. **Regression tests**: Capture known-good outputs from existing scripts as golden values
3. **Consistency checks**: Cross-check between modules (e.g., ThermalLayer vs ThermalLayerStack for single layer)

### Literature References (Proposed, Pending User Validation)

| Function | Reference | Test case |
|----------|-----------|-----------|
| `finEfficiency` | Incropera & DeWitt, "Fundamentals of Heat and Mass Transfer", Table 3.5 | Rectangular fin, known mL values -> known eta |
| `ThermalLayer.thermalLayerResistance` (spreading) | Lee et al., "Constriction/Spreading Resistance Model for Electronics Packaging" (1995) | Table 1 reference cases |
| `heatTransferParallelPlanesRadiation` | Incropera, Ch. 13 | Two parallel black bodies at known T |
| `Rth_fin` (Nusselt correlations) | Kays & London, "Compact Heat Exchangers" | Known Re/Nu for rectangular channels |
| `Temp_calc` (Fourier spreading) | Yovanovich, "Thermal Spreading and Contact Resistances" (2005) | Rectangular source on finite plate |
| Air properties (rho, Cp, mu, Kt) | Engineering Toolbox / Incropera Appendix A | Values at 20C, 50C, 100C |

## Success Criteria

1. `octave thermal_cli.m <command> --help` prints usage for every command
2. `octave thermal_cli.m <workflow> --config <file>` runs end-to-end without interactive prompts
3. `octave tests/run_tests.m` runs all tests, reports pass/fail, exits with 0 on all-pass
4. Every Formula/ function has at least one literature-verified test case
5. Every workflow has at least one regression test with golden values
6. No `menu()` calls remain in code paths reachable from the CLI
7. No Windows paths (`W:\`) remain in code paths reachable from the CLI
8. SoftwareTermico code reachable from CLI uses SI units (m, K, W)

## Constraints

- Pure Octave — no Python, no external packages beyond what ships with Octave
- Excel databases stay as .xlsx (Python loader is a separate future project)
- FEMM validation stays manual
- `LossTemperatureInteraction/` excluded until `SVM_7()` dependency is resolved
- GUI (`prova_grafica.m`) untouched, kept as optional separate tool
