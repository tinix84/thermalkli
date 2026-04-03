# Design Spec: Thermal Toolbox CLI Unification

**Date**: 2026-04-03
**Status**: Approved
**PRD**: `docs/prd.md`

## 1. Architecture: Flat Command Functions (Approach A)

Single `thermal_cli.m` dispatcher routes to `cmd_*.m` command functions and `workflow_*.m` workflow functions in a `lib/` directory. No registry, no namespace packages.

### Project Layout

```
thermal_cli.m                         # Entry point: parses argv, dispatches
lib/
  cli_parse_args.m                    # '--key value' -> struct (dots become underscores)
  cli_load_config.m                   # Load .m config, merge CLI overrides
  cli_print_help.m                    # Help printer for commands and workflows

  # --- Standalone commands ---
  cmd_calc_rth.m                      # Rth from P, Tref, Tmeas
  cmd_fin_efficiency.m                # Fin efficiency (tanh model)
  cmd_radiation.m                     # 5 radiation formulas (--mode flag)
  cmd_layer_rth.m                     # Single layer Rth with spreading
  cmd_stack_rth.m                     # Layer stack Rth
  cmd_heatsink_create.m              # Create heatsink from DB ref
  cmd_heatsink_rth.m                 # Extruded fin heatsink Rth
  cmd_free_conv.m                    # Free convection surface temperature
  cmd_water_cooling.m                # Water cooling analysis
  cmd_hydraulic_op.m                 # Fan-heatsink hydraulic operating point
  cmd_fin_rth.m                      # Finned heatsink Rth (SoftwareTermico)
  cmd_temp_dist.m                    # Temperature distribution on plane
  cmd_gen_femm.m                     # Generate FEMM Lua script (--model flag)
  cmd_compare_femm.m                 # Compare FEMM CSV vs analytical CSV

  # --- FEMM Lua generators ---
  femm_semi_on_pcb.m                 # Axisymmetric PCB+semi model
  femm_extruded_fin.m                # 2D planar fin cross-section
  femm_baseplate_spreading.m         # 2D planar baseplate with sources

  # --- Predefined workflows ---
  workflow_semi_on_pcb.m             # ThermalModelSemi full pipeline
  workflow_extruded_fin.m            # Extruded fin design pipeline
  workflow_optimize_fin.m            # Parametric fin optimization
  workflow_forced_conv_sim.m         # SoftwareTermico single simulation
  workflow_multi_sim.m               # SoftwareTermico multi simulation

configs/
  example_to247_u90.m                # Example: TO247 with U90 connector
  example_forced_conv.m              # Example: forced convection simulation

tests/
  run_tests.m                        # Test runner
  assert_near.m                      # Assertion helper
  test_formula.m                     # Formula/ function tests
  test_thermal_layer.m               # ThermalLayer/Stack tests
  test_thermal_model_semi.m          # ThermalModelSemi pipeline tests
  test_heatsink_model.m              # extrudedFinModel tests
  test_fluid_properties.m            # GasProperty/LiquidProperty tests
  test_air_properties.m              # Coeff_Aria function tests
  test_hydraulic.m                   # idraulico/Rth_fin tests
  test_temp_distribution.m           # Temp_calc/Tplane_dist tests

mfiles/                              # Existing code
  Thermal/                           # Wrapped (not modified), called by cmd_*
  SoftwareTermico/                   # Refactored in-place (SI+English)
  archive/                           # Moved originals (Dati.m, Dati_multipla.m, etc.)

db/                                  # Existing xlsx databases (unchanged)
docs/
  prd.md
  superpowers/specs/                 # This file
```

## 2. CLI Dispatcher

`thermal_cli.m` is the single entry point:

