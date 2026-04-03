# Phase 1: Foundation — CLI Skeleton + Formula Tests

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the CLI dispatcher, shared utilities, simplest commands (calc-rth, fin-efficiency, radiation), test runner, and literature-verified formula tests.

**Architecture:** Single `thermal_cli.m` entry point dispatches to `cmd_*.m` functions in `lib/`. Each command parses a struct from `cli_parse_args`, calls existing functions in `mfiles/`, prints `key=value` output. Tests live in `tests/` and run via `tests/run_tests.m`.

**Tech Stack:** GNU Octave (CLI mode), existing MATLAB/Octave `.m` files in `mfiles/Thermal/Formula/`

**Design spec:** `docs/superpowers/specs/2026-04-03-cli-unification-design.md`

---

### Task 1: Create directory structure and test runner

**Files:**
- Create: `lib/` (directory)
- Create: `configs/` (directory)
- Create: `tests/run_tests.m`
- Create: `tests/assert_near.m`

- [ ] **Step 1: Create directories**

```bash
mkdir -p lib configs tests
```

- [ ] **Step 2: Write `tests/assert_near.m`**

```matlab
function pass = assert_near(actual, expected, tol, name)
    % assert_near - check that actual is within tol of expected
    % Returns true if |actual - expected| < tol, prints FAIL message otherwise
    pass = abs(actual - expected) < tol;
    if ~pass
        fprintf('  FAIL: %s: got %.6g, expected %.6g (tol %.6g)\n', name, actual, expected, tol);
    end
end
```

- [ ] **Step 3: Write `tests/run_tests.m`**

```matlab
function run_tests()
    % run_tests - discovers and runs all test_*.m files in tests/
    % Each test file must be a function returning a cell array of structs
    % with fields: .name (string), .pass (bool)

    this_dir = fileparts(mfilename('fullpath'));
    root_dir = fullfile(this_dir, '..');
    addpath(fullfile(root_dir, 'lib'));
    addpath(genpath(fullfile(root_dir, 'mfiles')));
    addpath(this_dir);

    test_files = glob(fullfile(this_dir, 'test_*.m'));
    total_pass = 0;
    total_fail = 0;
    total_error = 0;

    for i = 1:length(test_files)
        [~, name, ~] = fileparts(test_files{i});
        fprintf('Running %s ...', name);
        try
            results = feval(name);
            pass = sum(cellfun(@(r) r.pass, results));
            fail = length(results) - pass;
            fprintf(' %d/%d PASS\n', pass, length(results));
            if fail > 0
                for j = 1:length(results)
                    if ~results{j}.pass
                        fprintf('  FAIL: %s\n', results{j}.name);
                        if isfield(results{j}, 'detail')
                            fprintf('    %s\n', results{j}.detail);
                        end
                    end
                end
            end
            total_pass = total_pass + pass;
            total_fail = total_fail + fail;
        catch e
            fprintf(' ERROR: %s\n', e.message);
            total_error = total_error + 1;
        end
    end

    fprintf('\n========================================\n');
    fprintf('TOTAL: %d pass, %d fail, %d error\n', total_pass, total_fail, total_error);
    if total_fail > 0 || total_error > 0
        exit(1);
    end
end
```

- [ ] **Step 4: Write a dummy test to verify the runner works**

Create `tests/test_sanity.m`:

```matlab
function results = test_sanity()
    results = {};
    r.name = 'sanity: 1 + 1 == 2';
    r.pass = (1 + 1 == 2);
    results{end+1} = r;
end
```

- [ ] **Step 5: Run the test runner**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui --path tests tests/run_tests.m
```

Expected output:
```
Running test_sanity ... 1/1 PASS

