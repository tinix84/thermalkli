# Phase 3: SoftwareTermico — Air Properties Tests + Hydraulic/Thermal CLI Commands

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add literature-verified tests for the air property functions, wrap `idraulico` and `Rth_fin` as CLI commands with SI unit conversion at boundaries, and build the `forced-conv-sim` workflow that replaces `Simulazione_Singola.m`.

**Architecture:** The existing SoftwareTermico functions internally use mm. Rather than rewriting internals (high risk, low value), CLI commands accept SI inputs (meters) and convert to mm at the call boundary, then convert outputs back. The air property functions stay as-is (they already take °C and return SI units). Database lookups (HS_Type, Fan_Model) stay unchanged.

**Design spec:** `docs/superpowers/specs/2026-04-03-cli-unification-design.md`

---

### Task 1: Add air property tests with literature values

**Files:**
- Create: `tests/test_air_properties.m`

The 4 air property functions (`rho_air`, `Cp_air`, `mu_air`, `Kt_air`) take temperature in °C and return SI values. They use spline interpolation over 4 reference points. We verify against Engineering Toolbox values.

- [ ] **Step 1: Write `tests/test_air_properties.m`**

```matlab
function results = test_air_properties()
    results = {};

    % --- rho_air: air density ---
    % Reference: Engineering Toolbox / Incropera Appendix A

    r.name = 'rho_air: density at 20C';
    rho = rho_air(20);
    r.pass = assert_near(rho, 1.204, 0.02, r.name);
    r.detail = sprintf('got %.4f, expected ~1.204 kg/m3', rho);
    results{end+1} = r;

    r.name = 'rho_air: density at 50C';
    rho = rho_air(50);
    r.pass = assert_near(rho, 1.093, 0.03, r.name);
    r.detail = sprintf('got %.4f, expected ~1.093 kg/m3', rho);
    results{end+1} = r;

    r.name = 'rho_air: density at 100C';
    rho = rho_air(100);
    r.pass = assert_near(rho, 0.946, 0.03, r.name);
    r.detail = sprintf('got %.4f, expected ~0.946 kg/m3', rho);
    results{end+1} = r;

    % --- Cp_air: specific heat ---

    r.name = 'Cp_air: specific heat at 20C';
    cp = Cp_air(20);
    r.pass = assert_near(cp, 1005, 10, r.name);
    r.detail = sprintf('got %.1f, expected ~1005 J/(kg*K)', cp);
    results{end+1} = r;

    r.name = 'Cp_air: specific heat at 50C';
    cp = Cp_air(50);
    r.pass = assert_near(cp, 1007, 10, r.name);
    r.detail = sprintf('got %.1f, expected ~1007 J/(kg*K)', cp);
    results{end+1} = r;

    % --- mu_air: dynamic viscosity ---

    r.name = 'mu_air: viscosity at 20C';
    mu = mu_air(20);
    r.pass = assert_near(mu, 1.825e-5, 2e-7, r.name);
    r.detail = sprintf('got %.4e, expected ~1.825e-5 Pa*s', mu);
    results{end+1} = r;

    r.name = 'mu_air: viscosity at 100C';
    mu = mu_air(100);
    r.pass = assert_near(mu, 2.18e-5, 3e-7, r.name);
    r.detail = sprintf('got %.4e, expected ~2.18e-5 Pa*s', mu);
    results{end+1} = r;

    % --- Kt_air: thermal conductivity ---

    r.name = 'Kt_air: conductivity at 20C';
    kt = Kt_air(20);
    r.pass = assert_near(kt, 0.0257, 0.002, r.name);
    r.detail = sprintf('got %.4f, expected ~0.0257 W/(m*K)', kt);
    results{end+1} = r;

    r.name = 'Kt_air: conductivity at 100C';
    kt = Kt_air(100);
    r.pass = assert_near(kt, 0.0308, 0.002, r.name);
    r.detail = sprintf('got %.4f, expected ~0.0308 W/(m*K)', kt);
    results{end+1} = r;
end
```