```matlab
function thermal_cli()
    addpath('lib');
    addpath(genpath('mfiles'));

    args = argv();
    if isempty(args) || strcmp(args{1}, '--help') || strcmp(args{1}, '-h')
        cli_print_help(); return;
    end

    command = args{1};
    rest = args(2:end);
    parsed = cli_parse_args(rest);

    switch command
        case 'calc-rth',           cmd_calc_rth(parsed);
        case 'fin-efficiency',     cmd_fin_efficiency(parsed);
        case 'radiation',          cmd_radiation(parsed);
        case 'layer-rth',          cmd_layer_rth(parsed);
        case 'stack-rth',          cmd_stack_rth(parsed);
        case 'heatsink-create',    cmd_heatsink_create(parsed);
        case 'heatsink-rth',       cmd_heatsink_rth(parsed);
        case 'free-conv',          cmd_free_conv(parsed);
        case 'water-cooling',      cmd_water_cooling(parsed);
        case 'hydraulic-op',       cmd_hydraulic_op(parsed);
        case 'fin-rth',            cmd_fin_rth(parsed);
        case 'temp-dist',          cmd_temp_dist(parsed);
        case 'semi-on-pcb',        workflow_semi_on_pcb(parsed);
        case 'extruded-fin',       workflow_extruded_fin(parsed);
        case 'optimize-fin',       workflow_optimize_fin(parsed);
        case 'forced-conv-sim',    workflow_forced_conv_sim(parsed);
        case 'multi-sim',          workflow_multi_sim(parsed);
        case 'gen-femm',           cmd_gen_femm(parsed);
        case 'compare-femm',       cmd_compare_femm(parsed);
        otherwise
            fprintf(2, 'Unknown command: %s\n', command);
            cli_print_help();
            exit(1);
    end
end
```

Invocation:
```bash
octave thermal_cli.m calc-rth --power 50 --tref 300 --tmeas 350
octave thermal_cli.m semi-on-pcb --config configs/example_to247_u90.m
octave thermal_cli.m radiation --mode parallel --t1 500 --t2 300 --area 0.01 --eps1 0.8 --eps2 0.9
# --mode is required: parallel|cylinder|sphere|enclosure|convex. Error if missing.
```

## 3. Shared Utilities

### cli_parse_args.m

Converts `{'--key', 'value', '--flag'}` to struct. Rules:
- `--key value` -> `parsed.key = 'value'` (string)
- `--key.sub value` -> `parsed.key_sub = 'value'` (dot to underscore)
- `--flag` (no value, next arg starts with `--`) -> `parsed.flag = true`
- `--help` -> `parsed.help = true`

Each `cmd_*` is responsible for type conversion (`str2double`, etc.).

### cli_load_config.m

```matlab
function cfg = cli_load_config(parsed)
    if isfield(parsed, 'config')
        [dir, name, ~] = fileparts(parsed.config);
        if ~isempty(dir), addpath(dir); end
        cfg = feval(name);
    else
        cfg = struct();
    end
    cfg = merge_overrides(cfg, parsed);
end
```

Override logic: `--fluid.flowrate 0.01` sets `cfg.fluid.flowrate = 0.01`. Nested struct fields created if they don't exist.

### cli_print_help.m

Prints command list with one-line descriptions. When called with a command name, prints that command's usage and options.

## 4. Command Interface Contract

Every `cmd_*.m` function:

1. **Signature**: `function result = cmd_name(parsed)` where `parsed` is the struct from `cli_parse_args`
2. **Help**: If `parsed.help` is true, print usage and return empty
3. **Config**: If the command supports `--config`, load it via `cli_load_config`
4. **Compute**: Call the underlying classes/functions from `mfiles/`
5. **Output**: Print results as `key=value\n` lines to stdout (machine-parseable)
6. **Return**: Return result as struct (for workflow chaining)

Example pattern:

```matlab
function result = cmd_fin_efficiency(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m fin-efficiency --length <m> --h <W/m2K> --area <m2> --k <W/mK> --ac <m2>\n');
        fprintf('Calculates fin efficiency using tanh(mL)/mL formula.\n');
        result = struct(); return;
    end

    L  = str2double(parsed.length);
    h  = str2double(parsed.h);
    A  = str2double(parsed.area);
    k  = str2double(parsed.k);
    Ac = str2double(parsed.ac);

    eta = finEfficieny(L, h, A, k, Ac);

    result.eta = eta;
    fprintf('eta=%.6f\n', eta);
end
```