========================================
TOTAL: 1 pass, 0 fail, 0 error
```

- [ ] **Step 6: Delete dummy test and commit**

```bash
rm tests/test_sanity.m
git add tests/run_tests.m tests/assert_near.m
git commit -m "feat: add test runner and assert_near helper"
```

---

### Task 2: Build CLI argument parser

**Files:**
- Create: `lib/cli_parse_args.m`

- [ ] **Step 1: Write test for cli_parse_args**

Create `tests/test_cli_parse_args.m`:

```matlab
function results = test_cli_parse_args()
    results = {};

    % Test 1: key-value pairs
    r.name = 'cli_parse_args: key-value pairs';
    parsed = cli_parse_args({'--power', '50', '--tref', '300'});
    r.pass = strcmp(parsed.power, '50') && strcmp(parsed.tref, '300');
    r.detail = 'should parse --power 50 --tref 300';
    results{end+1} = r;

    % Test 2: dotted keys become underscores
    r.name = 'cli_parse_args: dotted keys';
    parsed = cli_parse_args({'--fluid.flowrate', '0.01'});
    r.pass = isfield(parsed, 'fluid_flowrate') && strcmp(parsed.fluid_flowrate, '0.01');
    r.detail = 'should convert --fluid.flowrate to fluid_flowrate';
    results{end+1} = r;

    % Test 3: flag without value
    r.name = 'cli_parse_args: boolean flag';
    parsed = cli_parse_args({'--help'});
    r.pass = isfield(parsed, 'help') && parsed.help == true;
    r.detail = 'should set help=true';
    results{end+1} = r;

    % Test 4: flag followed by another flag
    r.name = 'cli_parse_args: two flags';
    parsed = cli_parse_args({'--verbose', '--help'});
    r.pass = parsed.verbose == true && parsed.help == true;
    r.detail = 'should set both flags to true';
    results{end+1} = r;

    % Test 5: mixed flags and key-value
    r.name = 'cli_parse_args: mixed';
    parsed = cli_parse_args({'--verbose', '--power', '50', '--help'});
    r.pass = parsed.verbose == true && strcmp(parsed.power, '50') && parsed.help == true;
    r.detail = 'should handle mixed flags and values';
    results{end+1} = r;

    % Test 6: empty args
    r.name = 'cli_parse_args: empty';
    parsed = cli_parse_args({});
    r.pass = isstruct(parsed) && isempty(fieldnames(parsed));
    r.detail = 'should return empty struct';
    results{end+1} = r;
end
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui --path tests --path lib tests/run_tests.m
```

Expected: ERROR with "undefined function 'cli_parse_args'"

- [ ] **Step 3: Write `lib/cli_parse_args.m`**

```matlab
function parsed = cli_parse_args(args)
    % cli_parse_args - parse CLI arguments into a struct
    % Input: cell array of strings, e.g. {'--power', '50', '--help'}
    % Output: struct with fields
    %   --key value  -> parsed.key = 'value' (string)
    %   --key.sub v  -> parsed.key_sub = 'value' (dots to underscores)
    %   --flag       -> parsed.flag = true (if next arg starts with -- or is last)

    parsed = struct();
    i = 1;
    while i <= length(args)
        arg = args{i};
        if length(arg) > 2 && strcmp(arg(1:2), '--')
            key = strrep(arg(3:end), '.', '_');
            key = strrep(key, '-', '_');
            if i + 1 <= length(args) && ~strncmp(args{i+1}, '--', 2)
                parsed.(key) = args{i+1};
                i = i + 2;
            else
                parsed.(key) = true;
                i = i + 1;
            end
        else
            i = i + 1;
        end
    end
end
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui --path tests --path lib tests/run_tests.m
```

Expected: `test_cli_parse_args ... 6/6 PASS`

- [ ] **Step 5: Commit**

```bash
git add lib/cli_parse_args.m tests/test_cli_parse_args.m
git commit -m "feat: add CLI argument parser with tests"
```

---

### Task 3: Build config loader

**Files:**
- Create: `lib/cli_load_config.m`

- [ ] **Step 1: Write a test config file**

Create `tests/fixtures/test_config.m`:

```matlab
function cfg = test_config()
    cfg.heatsink.type = 'extruded';
    cfg.heatsink.height = 0.022;
    cfg.fluid.type = 'H2OGly50';
    cfg.fluid.flowrate = 0.005;
end
```

- [ ] **Step 2: Write test for cli_load_config**

Create `tests/test_cli_load_config.m`:

```matlab
function results = test_cli_load_config()
    results = {};

    % Test 1: load config from file
    r.name = 'cli_load_config: load from file';
    parsed = struct('config', fullfile(fileparts(mfilename('fullpath')), 'fixtures', 'test_config.m'));
    cfg = cli_load_config(parsed);
    r.pass = strcmp(cfg.heatsink.type, 'extruded') && cfg.fluid.flowrate == 0.005;
    r.detail = sprintf('heatsink.type=%s, fluid.flowrate=%g', cfg.heatsink.type, cfg.fluid.flowrate);
    results{end+1} = r;

    % Test 2: override nested field
    r.name = 'cli_load_config: override nested field';
    parsed = struct('config', fullfile(fileparts(mfilename('fullpath')), 'fixtures', 'test_config.m'), ...
                    'fluid_flowrate', '0.01');
    cfg = cli_load_config(parsed);
    r.pass = cfg.fluid.flowrate == 0.01;
    r.detail = sprintf('fluid.flowrate=%g, expected 0.01', cfg.fluid.flowrate);
    results{end+1} = r;

    % Test 3: no config file, just args
    r.name = 'cli_load_config: no config file';
    parsed = struct('power', '50');
    cfg = cli_load_config(parsed);
    r.pass = isstruct(cfg) && strcmp(cfg.power, '50');
    r.detail = 'should return struct with flat args';
    results{end+1} = r;