- [ ] **Step 2: Run tests**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui tests/run_tests.m
```

Expected: `test_air_properties ... 9/9 PASS`

- [ ] **Step 3: Commit**

```bash
git add tests/test_air_properties.m
git commit -m "test: add air property tests with Engineering Toolbox reference values"
```

---

### Task 2: Implement cmd_hydraulic_op (wraps idraulico)

**Files:**
- Create: `lib/cmd_hydraulic_op.m`
- Modify: `thermal_cli.m` (add case)

The existing `idraulico()` takes dimensions in mm. The CLI command accepts meters and converts.

- [ ] **Step 1: Write `lib/cmd_hydraulic_op.m`**

```matlab
function result = cmd_hydraulic_op(parsed)
    % cmd_hydraulic_op - find fan-heatsink hydraulic operating point
    % Usage: thermal_cli.m hydraulic-op --config <file>
    % Config fields:
    %   cfg.heatsink.length    [m] parallel to fins (b)
    %   cfg.heatsink.width     [m] perpendicular to fins (a) - used for impinge
    %   cfg.heatsink.profile   string -> HS_Type lookup for tb,Hf,tf,bch
    %   cfg.fan.model          string -> Fan_Model lookup
    %   cfg.fan.count          integer, number of fans in parallel
    %   cfg.ventilation.type   'push' or 'impinge'
    %   cfg.ventilation.impingeOpening  [m] (only for impinge)
    %   cfg.ambient.tInlet     [K] inlet temperature

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m hydraulic-op --config <file>\n');
        fprintf('Finds fan-heatsink hydraulic operating point.\n');
        result = struct();
        return;
    end

    cfg = cli_load_config(parsed);

    % Get heatsink geometry from database (returns mm)
    [tb_mm, Hf_mm, tf_mm, bch_mm] = HS_Type(cfg.heatsink.profile);

    % Get fan curves
    [Hv1, Qv1, Qvmin1, Qvmax1, Cost_Fan1, Volume_Fan1] = Fan_Model(cfg.fan.model);
    nFans = cfg.fan.count;
    Qv = nFans * Qv1;
    Hv = Hv1;

    % Convert SI inputs to mm for idraulico
    b_mm = cfg.heatsink.length * 1000;         % m -> mm
    a_mm = cfg.heatsink.width * 1000;           % m -> mm
    Nf = round(a_mm / (bch_mm + tf_mm));        % number of fins

    % Temperature: K -> C
    Tin_C = cfg.ambient.tInlet - 273.15;

    % Ventilation
    vent_type = cfg.ventilation.type;
    if strcmp(vent_type, 'impinge')
        s_mm = cfg.ventilation.impingeOpening * 1000;
    else
        s_mm = a_mm;  % not used for push, but must be defined
    end

    % Estimate mean air temperature
    Tair_C = Tin_C + 5;  % rough estimate, will be refined in workflow

    % Call idraulico (all dimensions in mm)
    [Redhavg, Hv_f, Qv_f] = idraulico(b_mm, s_mm, Nf, tf_mm, bch_mm, Hf_mm, Tair_C, vent_type, Qv, Hv);

    result.reynolds = Redhavg;
    result.pressure = Hv_f;
    result.flowrate = Qv_f;
    result.numFins = Nf;
    result.tb_mm = tb_mm;
    result.Hf_mm = Hf_mm;
    result.tf_mm = tf_mm;
    result.bch_mm = bch_mm;

    fprintf('reynolds=%.1f\n', Redhavg);
    fprintf('pressure=%.2f\n', Hv_f);
    fprintf('flowrate=%.6f\n', Qv_f);
    fprintf('num_fins=%d\n', Nf);
end
```

- [ ] **Step 2: Add dispatcher case in `thermal_cli.m`**

Add before `otherwise`:
```matlab
        case 'hydraulic-op'
            cmd_hydraulic_op(parsed);
```

- [ ] **Step 3: Write a test config**

Create `tests/fixtures/test_hydraulic_config.m`:

```matlab
function cfg = test_hydraulic_config()
    cfg.heatsink.profile = 'I117';
    cfg.heatsink.length = 0.33;        % [m]
    cfg.heatsink.width = 0.65;         % [m]
    cfg.heatsink.material = 'all_aluminum';
    cfg.fan.model = 'EBMW2E200_axial_AC_50Hz';
    cfg.fan.count = 2;
    cfg.ventilation.type = 'push';
    cfg.ventilation.impingeOpening = 0.22;
    cfg.ambient.tInlet = 313.15;       % 40C in K
end
```

- [ ] **Step 4: Test via CLI**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m hydraulic-op --config tests/fixtures/test_hydraulic_config.m
```