## 5. Workflow Design

Workflows call `cmd_*` functions in sequence, piping result structs.

### workflow_semi_on_pcb.m

Full ThermalModelSemi pipeline:
1. Load config
2. Build `ThermalModelSemiInput` from config fields
3. Create `ThermalModelSemi` object
4. Call appropriate calc methods based on what's specified (Rth, Tjunction, PMax, etc.)
5. Print results

### workflow_extruded_fin.m

1. Load config
2. `cmd_heatsink_create` or build `extrudedFinModel` from geometry
3. Define fluid properties
4. Define heating arrangement
5. `cmd_heatsink_rth` to compute thermal resistance
6. Print results including Rth breakdown and temperatures

### workflow_forced_conv_sim.m

Replaces `Simulazione_Singola.m`:
1. Load config (replaces `Dati.m` + `menu()` calls)
2. `cmd_hydraulic_op` — find fan operating point
3. `cmd_fin_rth` — compute fin thermal resistance
4. `cmd_temp_dist` — compute temperature distribution
5. Print results (peak temperature, temperature map)

### workflow_multi_sim.m

Replaces `Simulazione_Multipla.m`:
1. Load config with parameter sweep ranges
2. Loop over geometry variations
3. For each: run `workflow_forced_conv_sim` pipeline
4. Collect results, find optimal configuration
5. Print summary table

### workflow_optimize_fin.m

Replaces `Optimizer/extrudedFinHeatsinkCalculations.m`:
1. Load config with sweep parameters
2. Loop over fin thickness / channel depth grid
3. For each: compute heatsink Rth
4. Find minimum Rth configuration
5. Print optimal geometry + Rth

## 6. Config File Format

Each config is a `.m` function returning a struct:

```matlab
% configs/example_to247_u90.m
function cfg = example_to247_u90()
    % Heatsink
    cfg.heatsink.type = 'extruded';
    cfg.heatsink.ref = 'HS_EX_001';              % DB reference
    cfg.heatsink.heightHeatsink = 22e-3;          % [m]
    cfg.heatsink.thickHeatsink = 10e-3;           % [m]
    cfg.heatsink.thickWall = 0.8e-3;              % [m]
    cfg.heatsink.thickFin = 0.8e-3;               % [m]
    cfg.heatsink.widthChannel = 1.05e-3;          % [m]
    cfg.heatsink.kProfile = 190;                  % [W/(m*K)]

    % Fluid
    cfg.fluid.type = 'H2OGly50';
    cfg.fluid.flowrate = 5e-3;                    % [m^3/s]
    cfg.fluid.tInlet = 298.15;                    % [K]

    % Component
    cfg.component.numInSeries = 1;
    cfg.component.pLoss = 50;                     % [W]
    cfg.component.areaContact = 1.5e-4;           % [m^2]
    cfg.component.rThJC = 0.5;                    % [K/W]

    % TIM
    cfg.tim.thickness = 0.329e-3;                 % [m]
    cfg.tim.conductivity = 1.0;                   % [W/(m*K)]
end
```