end
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui --path tests --path lib tests/run_tests.m
```

Expected: ERROR with "undefined function 'cli_load_config'"

- [ ] **Step 4: Write `lib/cli_load_config.m`**

```matlab
function cfg = cli_load_config(parsed)
    % cli_load_config - load config from .m file and merge CLI overrides
    % If parsed.config exists, calls the .m function to get base config.
    % Then merges any --key.sub value overrides from parsed.

    if isfield(parsed, 'config')
        config_path = parsed.config;
        [dir_path, func_name, ~] = fileparts(config_path);
        if ~isempty(dir_path)
            addpath(dir_path);
        end
        cfg = feval(func_name);
    else
        cfg = struct();
    end

    % Merge overrides: fields with underscores map to nested struct fields
    fnames = fieldnames(parsed);
    skip_fields = {'config', 'help', 'verbose', 'femm_lua', 'save_csv', 'output'};
    for i = 1:length(fnames)
        key = fnames{i};
        if any(strcmp(key, skip_fields))
            continue;
        end
        val = parsed.(key);
        parts = strsplit(key, '_');
        if length(parts) == 2
            % nested: fluid_flowrate -> cfg.fluid.flowrate
            num_val = str2double(val);
            if ~isnan(num_val)
                cfg.(parts{1}).(parts{2}) = num_val;
            else
                cfg.(parts{1}).(parts{2}) = val;
            end
        else
            % flat: power -> cfg.power
            if ischar(val)
                num_val = str2double(val);
                if ~isnan(num_val)
                    cfg.(key) = num_val;
                else
                    cfg.(key) = val;
                end
            else
                cfg.(key) = val;
            end
        end
    end
end
```

- [ ] **Step 5: Create fixtures directory and test config**

```bash
mkdir -p tests/fixtures
```

(The test config file was already specified in Step 1.)

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui --path tests --path lib tests/run_tests.m
```

Expected: `test_cli_load_config ... 3/3 PASS`

- [ ] **Step 7: Commit**

```bash
git add lib/cli_load_config.m tests/test_cli_load_config.m tests/fixtures/test_config.m
git commit -m "feat: add config loader with override merging"
```

---

### Task 4: Build help printer and CLI dispatcher

**Files:**
- Create: `lib/cli_print_help.m`
- Create: `thermal_cli.m`

- [ ] **Step 1: Write `lib/cli_print_help.m`**

```matlab
function cli_print_help(command)
    % cli_print_help - print help for all commands or a specific command

    if nargin == 0 || isempty(command)
        fprintf('Usage: octave thermal_cli.m <command> [options]\n\n');
        fprintf('Commands:\n');
        fprintf('  calc-rth           Thermal resistance from power and temperatures\n');
        fprintf('  fin-efficiency     Fin efficiency (tanh model)\n');
        fprintf('  radiation          Radiation heat transfer (5 modes)\n');
        fprintf('  layer-rth          Single layer thermal resistance with spreading\n');
        fprintf('  stack-rth          Layer stack thermal resistance\n');
        fprintf('  heatsink-create    Create heatsink from database reference\n');
        fprintf('  heatsink-rth       Extruded fin heatsink thermal resistance\n');
        fprintf('  free-conv          Free convection surface temperature\n');
        fprintf('  water-cooling      Water cooling system analysis\n');
        fprintf('  hydraulic-op       Fan-heatsink hydraulic operating point\n');
        fprintf('  fin-rth            Finned heatsink thermal resistance\n');
        fprintf('  temp-dist          Temperature distribution on heatsink plane\n');
        fprintf('  gen-femm           Generate FEMM Lua verification script\n');
        fprintf('  compare-femm       Compare FEMM results with analytical\n');
        fprintf('\nWorkflows:\n');
        fprintf('  semi-on-pcb        Semiconductor on PCB thermal model\n');
        fprintf('  extruded-fin       Extruded fin heatsink design\n');
        fprintf('  optimize-fin       Parametric fin optimization\n');
        fprintf('  forced-conv-sim    Forced convection simulation\n');
        fprintf('  multi-sim          Multi-configuration simulation\n');
        fprintf('\nOptions:\n');
        fprintf('  --help             Show help for a command\n');
        fprintf('  --config <file>    Load configuration from .m file\n');
    end
end
```