Expected: prints reynolds, pressure, flowrate, num_fins without errors.

- [ ] **Step 5: Commit**

```bash
git add lib/cmd_hydraulic_op.m thermal_cli.m tests/fixtures/test_hydraulic_config.m
git commit -m "feat: add hydraulic-op command wrapping idraulico with SI interface"
```

---

### Task 3: Implement cmd_fin_rth (wraps Rth_fin)

**Files:**
- Create: `lib/cmd_fin_rth.m`
- Modify: `thermal_cli.m` (add case)

- [ ] **Step 1: Write `lib/cmd_fin_rth.m`**

```matlab
function result = cmd_fin_rth(parsed)
    % cmd_fin_rth - finned heatsink thermal resistance
    % Usage: thermal_cli.m fin-rth --config <file> --flowrate <m3/s>
    % Wraps SoftwareTermico Rth_fin.m with SI interface.

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m fin-rth --config <file> --flowrate <m3/s>\n');
        fprintf('Calculates finned heatsink thermal resistance.\n');
        fprintf('Config defines heatsink geometry, fan, and ventilation.\n');
        fprintf('  --flowrate   Operating flow rate [m3/s] (from hydraulic-op)\n');
        result = struct();
        return;
    end

    cfg = cli_load_config(parsed);
    Qv_f = str2double(parsed.flowrate);

    % Get heatsink geometry from database (returns mm)
    [tb_mm, Hf_mm, tf_mm, bch_mm] = HS_Type(cfg.heatsink.profile);

    % Get material properties
    [Kth_plate, Kth_fin, ~, ~, ~, ~] = HS_Tech(cfg.heatsink.material);

    % Convert SI to mm
    a_mm = cfg.heatsink.width * 1000;
    b_mm = cfg.heatsink.length * 1000;
    Nf = round(a_mm / (bch_mm + tf_mm));

    vent_type = cfg.ventilation.type;
    if strcmp(vent_type, 'impinge')
        s_mm = cfg.ventilation.impingeOpening * 1000;
    else
        s_mm = a_mm;
    end

    % Temperature in C
    Tin_C = cfg.ambient.tInlet - 273.15;
    Tair_C = Tin_C + 5;  % estimate

    [Rebavg, Vch1, Vch2, Rth, hf_eq] = Rth_fin(Qv_f, a_mm, b_mm, s_mm, tf_mm, bch_mm, Hf_mm, Tair_C, vent_type, Kth_fin, Nf);

    result.reynolds = Rebavg;
    result.rth = Rth;
    result.h_eq = hf_eq;
    result.v_ch1 = Vch1;
    result.v_ch2 = Vch2;

    fprintf('rth=%.6f\n', Rth);
    fprintf('h_eq=%.2f\n', hf_eq);
    fprintf('reynolds=%.1f\n', Rebavg);
    fprintf('v_ch1=%.4f\n', Vch1);
    fprintf('v_ch2=%.4f\n', Vch2);
end
```

- [ ] **Step 2: Add dispatcher case**

```matlab
        case 'fin-rth'
            cmd_fin_rth(parsed);
```

- [ ] **Step 3: Test via CLI**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m fin-rth --config tests/fixtures/test_hydraulic_config.m --flowrate 0.05
```

Expected: prints rth, h_eq, reynolds, velocities.

- [ ] **Step 4: Commit**

```bash
git add lib/cmd_fin_rth.m thermal_cli.m
git commit -m "feat: add fin-rth command wrapping Rth_fin with SI interface"
```

---

### Task 4: Implement workflow_forced_conv_sim

**Files:**
- Create: `lib/workflow_forced_conv_sim.m`
- Create: `configs/example_forced_conv.m`
- Modify: `thermal_cli.m` (add case)

This replaces `Simulazione_Singola.m` with a config-driven non-interactive pipeline.

- [ ] **Step 1: Write `configs/example_forced_conv.m`**

```matlab
function cfg = example_forced_conv()
    % Example: forced convection simulation
    % Small heatsink with 5 heat sources (from Dati.m VH example)

    cfg.heatsink.profile = 'VHSmallHeatsink30mm';
    cfg.heatsink.width = 0.063;          % [m] perpendicular to fins (a)
    cfg.heatsink.length = 0.130;         % [m] parallel to fins (b)
    cfg.heatsink.material = 'all_aluminum';

    cfg.fan.model = 'JF0825-1H-02';
    cfg.fan.count = 1;

    cfg.ventilation.type = 'push';
    cfg.ventilation.impingeOpening = 0.063;  % [m]

    cfg.ambient.tInlet = 313.15;         % [K] (40C)

    % Heat sources (all in SI: meters, watts)
    cfg.sources.width  = [0.013 0.013 0.013 0.013 0.013];  % [m]
    cfg.sources.length = [0.013 0.013 0.013 0.013 0.013];  % [m]
    cfg.sources.power  = [0.1 30 30 30 30];                 % [W]
    cfg.sources.x      = [0.0165 0.0165 0.0165 0.0165 0.0165]; % [m]
    cfg.sources.y      = [0.119 0.094 0.0715 0.035 0.013];     % [m]

    % Fourier series settings
    cfg.niter = 25;
    cfg.piastra = 'no';           % no additional copper plate
    cfg.grid_points = 41;         % number of grid points per axis