```matlab
% configs/example_forced_conv.m
function cfg = example_forced_conv()
    % Heatsink geometry
    cfg.heatsink.profile = 'I117';                % DB lookup in HS_Type
    cfg.heatsink.width = 0.65;                    % [m] (was 650mm)
    cfg.heatsink.length = 0.33;                   % [m] (was 330mm)
    cfg.heatsink.material = 'all_aluminum';

    % Fan
    cfg.fan.model = 'EBMW2E200_axial_AC_50Hz';
    cfg.fan.count = 2;

    % Ventilation
    cfg.ventilation.type = 'push';                % 'push' or 'impinge'
    cfg.ventilation.impingeOpening = 0.22;        % [m] (only for impinge)

    % Ambient
    cfg.ambient.tInlet = 313.15;                  % [K] (40C)

    % Heat sources (arrays)
    cfg.sources.width  = [0.013 0.013 0.013 0.013 0.013];  % [m]
    cfg.sources.length = [0.013 0.013 0.013 0.013 0.013];  % [m]
    cfg.sources.power  = [0.1 30 30 30 30];                 % [W]
    cfg.sources.x      = [0.0165 0.0165 0.0165 0.0165 0.0165]; % [m]
    cfg.sources.y      = [0.119 0.094 0.0715 0.035 0.013];     % [m]
end
```

## 7. SoftwareTermico Refactoring

### Strategy

- **Wrap Thermal/ OOP code** — new `cmd_*` functions call existing classes. No changes to class files.
- **Refactor SoftwareTermico/ in-place** — modify function signatures, units, variable names.
- **Archive originals** — move `Dati.m`, `Dati(originale).m`, `Dati_multipla.m` to `mfiles/archive/`.

### Unit Conversion

Conversion happens at the database lookup boundary (HS_Type, HS_Tech) and config loading. Internal physics calculations already use consistent units within each function.

**HS_Type.m**: Add `* 1e-3` to all returned dimensions (tb, Hf, tf, bch are currently in mm).

**Simulation functions**: Change signatures from workspace-variable-dependent scripts to `function result = single_simulation(cfg)`. The config struct provides all values in SI.

### Variable Renames (in refactored files)

| Old | New | Where |
|-----|-----|-------|
| `a`, `b` | `heatsinkWidth`, `heatsinkLength` | Simulation entry points |
| `a_n`, `b_n` | `sourceWidth`, `sourceLength` | Source definitions |
| `p_n` | `sourcePower` | Source definitions |
| `x_g`, `y_g` | `sourceX`, `sourceY` | Source positions |
| `Nf` | `numFins` | Geometry calcs |
| `Nv` | `numFans` | Fan setup |
| `Qv` | `flowRate` | Hydraulic calcs |
| `Hv` | `fanPressure` | Hydraulic calcs |
| `tb` | `baseThickness` | Heatsink geometry |
| `Hf` | `finHeight` | Heatsink geometry |
| `tf` | `finThickness` | Heatsink geometry |
| `bch` | `channelWidth` | Heatsink geometry |
| `Ths` | `tempGrid` | Temperature results |
| `Th_BP` | `tempBaseplate` | Temperature results |

### Menu Elimination

Every `menu()` call maps to a config field (documented in PRD Section "Menu Replacement"). The refactored functions read from the config struct instead of prompting.

## 8. Test Suite

### Test Runner (tests/run_tests.m)

```matlab
function run_tests()
    addpath('..');                    % thermal_cli.m
    addpath('../lib');
    addpath(genpath('../mfiles'));

    test_files = glob('test_*.m');
    total_pass = 0; total_fail = 0; total_error = 0;

    for i = 1:length(test_files)
        [~, name, ~] = fileparts(test_files{i});
        fprintf('Running %s ...', name);
        try
            results = feval(name);
            pass = sum(cellfun(@(r) r.pass, results));
            fail = length(results) - pass;
            fprintf(' %d/%d PASS\n', pass, length(results));
            total_pass += pass;
            total_fail += fail;
        catch e
            fprintf(' ERROR: %s\n', e.message);
            total_error += 1;
        end
    end

    fprintf('\nTOTAL: %d pass, %d fail, %d error\n', total_pass, total_fail, total_error);
    if total_fail > 0 || total_error > 0
        exit(1);
    end
end
```

### Literature References for Tests