- [ ] **Step 2: Write `thermal_cli.m`**

```matlab
function thermal_cli()
    % thermal_cli - main entry point for the thermal toolbox CLI
    % Usage: octave thermal_cli.m <command> [options]

    root_dir = fileparts(mfilename('fullpath'));
    addpath(fullfile(root_dir, 'lib'));
    addpath(genpath(fullfile(root_dir, 'mfiles')));

    args = argv();
    if isempty(args) || strcmp(args{1}, '--help') || strcmp(args{1}, '-h')
        cli_print_help();
        return;
    end

    command = args{1};
    rest = args(2:end);
    parsed = cli_parse_args(rest);

    switch command
        case 'calc-rth'
            cmd_calc_rth(parsed);
        case 'fin-efficiency'
            cmd_fin_efficiency(parsed);
        case 'radiation'
            cmd_radiation(parsed);
        otherwise
            fprintf(2, 'Unknown command: %s\n', command);
            cli_print_help();
            exit(1);
    end
end
```

Note: The dispatcher starts with only the Phase 1 commands. More cases will be added in later phases.

- [ ] **Step 3: Test the help output**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m --help
```

Expected: prints the command listing without errors.

- [ ] **Step 4: Test unknown command**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m unknown-cmd 2>&1 || true
```

Expected: `Unknown command: unknown-cmd` followed by help text.

- [ ] **Step 5: Commit**

```bash
git add thermal_cli.m lib/cli_print_help.m
git commit -m "feat: add CLI dispatcher with help system"
```

---

### Task 5: Implement cmd_calc_rth

**Files:**
- Create: `lib/cmd_calc_rth.m`
- Existing: `mfiles/calc_rth_from_power_temp.m` (also at root `calc_rth_from_power_temp.m`)

The underlying function is: `Rth = (Tmeas - Tref) / P`

- [ ] **Step 1: Write test**

Add to `tests/test_formula.m` (create file):

```matlab
function results = test_formula()
    results = {};

    % --- calc_rth_from_power_temp ---

    r.name = 'calc_rth: basic calculation';
    rth = calc_rth_from_power_temp(50, 300, 350);
    r.pass = assert_near(rth, 1.0, 1e-10, r.name);
    r.detail = sprintf('got %.6g, expected 1.0', rth);
    results{end+1} = r;

    r.name = 'calc_rth: high power';
    rth = calc_rth_from_power_temp(100, 298.15, 373.15);
    expected = (373.15 - 298.15) / 100;  % 0.75 K/W
    r.pass = assert_near(rth, expected, 1e-10, r.name);
    r.detail = sprintf('got %.6g, expected %.6g', rth, expected);
    results{end+1} = r;
end
```

- [ ] **Step 2: Run test to verify it passes (the underlying function already exists)**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui --path tests --path lib --path mfiles tests/run_tests.m
```

Expected: `test_formula ... 2/2 PASS` (the underlying function exists, we're just testing it)

- [ ] **Step 3: Write `lib/cmd_calc_rth.m`**

```matlab
function result = cmd_calc_rth(parsed)
    % cmd_calc_rth - calculate thermal resistance from power and temperatures
    % Usage: thermal_cli.m calc-rth --power <W> --tref <K> --tmeas <K>

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m calc-rth --power <W> --tref <K> --tmeas <K>\n');
        fprintf('Calculates thermal resistance: Rth = (Tmeas - Tref) / P\n');
        result = struct();
        return;
    end

    P = str2double(parsed.power);
    Tref = str2double(parsed.tref);
    Tmeas = str2double(parsed.tmeas);

    rth = calc_rth_from_power_temp(P, Tref, Tmeas);

    result.rth = rth;
    fprintf('rth=%.6f\n', rth);
end
```

- [ ] **Step 4: Test via CLI**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m calc-rth --power 50 --tref 300 --tmeas 350
```

Expected output: `rth=1.000000`

