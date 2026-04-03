# Phase 4: Remaining Workflows + Database Path Fix

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix hardcoded `W:\` database paths so OOP classes work on WSL, then implement the extruded-fin workflow and optimize-fin workflow. Multi-sim is deferred (too complex for this phase).

**Architecture:** Replace hardcoded `W:\Technology\Functions\Thermal\db\` paths with a path resolution function that finds `db/` relative to the project root. This unblocks `GasProperty`, `LiquidProperty`, `heatsinkFactory`, and `extrudedFinModel` on WSL.

**Design spec:** `docs/superpowers/specs/2026-04-03-cli-unification-design.md`

---

### Task 1: Fix database paths for WSL compatibility

**Files:**
- Create: `lib/thermal_db_path.m` — resolves db/ path relative to project root
- Modify: `mfiles/Thermal/Model/GasProperty.m` — fix xlsread path
- Modify: `mfiles/Thermal/Model/LiquidProperty.m` — fix xlsread path
- Modify: `mfiles/Thermal/Model/heatsinkFactory.m` — fix xlsread path
- Modify: `mfiles/Thermal/Model/extrudedFinModel.m` — fix xlsread path
- Modify: `mfiles/Thermal/Model/HeatsinkGenericClass.m` — fix xlsread path

All 6 files reference `'W:\Technology\Functions\Thermal\db\...'`. Replace with a call to `thermal_db_path()` which returns the correct local path.

- [ ] **Step 1: Create `lib/thermal_db_path.m`**

```matlab
function db_dir = thermal_db_path()
    % thermal_db_path - returns absolute path to the db/ directory
    % Searches upward from the current file location for a directory
    % containing 'db/FluidData.xlsx'.

    % Try relative to this file (lib/ -> project root -> db/)
    this_dir = fileparts(mfilename('fullpath'));
    candidate = fullfile(this_dir, '..', 'db');
    if exist(fullfile(candidate, 'FluidData.xlsx'), 'file')
        db_dir = candidate;
        return;
    end

    % Try relative to pwd
    candidate = fullfile(pwd, 'db');
    if exist(fullfile(candidate, 'FluidData.xlsx'), 'file')
        db_dir = candidate;
        return;
    end

    error('thermal_db_path: cannot find db/ directory with FluidData.xlsx');