| Test | Function | Reference | Expected Value | Tolerance |
|------|----------|-----------|---------------|-----------|
| Fin efficiency at mL=0.5 | `finEfficieny` | Incropera 7th ed, Table 3.5 | eta = 0.9242 | 0.5% |
| Fin efficiency at mL=2.0 | `finEfficieny` | Incropera 7th ed, Table 3.5 | eta = 0.4621 | 0.5% |
| Parallel plane radiation (T1=500K, T2=300K, A=1m2, eps=1) | `heatTransferParallelPlanesRadiation` | Stefan-Boltzmann: sigma*(T1^4-T2^4)*A = 2486 W | 2486 W | 1 W |
| Spreading resistance (eps=0.1, tau=1, Bi=1) | `ThermalLayer.thermalLayerResistance` | Lee et al. 1995, Fig. 3 | psi ~ 0.35 | 5% |
| Air density at 20C | `rho_air` | Engineering Toolbox | 1.204 kg/m3 | 0.5% |
| Air density at 100C | `rho_air` | Engineering Toolbox | 0.946 kg/m3 | 0.5% |
| Air Cp at 50C | `Cp_air` | Engineering Toolbox | 1007 J/(kg*K) | 0.5% |
| Air viscosity at 20C | `mu_air` | Engineering Toolbox | 1.825e-5 Pa*s | 1% |
| Air conductivity at 20C | `Kt_air` | Engineering Toolbox | 0.02514 W/(m*K) | 1% |

### Regression Tests

Capture golden values by running existing scripts once and recording outputs:

| Test | Script Source | Values to capture |
|------|-------------|-------------------|
| ThermalModelSemi pathCase 1 | `Designer/testScript.m` | rThCaseFluidBot, tJunction |
| ThermalModelSemi pathCase 3 | `Designer/testScript.m` (modified) | rThCaseFluidBot, tJunction |
| CSC128 module | `Designer/CSC128_thermalCalculation.m` | rThCaseFluidBot, tJunction |
| TO247+U90 Rth | `Designer/TO247Plus_U90_extrudedFinHeatsinkCalculations.m` | rThTot |
| Extruded fin Rth | `Designer/extrudedFinHeatsinkCalculations.m` | rThHF, rThCF |
| FEMM comparison | `Verifier/comparisonWithFEMM/testScript.m` | rThCaseFluidBot, tJunction |
| Spreading investigation | `Designer/spreadingInvestigation.m` | rThJFArrTot at specific points |

## 9. FEMM Lua Script Generation

### Overview

Three Lua generators produce FEMM heat-problem scripts from the same config structs used by the analytical CLI commands. Each script builds geometry, assigns materials/BCs, solves, and extracts results to CSV. The user runs the Lua script manually in FEMM.

### Generators

| Generator | FEMM problem type | Geometry | Source model |
|-----------|------------------|----------|-------------|
| `femm_semi_on_pcb.m` | Axisymmetric (`"axi"`) | Multi-layer PCB stack with via region, heatsink slab. Circular-equivalent areas. | Existing `semiHeatflow.lua` pattern |
| `femm_extruded_fin.m` | Planar 2D (`"planar"`) | Cross-section of fin channel: base plate, fin, channel walls. Convection BC on channel walls, heat flux on base. | New |
| `femm_baseplate_spreading.m` | Planar 2D (`"planar"`) | Rectangular baseplate with rectangular heat source(s). Convection BC on bottom face. | New |

### FEMM Lua API Used

All generators use FEMM's heat problem API (`hi_*` / `ho_*`):

```lua
-- Problem setup
newdocument(2)                              -- 2 = heat problem
hi_probdef("meters", "axi"|"planar", ...)   -- units, problem type

-- Materials
hi_addmaterial(name, kx, ky, qv)            -- thermal conductivity, volumetric heat gen

-- Boundary conditions
hi_addboundprop(name, type, ...)
-- type 0: fixed temperature
-- type 1: heat flux
-- type 2: convection (h, T_ambient)

-- Geometry
hi_addnode(x, y)
hi_addsegment(x1, y1, x2, y2)
hi_addblocklabel(x, y)
hi_setblockprop(material, ...)
hi_setsegmentprop(boundary, ...)

-- Solve
hi_saveas("model.feh")
hi_analyze()
hi_loadsolution()

-- Post-processing (extract to CSV)
ho_getpointvalues(x, y)                    -- returns temperature at point
ho_blockintegral(0)                         -- average temperature in block
```