- [ ] **Step 5: Test help**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m calc-rth --help
```

Expected: prints usage line.

- [ ] **Step 6: Commit**

```bash
git add lib/cmd_calc_rth.m tests/test_formula.m
git commit -m "feat: add calc-rth command with tests"
```

---

### Task 6: Implement cmd_fin_efficiency with literature tests

**Files:**
- Create: `lib/cmd_fin_efficiency.m`
- Modify: `tests/test_formula.m` (append tests)
- Existing: `mfiles/Thermal/Formula/finEfficieny.m`

The underlying function: `etaFin = tanh(mL)/mL` where `mL = sqrt(h*A/(k*Ac*L)) * L`

Literature reference: Incropera & DeWitt, "Fundamentals of Heat and Mass Transfer" 7th ed, Table 3.5.
- At mL = 0.5: eta = tanh(0.5)/0.5 = 0.46212/0.5 = 0.92424
- At mL = 1.0: eta = tanh(1.0)/1.0 = 0.76159/1.0 = 0.76159
- At mL = 2.0: eta = tanh(2.0)/2.0 = 0.96403/2.0 = 0.48201

To get a specific mL, set L=1, Ac=1, A=1, then `mL = sqrt(h/k)`. So for mL=0.5: h=0.25, k=1. For mL=2.0: h=4, k=1.

- [ ] **Step 1: Add literature tests to `tests/test_formula.m`**

Append to the `test_formula` function (after the existing calc_rth tests):

```matlab
    % --- finEfficieny: literature values ---
    % Reference: Incropera 7th ed, analytical: eta = tanh(mL)/mL
    % Setup: L=1, A=1, Ac=1, k=1 -> mL = sqrt(h)

    r.name = 'fin_efficiency: mL=0.5 (Incropera)';
    eta = finEfficieny(1, 0.25, 1, 1, 1);  % mL = sqrt(0.25) = 0.5
    expected = tanh(0.5) / 0.5;  % 0.92424
    r.pass = assert_near(eta, expected, 0.001, r.name);
    r.detail = sprintf('got %.6f, expected %.6f', eta, expected);
    results{end+1} = r;

    r.name = 'fin_efficiency: mL=1.0 (Incropera)';
    eta = finEfficieny(1, 1, 1, 1, 1);  % mL = sqrt(1) = 1.0
    expected = tanh(1.0) / 1.0;  % 0.76159
    r.pass = assert_near(eta, expected, 0.001, r.name);
    r.detail = sprintf('got %.6f, expected %.6f', eta, expected);
    results{end+1} = r;

    r.name = 'fin_efficiency: mL=2.0 (Incropera)';
    eta = finEfficieny(1, 4, 1, 1, 1);  % mL = sqrt(4) = 2.0
    expected = tanh(2.0) / 2.0;  % 0.48201
    r.pass = assert_near(eta, expected, 0.001, r.name);
    r.detail = sprintf('got %.6f, expected %.6f', eta, expected);
    results{end+1} = r;

    % Realistic case: aluminum fin, L=20mm, t=1mm, h=50 W/m2K, k=200 W/mK
    r.name = 'fin_efficiency: realistic aluminum fin';
    L = 0.02; t = 0.001; h = 50; k = 200;
    W = 1;  % per unit width
    A = 2 * L * W;   % both sides of fin
    Ac = t * W;       % cross section
    eta = finEfficieny(L, h, A, k, Ac);
    mL = sqrt(h * A / (k * Ac * L)) * L;  % = sqrt(50*0.04/(200*0.001*0.02))*0.02 = sqrt(1000)*0.02 = 0.6325
    expected = tanh(mL) / mL;
    r.pass = assert_near(eta, expected, 0.001, r.name);
    r.detail = sprintf('got %.6f, expected %.6f (mL=%.4f)', eta, expected, mL);
    results{end+1} = r;
```

- [ ] **Step 2: Run tests**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui --path tests --path lib --path mfiles --path mfiles/Thermal/Formula tests/run_tests.m
```

Expected: `test_formula ... 6/6 PASS`

- [ ] **Step 3: Write `lib/cmd_fin_efficiency.m`**