end
```

- [ ] **Step 2: Write `lib/workflow_forced_conv_sim.m`**

```matlab
function result = workflow_forced_conv_sim(parsed)
    % workflow_forced_conv_sim - forced convection heatsink simulation
    % Replaces Simulazione_Singola.m with config-driven pipeline.
    % Usage: thermal_cli.m forced-conv-sim --config <file>

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m forced-conv-sim --config <file>\n');
        fprintf('Runs forced convection heatsink simulation.\n');
        result = struct();
        return;
    end

    cfg = cli_load_config(parsed);

    fprintf('--- Forced Convection Simulation ---\n');

    % Get heatsink geometry (mm from DB)
    [tb_mm, Hf_mm, tf_mm, bch_mm] = HS_Type(cfg.heatsink.profile);
    [Kth_plate, Kth_fin, Kth_piastra, ~, Piastra_flag, ~] = HS_Tech(cfg.heatsink.material);

    % Convert SI to mm for internal functions
    a_mm = cfg.heatsink.width * 1000;
    b_mm = cfg.heatsink.length * 1000;
    Nf = round(a_mm / (bch_mm + tf_mm));

    % Fan
    [Hv1, Qv1, ~, ~, ~, ~] = Fan_Model(cfg.fan.model);
    Qv = cfg.fan.count * Qv1;
    Hv = Hv1;

    vent_type = cfg.ventilation.type;
    if strcmp(vent_type, 'impinge')
        s_mm = cfg.ventilation.impingeOpening * 1000;
    else
        s_mm = a_mm;
    end

    % Source arrays in mm
    p_n = cfg.sources.power;
    a_n = cfg.sources.width * 1000;   % m -> mm
    b_n = cfg.sources.length * 1000;
    x_g = cfg.sources.x * 1000;
    y_g = cfg.sources.y * 1000;

    Tin_C = cfg.ambient.tInlet - 273.15;

    % Step 1: Hydraulic operating point
    fprintf('Step 1: Hydraulic operating point\n');
    Tair_C = Tin_C + 0.5 * sum(p_n) / (Cp_air(Tin_C) * rho_air(Tin_C) * mean(Qv));
    [Redhavg, Hv_f, Qv_f] = idraulico(b_mm, s_mm, Nf, tf_mm, bch_mm, Hf_mm, Tair_C, vent_type, Qv, Hv);
    fprintf('  flowrate=%.6f m3/s\n', Qv_f);
    fprintf('  reynolds=%.1f\n', Redhavg);

    % Recalculate mean air temperature with actual flow
    Tair_C = Tin_C + 0.5 * sum(p_n) / (Cp_air(Tin_C) * rho_air(Tin_C) * Qv_f);

    % Step 2: Fin thermal resistance
    fprintf('Step 2: Fin thermal resistance\n');
    [~, Vch1, Vch2, Rth, hf_eq] = Rth_fin(Qv_f, a_mm, b_mm, s_mm, tf_mm, bch_mm, Hf_mm, Tair_C, vent_type, Kth_fin, Nf);
    fprintf('  rth_fin=%.6f K/W\n', Rth);
    fprintf('  h_eq=%.2f W/(m2*K)\n', hf_eq);

    % Step 3: Temperature distribution
    fprintf('Step 3: Temperature distribution\n');
    tr_mm = 1;  % additional plate thickness (mm), minimum 1 for calc
    Piastra = cfg.piastra;
    Niter = cfg.niter;

    n_grid = cfg.grid_points;
    Xp = linspace(0, a_mm, n_grid);
    Yp = linspace(0, b_mm, n_grid);

    [Ths, Th_BP] = Tplane_dist(Rth, p_n, Tair_C, Tin_C, Niter, Piastra, ...
        a_mm, b_mm, x_g, y_g, Kth_plate, tb_mm, a_n, b_n, Kth_piastra, tr_mm, hf_eq, Xp, Yp);

    % Find max temperature
    T_max = max(Ths(:));
    [row, col] = find(Ths == T_max, 1);
    x_max_m = Xp(col) / 1000;
    y_max_m = Yp(row) / 1000;

    fprintf('  baseplate_temp=%.2f C\n', Th_BP);
    fprintf('  max_surface_temp=%.2f C\n', T_max);
    fprintf('  max_temp_location_x=%.4f m\n', x_max_m);
    fprintf('  max_temp_location_y=%.4f m\n', y_max_m);

    % Build result
    result.flowrate = Qv_f;
    result.reynolds = Redhavg;
    result.rth_fin = Rth;
    result.h_eq = hf_eq;
    result.baseplate_temp = Th_BP;
    result.max_surface_temp = T_max;
    result.temp_grid = Ths;

    % CSV export if requested
    if isfield(parsed, 'save_csv')
        fid = fopen(parsed.save_csv, 'w');
        fprintf(fid, 'point,value,unit\n');
        fprintf(fid, 'flowrate,%.6f,m3/s\n', Qv_f);
        fprintf(fid, 'rth_fin,%.6f,K/W\n', Rth);
        fprintf(fid, 'h_eq,%.2f,W/(m2*K)\n', hf_eq);
        fprintf(fid, 'baseplate_temp,%.2f,C\n', Th_BP);
        fprintf(fid, 'max_surface_temp,%.2f,C\n', T_max);
        fclose(fid);
        fprintf('Results saved to: %s\n', parsed.save_csv);
    end

    fprintf('--- Complete ---\n');