### Generated Lua Script Structure

Each generator outputs a `.lua` file with this structure:

```lua
-- Auto-generated by thermal_cli.m gen-femm
-- Model: semi-on-pcb
-- Config: configs/example_to247_u90.m
-- Date: 2026-04-03

-- 1. Problem definition
newdocument(2)
hi_probdef("meters", "axi", 1e-8, 20, 30)

-- 2. Materials (from config layer stack)
hi_addmaterial("Cu", 400, 400, 0)
hi_addmaterial("Fr4", 0.3, 0.3, 0)
-- ... generated from cfg.pcbLayerStack / cfg.heatsink

-- 3. Boundary conditions (from config)
hi_addboundprop("heatSource", 1, 0, -q)        -- heat flux from power/area
hi_addboundprop("convection", 2, 0, 0, T_fluid, h_fluid)

-- 4. Geometry (computed from layer thicknesses, areas)
-- ... nodes and segments generated programmatically

-- 5. Material & BC assignment
-- ... block labels and segment properties

-- 6. Solve
hi_saveas("semi_on_pcb_model.feh")
hi_analyze()
hi_loadsolution()

-- 7. Extract results to CSV
f = openfile("femm_results.csv", "w")
write(f, "point,x,y,temperature\n")
-- Extract temperature at junction (top center)
T_junction = ho_getpointvalues(0, 0)
write(f, string.format("junction,0,0,%.6f\n", T_junction))
-- Extract temperature at heatsink base
T_base = ho_getpointvalues(0, y_base)
write(f, string.format("base,0,%.6e,%.6f\n", y_base, T_base))
-- Extract temperature at fluid boundary
T_fluid_bc = ho_getpointvalues(0, y_fluid)
write(f, string.format("fluid_bc,0,%.6e,%.6f\n", y_fluid, T_fluid_bc))
closefile(f)
```

### Octave Generator Functions

Each generator is an Octave function that takes a config struct and returns the Lua script as a string:

```matlab
function lua_str = femm_semi_on_pcb(cfg)
    % Generates FEMM Lua script for semi-on-PCB axisymmetric model
    % cfg: same struct as workflow_semi_on_pcb uses
    %
    % Maps config to FEMM geometry:
    %   cfg.component.areaContact -> circular radius rc = sqrt(A/pi)
    %   cfg.pcbLayerStack -> layer thicknesses and materials
    %   cfg.sinkLayerStack -> heatsink layers below PCB
    %   cfg.component.pLoss / cfg.component.areaContact -> heat flux BC
    %   cfg.hFluidBottom, cfg.tempFluidBottom -> convection BC

    lua_str = '';
    lua_str = [lua_str, sprintf('-- Auto-generated: semi-on-pcb\n')];
    % ... build geometry from config
end
```

### CLI Integration

**Standalone command**:
```bash
octave thermal_cli.m gen-femm --model semi-on-pcb --config configs/example_to247_u90.m --output femm_semi.lua
octave thermal_cli.m gen-femm --model extruded-fin --config configs/example_fin.m --output femm_fin.lua
octave thermal_cli.m gen-femm --model baseplate --config configs/example_forced_conv.m --output femm_plate.lua
```

**Flag on workflows**:
```bash
octave thermal_cli.m semi-on-pcb --config configs/example_to247_u90.m --femm-lua femm_semi.lua
# Runs analytical calculation AND generates Lua script
```

**Comparison command**:
```bash
octave thermal_cli.m compare-femm --analytical semi_on_pcb_result.csv --femm femm_results.csv
# Output:
#   Point        Analytical [K]  FEMM [K]  Deviation [%]
#   junction     371.234         370.891   0.09
#   base         355.102         354.980   0.03
#   fluid_bc     343.150         343.150   0.00
```