```matlab
function result = cmd_fin_efficiency(parsed)
    % cmd_fin_efficiency - calculate fin efficiency
    % Usage: thermal_cli.m fin-efficiency --length <m> --h <W/m2K> --area <m2> --k <W/mK> --ac <m2>

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m fin-efficiency --length <m> --h <W/m2K> --area <m2> --k <W/mK> --ac <m2>\n');
        fprintf('Calculates fin efficiency using eta = tanh(mL)/mL.\n');
        fprintf('  --length  Fin length [m]\n');
        fprintf('  --h       Heat transfer coefficient [W/(m2*K)]\n');
        fprintf('  --area    Fin surface area [m2]\n');
        fprintf('  --k       Fin thermal conductivity [W/(m*K)]\n');
        fprintf('  --ac      Fin cross-sectional area [m2]\n');
        result = struct();
        return;
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

- [ ] **Step 4: Test via CLI**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m fin-efficiency --length 1 --h 0.25 --area 1 --k 1 --ac 1
```

Expected: `eta=0.924244` (tanh(0.5)/0.5)

- [ ] **Step 5: Commit**

```bash
git add lib/cmd_fin_efficiency.m tests/test_formula.m
git commit -m "feat: add fin-efficiency command with literature-verified tests"
```

---

### Task 7: Implement cmd_radiation with all 5 modes and literature tests

**Files:**
- Create: `lib/cmd_radiation.m`
- Modify: `tests/test_formula.m` (append radiation tests)
- Existing: `mfiles/Thermal/Formula/heatTransfer*.m` (5 files)

**BUG NOTE:** `heatTransferSmallConvexRadiation.m` line 14 has `eps1(T1^4-T2^4)` — missing `*` operator. This tries to index eps1 as a function. Must fix before testing.

- [ ] **Step 1: Fix bug in `heatTransferSmallConvexRadiation.m`**

In `mfiles/Thermal/Formula/heatTransferSmallConvexRadiation.m`, line 14, change:

```matlab
    qRad12 = sigmaBoltz*A1*eps1(T1^4-T2^4);
```

to:

```matlab
    qRad12 = sigmaBoltz*A1*eps1*(T1^4-T2^4);
```

- [ ] **Step 2: Add radiation tests to `tests/test_formula.m`**

Append to the `test_formula` function:

```matlab
    % --- Radiation: literature values ---
    % Reference: Incropera 7th ed Ch.13, using Stefan-Boltzmann sigma = 5.670367e-8

    sigma = 5.670367e-8;

    % Parallel planes: two blackbodies (eps=1)
    % q = sigma * A * (T1^4 - T2^4) / (1/eps1 + 1/eps2 - 1)
    % With eps1=eps2=1: q = sigma * A * (T1^4 - T2^4)
    r.name = 'radiation_parallel: blackbody 500K-300K';
    q = heatTransferParallelPlanesRadiation(500, 300, 1.0, 1.0, 1.0);
    expected = sigma * 1.0 * (500^4 - 300^4);  % 2552.68 W
    r.pass = assert_near(q, expected, 0.01, r.name);
    r.detail = sprintf('got %.2f W, expected %.2f W', q, expected);
    results{end+1} = r;

    % Parallel planes: gray surfaces
    r.name = 'radiation_parallel: gray eps=0.5 500K-300K';
    q = heatTransferParallelPlanesRadiation(500, 300, 1.0, 0.5, 0.5);
    expected = sigma * 1.0 * (500^4 - 300^4) / (1/0.5 + 1/0.5 - 1);  % 2+2-1=3 -> 850.89 W
    r.pass = assert_near(q, expected, 0.01, r.name);
    r.detail = sprintf('got %.2f W, expected %.2f W', q, expected);
    results{end+1} = r;

    % Concentric cylinders: blackbody
    r.name = 'radiation_cylinder: blackbody r1=0.05 r2=0.10 L=1';
    q = heatTransferConcentricCylinderRadiation(500, 300, 0.05, 0.10, 1.0, 1.0, 1.0);
    A1 = 2 * pi * 0.05 * 1.0;
    expected = sigma * A1 * (500^4 - 300^4) / (1/1.0 + (1-1.0)/1.0*(0.05/0.10));
    r.pass = assert_near(q, expected, 0.01, r.name);
    r.detail = sprintf('got %.2f W, expected %.2f W', q, expected);
    results{end+1} = r;

    % Concentric spheres: blackbody
    r.name = 'radiation_sphere: blackbody r1=0.05 r2=0.10';
    q = heatTransferConcentricSphereRadiation(500, 300, 0.05, 0.10, 1.0, 1.0);
    A1 = 4 * pi * 0.05^2;
    expected = sigma * A1 * (500^4 - 300^4) / (1/1.0 + (1-1.0)/1.0*(0.05/0.10)^2);
    r.pass = assert_near(q, expected, 0.01, r.name);
    r.detail = sprintf('got %.2f W, expected %.2f W', q, expected);
    results{end+1} = r;

    % Enclosure: two parallel surfaces forming enclosure, F12=1
    r.name = 'radiation_enclosure: F12=1 A1=A2=1 eps=0.8';
    q = heatTransferEnclosureRadiation(500, 300, 0.8, 0.8, 1.0, 1.0, 1.0);
    expected = sigma * (500^4 - 300^4) / ((1-0.8)/(0.8*1) + 1/(1*1) + (1-0.8)/(0.8*1));
    r.pass = assert_near(q, expected, 0.01, r.name);
    r.detail = sprintf('got %.2f W, expected %.2f W', q, expected);
    results{end+1} = r;

    % Small convex body in large cavity
    r.name = 'radiation_convex: small body eps=0.9 A=0.01';
    q = heatTransferSmallConvexRadiation(500, 300, 0.01, 0.9);
    expected = sigma * 0.01 * 0.9 * (500^4 - 300^4);
    r.pass = assert_near(q, expected, 0.01, r.name);
    r.detail = sprintf('got %.4f W, expected %.4f W', q, expected);
    results{end+1} = r;
```