end
```

- [ ] **Step 2: Fix GasProperty.m**

In `mfiles/Thermal/Model/GasProperty.m`, change the xlsread line from:
```matlab
[~,~,obj.raw] = xlsread('W:\Technology\Functions\Thermal\db\FluidData.xlsx',...
```
to:
```matlab
pkg load io;
[~,~,obj.raw] = xlsread(fullfile(thermal_db_path(), 'FluidData.xlsx'),...
```

- [ ] **Step 3: Fix LiquidProperty.m**

Same pattern as GasProperty.m — replace the `W:\` path with `thermal_db_path()`.

- [ ] **Step 4: Fix heatsinkFactory.m**

Change:
```matlab
[~,~,raw] = xlsread('W:\Technology\Functions\Thermal\db\heatsinks.xlsx',...
```
to:
```matlab
pkg load io;
[~,~,raw] = xlsread(fullfile(thermal_db_path(), 'heatsinks.xlsx'),...
```

- [ ] **Step 5: Fix extrudedFinModel.m**

Same pattern — replace `W:\...\heatsinks.xlsx` with `thermal_db_path()`.

- [ ] **Step 6: Fix HeatsinkGenericClass.m**

Same pattern.

- [ ] **Step 7: Write test**

Create `tests/test_fluid_properties.m`:

```matlab
function results = test_fluid_properties()
    results = {};

    pkg load io;

    % Test 1: GasProperty airDry loads
    r.name = 'GasProperty: airDry loads';
    try
        gas = GasProperty('airDry');
        r.pass = ~isempty(gas.fluidData);
        r.detail = 'GasProperty created successfully';
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 2: airDry density at 300K (27C)
    r.name = 'GasProperty: airDry density at 300K';
    try
        rho = gas.calcDensity(300);
        r.pass = assert_near(rho, 1.177, 0.05, r.name);
        r.detail = sprintf('got %.4f, expected ~1.177 kg/m3', rho);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 3: LiquidProperty H2OGly50 loads
    r.name = 'LiquidProperty: H2OGly50 loads';
    try
        liq = LiquidProperty('H2OGly50');
        r.pass = ~isempty(liq.fluidData);
        r.detail = 'LiquidProperty created successfully';
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 4: H2OGly50 density at 320K
    r.name = 'LiquidProperty: H2OGly50 density at 320K';
    try
        rho = liq.calcDensity(320);
        r.pass = rho > 900 && rho < 1200;
        r.detail = sprintf('got %.1f kg/m3', rho);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;
end
```

- [ ] **Step 8: Run tests**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui tests/run_tests.m
```

Expected: test_fluid_properties ... 4/4 PASS

- [ ] **Step 9: Commit**

```bash
git add lib/thermal_db_path.m mfiles/Thermal/Model/GasProperty.m mfiles/Thermal/Model/LiquidProperty.m mfiles/Thermal/Model/heatsinkFactory.m mfiles/Thermal/Model/extrudedFinModel.m mfiles/Thermal/Model/HeatsinkGenericClass.m tests/test_fluid_properties.m
git commit -m "fix: replace hardcoded W:\\ database paths with local db/ resolution

Add thermal_db_path() to find db/ directory relative to project root.
All Model/ classes now work on WSL/Linux without Windows network paths.
Add fluid property tests verifying xlsx loading works."
```

---

### Task 2: Implement workflow_extruded_fin

**Files:**
- Create: `lib/workflow_extruded_fin.m`
- Create: `configs/example_extruded_fin.m`
- Modify: `thermal_cli.m` (add case)

- [ ] **Step 1: Write `configs/example_extruded_fin.m`**

```matlab
function cfg = example_extruded_fin()
    % Example: extruded fin heatsink thermal analysis
    % Based on Optimizer/extrudedFinHeatsinkCalculations.m

    % Heatsink geometry (direct, not from DB)
    cfg.heatsink.rhoSink = 2698.9;        % [kg/m3]
    cfg.heatsink.kSink = 180;             % [W/(m*K)]
    cfg.heatsink.specHeat = 880;          % [J/(kg*K)]
    cfg.heatsink.thickHeatsink = 5e-3;    % [m]
    cfg.heatsink.thickWall = 0.8e-3;      % [m]
    cfg.heatsink.widthChannel = 1.05e-3;  % [m]
    cfg.heatsink.numBridge = 0;
    cfg.heatsink.heightTotal = 21e-3;     % [m] total profile height (for numChannel calc)

    % Fluid
    cfg.fluid.type = 'H2OGly50';
    cfg.fluid.flowrate = 1.0 / 1000 / 60; % 1 L/min -> m3/s
    cfg.fluid.tInlet = 343.15;            % [K] (70C)

    % Heating arrangement
    cfg.heating.widthContact = 16.9e-3;   % [m]
    cfg.heating.lengthContact = 13.7e-3;  % [m]
    cfg.heating.numHeatedSides = 1;
    cfg.heating.maxDissLength = 21e-3;    % [m]
    cfg.heating.numInSeries = 1;
    cfg.heating.spacing = 0;              % [m]
    cfg.heating.pLoss = 100;              % [W]
end
```

- [ ] **Step 2: Write `lib/workflow_extruded_fin.m`**

```matlab
function result = workflow_extruded_fin(parsed)
    % workflow_extruded_fin - extruded fin heatsink thermal analysis
    % Usage: thermal_cli.m extruded-fin --config <file>

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m extruded-fin --config <file>\n');
        fprintf('Runs extruded fin heatsink thermal analysis.\n');
        result = struct();
        return;
    end

    pkg load io;
    cfg = cli_load_config(parsed);

    fprintf('--- Extruded Fin Heatsink Analysis ---\n');

    % Create heatsink
    numChannel = ceil((cfg.heatsink.heightTotal - cfg.heatsink.thickWall) / ...
        (cfg.heatsink.widthChannel + cfg.heatsink.thickWall));

    heatsink = extrudedFinModel(...
        cfg.heatsink.rhoSink, ...
        cfg.heatsink.kSink, ...
        cfg.heatsink.specHeat, ...
        numChannel, ...
        cfg.heatsink.thickHeatsink, ...
        cfg.heatsink.thickWall, ...
        cfg.heatsink.widthChannel, ...
        cfg.heatsink.numBridge);

    fprintf('num_channels=%d\n', numChannel);

    % Define fluid
    heatsink.defineFluid(cfg.fluid.type);
    heatsink.TFluidIn = cfg.fluid.tInlet;
    heatsink.flowrate = cfg.fluid.flowrate;

    % Define heating arrangement
    heatsink.defineHeatingArrangement(...
        cfg.heating.widthContact, ...
        cfg.heating.lengthContact, ...
        cfg.heating.numHeatedSides, ...
        cfg.heating.maxDissLength, ...
        cfg.heating.numInSeries, ...
        cfg.heating.spacing);

    heatsink.pLossComponent = cfg.heating.pLoss;

    % Calculate thermal resistance
    heatsink.thermalResistance();

    % Output results
    fprintf('rth_tot=%.6f\n', heatsink.rThTot);
    fprintf('rth_fluid_flow=%.6f\n', heatsink.rThFluidFlow);
    fprintf('reynolds=%.1f\n', heatsink.Re);
    fprintf('v_fluid=%.4f\n', heatsink.vFluid);

    for i = 1:length(heatsink.TContact)
        fprintf('t_contact_%d=%.2f\n', i, heatsink.TContact(i));
        fprintf('t_wall_%d=%.2f\n', i, heatsink.TWall(i));
        fprintf('t_fluid_mean_%d=%.2f\n', i, heatsink.TFluidLocMean(i));
    end

    result.rThTot = heatsink.rThTot;
    result.rThFluidFlow = heatsink.rThFluidFlow;
    result.Re = heatsink.Re;
    result.vFluid = heatsink.vFluid;
    result.TContact = heatsink.TContact;

    % CSV export
    if isfield(parsed, 'save_csv')
        fid = fopen(parsed.save_csv, 'w');
        fprintf(fid, 'point,value,unit\n');
        fprintf(fid, 'rth_tot,%.6f,K/W\n', heatsink.rThTot);
        fprintf(fid, 'rth_fluid_flow,%.6f,K/W\n', heatsink.rThFluidFlow);
        fprintf(fid, 'reynolds,%.1f,-\n', heatsink.Re);
        for i = 1:length(heatsink.TContact)
            fprintf(fid, 't_contact_%d,%.2f,K\n', i, heatsink.TContact(i));
        end
        fclose(fid);
        fprintf('Results saved to: %s\n', parsed.save_csv);
    end

    fprintf('--- Complete ---\n');
end
```

- [ ] **Step 3: Add dispatcher case**

```matlab
        case 'extruded-fin'
            workflow_extruded_fin(parsed);
```

- [ ] **Step 4: Test**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m extruded-fin --config configs/example_extruded_fin.m
```

- [ ] **Step 5: Commit**

```bash
git add lib/workflow_extruded_fin.m configs/example_extruded_fin.m thermal_cli.m
git commit -m "feat: add extruded-fin workflow with liquid cooling analysis"
```

---

### Task 3: Final integration test

- [ ] **Step 1: Run full test suite**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui tests/run_tests.m
```

Expected: ~44 tests pass (40 + 4 fluid properties).

- [ ] **Step 2: Test all workflows end-to-end**

```bash
octave --no-gui thermal_cli.m semi-on-pcb --config configs/example_semi_on_pcb.m
octave --no-gui thermal_cli.m forced-conv-sim --config configs/example_forced_conv.m
octave --no-gui thermal_cli.m extruded-fin --config configs/example_extruded_fin.m
```

---

## Summary

After Phase 4:
- **Database path fix** — all OOP Model/ classes work on WSL
- **4 new tests** for fluid properties (GasProperty + LiquidProperty)
- **1 new workflow:** `extruded-fin`
- **Total: ~44 tests**
- **Workflows: 3** (semi-on-pcb, forced-conv-sim, extruded-fin)

**Deferred:**
- `workflow_multi_sim` — too complex (6-level nested loop with heatsink resizing), needs dedicated design
- `workflow_optimize_fin` — depends on multi-sim infrastructure or can be a simpler parametric sweep