### CSV Formats

**Analytical result CSV** (generated by `--save-csv` flag on commands):
```csv
point,value,unit
junction_temperature,371.234,K
rth_junction_fluid,1.234,K/W
rth_case_fluid,0.890,K/W
```

**FEMM result CSV** (generated by Lua post-processing):
```csv
point,x,y,temperature
junction,0,0,370.891
base,0,-1.6e-3,354.980
fluid_bc,0,-4.6e-3,343.150
```

**compare-femm** matches points by name (`junction`, `base`, `fluid_bc`) across both CSVs.

### New Files

```
lib/
  cmd_gen_femm.m               # CLI command: dispatches to appropriate generator
  cmd_compare_femm.m           # CLI command: reads two CSVs, prints comparison
  femm_semi_on_pcb.m           # Generator: axisymmetric PCB+semi model
  femm_extruded_fin.m          # Generator: 2D planar fin cross-section
  femm_baseplate_spreading.m   # Generator: 2D planar baseplate with sources
```

## 10. Implementation Order

Recommended phased approach:

**Phase 1 — Foundation** (CLI skeleton + Formula tests)
1. Create `lib/` with `cli_parse_args`, `cli_load_config`, `cli_print_help`
2. Create `thermal_cli.m` dispatcher
3. Implement `cmd_calc_rth`, `cmd_fin_efficiency`, `cmd_radiation` (simplest commands)
4. Create `tests/run_tests.m`, `assert_near.m`
5. Write `test_formula.m` with literature values

**Phase 2 — Thermal/ Commands** (wrap OOP code)
6. Implement `cmd_layer_rth`, `cmd_stack_rth`
7. Implement `cmd_heatsink_create`, `cmd_heatsink_rth`
8. Implement `cmd_free_conv`, `cmd_water_cooling`
9. Write `test_thermal_layer.m`, `test_heatsink_model.m`, `test_fluid_properties.m`
10. Implement `workflow_semi_on_pcb`, `workflow_extruded_fin`
11. Write `test_thermal_model_semi.m` with regression values

**Phase 3 — SoftwareTermico Refactoring**
12. Archive original Dati files
13. Refactor `HS_Type.m` (add SI conversion)
14. Refactor `idraulico.m`, `Rth_fin.m` signatures
15. Refactor `Temp_calc.m`, `Tplane_dist.m`
16. Refactor `Simulazione_Singola.m` -> `single_simulation(cfg)`
17. Refactor `Simulazione_Multipla.m` -> `multi_simulation(cfg)`
18. Write `test_air_properties.m`, `test_hydraulic.m`, `test_temp_distribution.m`

**Phase 4 — Workflows + Integration**
19. Implement `cmd_hydraulic_op`, `cmd_fin_rth`, `cmd_temp_dist`
20. Implement `workflow_forced_conv_sim`, `workflow_multi_sim`, `workflow_optimize_fin`
21. Create example configs
22. End-to-end integration test

**Phase 5 — FEMM Lua Generation**
23. Implement `femm_semi_on_pcb.m` (based on existing `semiHeatflow.lua` pattern)
24. Implement `cmd_gen_femm.m` and `cmd_compare_femm.m`
25. Add `--femm-lua` flag to `workflow_semi_on_pcb`
26. Implement `femm_extruded_fin.m` (2D planar fin cross-section)
27. Implement `femm_baseplate_spreading.m` (2D planar rectangular sources)
28. Add `--femm-lua` flag to `workflow_extruded_fin` and `workflow_forced_conv_sim`
29. Add `--save-csv` flag to commands for analytical result export
30. Write `test_femm_generation.m` (verify Lua syntax, correct geometry dimensions, correct BCs)

## 11. Error Handling

- Commands validate required args and print usage on missing params
- Config loading errors print which field is missing/invalid
- Underlying computation errors propagate with context (which command, which step)
- Exit code 0 = success, 1 = error
- No silent failures — every error prints to stderr