- [ ] **Step 3: Run tests**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui --path tests --path lib --path mfiles --path mfiles/Thermal/Formula tests/run_tests.m
```

Expected: `test_formula ... 12/12 PASS` (2 calc_rth + 4 fin_efficiency + 6 radiation)

- [ ] **Step 4: Write `lib/cmd_radiation.m`**

```matlab
function result = cmd_radiation(parsed)
    % cmd_radiation - radiation heat transfer calculations
    % Usage: thermal_cli.m radiation --mode <type> [options]
    % Modes: parallel, cylinder, sphere, enclosure, convex

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m radiation --mode <type> [options]\n\n');
        fprintf('Modes:\n');
        fprintf('  parallel   --t1 <K> --t2 <K> --area <m2> --eps1 <-> --eps2 <->\n');
        fprintf('  cylinder   --t1 <K> --t2 <K> --r1 <m> --r2 <m> --length <m> --eps1 <-> --eps2 <->\n');
        fprintf('  sphere     --t1 <K> --t2 <K> --r1 <m> --r2 <m> --eps1 <-> --eps2 <->\n');
        fprintf('  enclosure  --t1 <K> --t2 <K> --eps1 <-> --eps2 <-> --a1 <m2> --a2 <m2> --f12 <->\n');
        fprintf('  convex     --t1 <K> --t2 <K> --a1 <m2> --eps1 <->\n');
        result = struct();
        return;
    end

    if ~isfield(parsed, 'mode')
        fprintf(2, 'Error: --mode is required (parallel|cylinder|sphere|enclosure|convex)\n');
        result = struct();
        return;
    end

    T1 = str2double(parsed.t1);
    T2 = str2double(parsed.t2);

    switch parsed.mode
        case 'parallel'
            A = str2double(parsed.area);
            eps1 = str2double(parsed.eps1);
            eps2 = str2double(parsed.eps2);
            q = heatTransferParallelPlanesRadiation(T1, T2, A, eps1, eps2);

        case 'cylinder'
            r1 = str2double(parsed.r1);
            r2 = str2double(parsed.r2);
            L = str2double(parsed.length);
            eps1 = str2double(parsed.eps1);
            eps2 = str2double(parsed.eps2);
            q = heatTransferConcentricCylinderRadiation(T1, T2, r1, r2, L, eps1, eps2);

        case 'sphere'
            r1 = str2double(parsed.r1);
            r2 = str2double(parsed.r2);
            eps1 = str2double(parsed.eps1);
            eps2 = str2double(parsed.eps2);
            q = heatTransferConcentricSphereRadiation(T1, T2, r1, r2, eps1, eps2);

        case 'enclosure'
            eps1 = str2double(parsed.eps1);
            eps2 = str2double(parsed.eps2);
            A1 = str2double(parsed.a1);
            A2 = str2double(parsed.a2);
            F12 = str2double(parsed.f12);
            q = heatTransferEnclosureRadiation(T1, T2, eps1, eps2, A1, A2, F12);

        case 'convex'
            A1 = str2double(parsed.a1);
            eps1 = str2double(parsed.eps1);
            q = heatTransferSmallConvexRadiation(T1, T2, A1, eps1);

        otherwise
            fprintf(2, 'Error: unknown mode "%s"\n', parsed.mode);
            result = struct();
            return;
    end

    result.q = q;
    result.mode = parsed.mode;
    fprintf('q=%.6f\n', q);