end
```

- [ ] **Step 3: Add dispatcher case**

```matlab
        case 'forced-conv-sim'
            workflow_forced_conv_sim(parsed);
```

- [ ] **Step 4: Test via CLI**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m forced-conv-sim --config configs/example_forced_conv.m
```

Expected: prints 3-step output with flowrate, Rth, temperature distribution, max temp.

- [ ] **Step 5: Commit**

```bash
git add lib/workflow_forced_conv_sim.m configs/example_forced_conv.m thermal_cli.m
git commit -m "feat: add forced-conv-sim workflow replacing Simulazione_Singola"
```

---

### Task 5: Final integration test

- [ ] **Step 1: Run full test suite**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui tests/run_tests.m
```

Expected: All tests pass (31 from Phase 2 + 9 air properties = 40).

- [ ] **Step 2: Test all new CLI commands**

```bash
cd /home/tinix/claude_wsl/octave/thermal

octave --no-gui thermal_cli.m hydraulic-op --help
octave --no-gui thermal_cli.m hydraulic-op --config tests/fixtures/test_hydraulic_config.m
octave --no-gui thermal_cli.m fin-rth --config tests/fixtures/test_hydraulic_config.m --flowrate 0.05
octave --no-gui thermal_cli.m forced-conv-sim --config configs/example_forced_conv.m
```

- [ ] **Step 3: Commit any fixups**

```bash
git add -p
git commit -m "fix: phase 3 integration fixups"
```

---

## Summary

After Phase 3, the project has:
- **9 new tests** for air properties (literature-verified)
- **2 new CLI commands:** `hydraulic-op`, `fin-rth`
- **1 new workflow:** `forced-conv-sim` (replaces Simulazione_Singola)
- **SI boundary conversion** — CLI accepts meters/Kelvin, converts to mm/°C at the SoftwareTermico interface
- **Total: ~40 tests, all passing**
- **CLI commands: 8** (calc-rth, fin-efficiency, radiation, layer-rth, stack-rth, semi-on-pcb, hydraulic-op, fin-rth)
- **Workflows: 2** (semi-on-pcb, forced-conv-sim)