end
```

- [ ] **Step 5: Test via CLI**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m radiation --mode parallel --t1 500 --t2 300 --area 1 --eps1 1 --eps2 1
```

Expected: `q=2552.680000` (approximately)

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m radiation --mode convex --t1 500 --t2 300 --a1 0.01 --eps1 0.9
```

Expected: `q=22.974120` (approximately)

- [ ] **Step 6: Commit**

```bash
git add lib/cmd_radiation.m tests/test_formula.m mfiles/Thermal/Formula/heatTransferSmallConvexRadiation.m
git commit -m "feat: add radiation command (5 modes) with literature tests

fix: missing * operator in heatTransferSmallConvexRadiation.m"
```

---

### Task 8: Final integration test and cleanup

**Files:**
- Verify: all files from Tasks 1-7

- [ ] **Step 1: Run full test suite**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui --path tests --path lib --path mfiles --path mfiles/Thermal/Formula tests/run_tests.m
```

Expected:
```
Running test_cli_load_config ... 3/3 PASS
Running test_cli_parse_args ... 6/6 PASS
Running test_formula ... 12/12 PASS

========================================
TOTAL: 21 pass, 0 fail, 0 error
```

- [ ] **Step 2: Test all CLI commands end-to-end**

```bash
cd /home/tinix/claude_wsl/octave/thermal

# Help
octave --no-gui thermal_cli.m --help

# calc-rth
octave --no-gui thermal_cli.m calc-rth --power 100 --tref 298.15 --tmeas 373.15

# fin-efficiency
octave --no-gui thermal_cli.m fin-efficiency --length 0.02 --h 50 --area 0.04 --k 200 --ac 0.001

# radiation (all 5 modes)
octave --no-gui thermal_cli.m radiation --mode parallel --t1 500 --t2 300 --area 1 --eps1 0.8 --eps2 0.8
octave --no-gui thermal_cli.m radiation --mode cylinder --t1 500 --t2 300 --r1 0.05 --r2 0.1 --length 1 --eps1 0.9 --eps2 0.9
octave --no-gui thermal_cli.m radiation --mode sphere --t1 500 --t2 300 --r1 0.05 --r2 0.1 --eps1 0.9 --eps2 0.9
octave --no-gui thermal_cli.m radiation --mode enclosure --t1 500 --t2 300 --eps1 0.8 --eps2 0.8 --a1 1 --a2 1 --f12 1
octave --no-gui thermal_cli.m radiation --mode convex --t1 500 --t2 300 --a1 0.01 --eps1 0.9
```

All should print `key=value` output without errors.

- [ ] **Step 3: Verify no errors with --help on each command**

```bash
cd /home/tinix/claude_wsl/octave/thermal
octave --no-gui thermal_cli.m calc-rth --help
octave --no-gui thermal_cli.m fin-efficiency --help
octave --no-gui thermal_cli.m radiation --help
```

All should print usage text and exit cleanly.

- [ ] **Step 4: Commit any fixups**

Only if Steps 1-3 revealed issues that needed fixing.

```bash
git add -p  # stage specific changes
git commit -m "fix: phase 1 integration fixups"
```

---

## Summary

After Phase 1, the project has:
- `thermal_cli.m` — working dispatcher with 3 commands
- `lib/cli_parse_args.m` — argument parser
- `lib/cli_load_config.m` — config loader with override merging
- `lib/cli_print_help.m` — help system
- `lib/cmd_calc_rth.m` — thermal resistance calculation
- `lib/cmd_fin_efficiency.m` — fin efficiency with literature-verified tests
- `lib/cmd_radiation.m` — 5 radiation modes with literature-verified tests
- `tests/run_tests.m` — test runner
- `tests/assert_near.m` — assertion helper
- `tests/test_formula.m` — 12 tests (2 calc_rth + 4 fin_efficiency + 6 radiation)
- `tests/test_cli_parse_args.m` — 6 tests
- `tests/test_cli_load_config.m` — 3 tests
- **Bug fix:** `heatTransferSmallConvexRadiation.m` missing `*` operator
- **Total: 21 tests, all passing**

Next: Phase 2 plan will wrap the Thermal/ OOP classes as CLI commands.
