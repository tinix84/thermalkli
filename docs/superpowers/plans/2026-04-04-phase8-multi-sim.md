# Phase 8: Multi-Sim Workflow (Issue #2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port `Simulazione_Multipla.m` as a config-driven CLI workflow that sweeps heatsink geometry, checks temperature limits, auto-resizes the heatsink, and collects results.

**Architecture:** The workflow is decomposed into 3 layers:
1. `multi_sim_core.m` — runs a single geometry configuration (hydraulic OP + Rth + temperature check + resize loop)
2. `workflow_multi_sim.m` — orchestrates the sweep over all geometry combinations, calls core for each
3. Config struct replaces `Dati_multipla.m` + `Soluzione` structs

**Key simplification vs original:** The original uses a `Soluzione` struct array with different fan/heatsink material combinations. We model this as an array of `cfg.solutions` in the config, each with its own fan model, material, ventilation type, and initial geometry.

---

### Task 1: Create multi_sim_core — single configuration solver

**Files:**
- Create: `lib/multi_sim_core.m`
- Create: `tests/test_multi_sim.m`

This is the inner loop of the original code: given one geometry + one solution definition, run hydraulic + thermal, check temperatures, resize if needed.

- [ ] **Step 1: Write `lib/multi_sim_core.m`**

```matlab
function result = multi_sim_core(sol, geom, sources, params)
    % multi_sim_core - solve one heatsink configuration
    % Runs hydraulic + thermal pipeline, checks temperature limits,
    % auto-resizes heatsink if limits exceeded.
    %
    % sol: struct with fan/material/ventilation definition
    %   .hs_type       string -> HS_Tech lookup
    %   .fan_model     string -> Fan_Model lookup
    %   .n_fans        number of parallel fans
    %   .vent_type     'push' or 'impinge'
    %   .impinge_opening  [mm] opening for impinge mode
    % geom: struct with heatsink geometry for this iteration
    %   .a_init        [mm] initial heatsink width (perp to fins)
    %   .b_init        [mm] initial heatsink length (parallel to fins)
    %   .a_max         [mm] max width
    %   .b_max         [mm] max length
    %   .tf            [mm] fin thickness
    %   .Hf            [mm] fin height
    %   .bch           [mm] channel width (= pitch - tf)
    %   .tb            [mm] base thickness
    %   .tr            [mm] plate thickness
    % sources: struct with heat source definition
    %   .a_n           [mm] array of source widths
    %   .b_n           [mm] array of source lengths
    %   .p_n           [W]  array of source powers
    %   .x_g           [mm] array of initial source X positions
    %   .y_g           [mm] array of initial source Y positions
    %   .columns       array mapping each source to a column group
    %   .rows          array mapping each source to a row group
    %   .Tmax          [C] array of max temperatures per measurement point
    %   .scelta        'centro' or 'side'
    % params: struct with solver parameters
    %   .Tin           [C] inlet air temperature
    %   .Niter         number of Fourier iterations
    %   .piastra       'yes' or 'no'
    %   .Dx            [mm] column shift increment
    %   .Dy            [mm] row shift increment

    % Get material properties
    [Kth_plate, Kth_fin, Kth_piastra, Cost_kg, Piastra_str, rho_arr] = HS_Tech(sol.hs_type);

    % Get fan curves
    [Hv1, Qv1, Qvmin1, Qvmax1, Cost_Fan1, Vol_Fan1] = Fan_Model(sol.fan_model);
    Qv = sol.n_fans * Qv1;
    Hv = Hv1;
    Qvmin = sol.n_fans * Qvmin1;
    Qvmax = sol.n_fans * Qvmax1;

    % Initialize geometry
    a = geom.a_init;
    b = geom.b_init;
    x_g1 = sources.x_g;
    y_g1 = sources.y_g;

    % Ventilation
    if strcmp(sol.vent_type, 'impinge')
        s = sol.impinge_opening;
    else
        s = a;
    end

    % Initial air temp estimate
    Qguess = (Qvmin + Qvmax) / 2;
    Tair = params.Tin + 0.5 * sum(sources.p_n) / (Cp_air(params.Tin) * rho_air(params.Tin) * Qguess);

    % Resize loop
    Nf = round(a / (geom.bch + geom.tf));
    Ths = sources.Tmax * 2;  % force entry into loop
    max_iterations = 50;
    iter = 0;

    while any(Ths > sources.Tmax) && iter < max_iterations
        iter = iter + 1;
        Nf = round(a / (geom.bch + geom.tf));

        % Hydraulic
        [Re_hydr, Hv_f, Qv_f] = idraulico(b, s, Nf, geom.tf, geom.bch, geom.Hf, Tair, sol.vent_type, Qv, Hv);
        Tair = params.Tin + 0.5 * sum(sources.p_n) / (Cp_air(params.Tin) * rho_air(params.Tin) * Qv_f);

        % Thermal resistance
        [Re_therm, Vch1, Vch2, Rth_fin1, hf_eq] = Rth_fin(Qv_f, a, b, s, geom.tf, geom.bch, geom.Hf, Tair, sol.vent_type, Kth_fin, Nf);

        % Baseplate temperature
        LMTD = Rth_fin1 * sum(sources.p_n);
        Tfluido_out = (Tair - params.Tin) * 2 + params.Tin;
        Th_BP = (params.Tin - Tfluido_out * exp((Tfluido_out - params.Tin) / LMTD)) / ...
                (1 - exp((Tfluido_out - params.Tin) / LMTD)) - LMTD;

        % Temperature at measurement points
        [xThs, yThs] = XY_Thscalc(x_g1, y_g1, sources.a_n, sources.b_n, sources.scelta);
        Ths = zeros(1, length(sources.Tmax));
        for i = 1:length(sources.Tmax)
            [~, Ths(i)] = Temp_calc(xThs(i), yThs(i), params.Niter, params.piastra, ...
                sources.p_n, a, b, x_g1, y_g1, Kth_plate, geom.tb, ...
                sources.a_n, sources.b_n, Kth_piastra, geom.tr, Th_BP, hf_eq);
        end

        % Check if all temperatures OK
        if all(Ths <= sources.Tmax)
            break;
        end

        % Auto-resize: shift columns and rows that exceed limits
        Nmovex = 0;
        Nmovey = 0;

        if a < geom.a_max
            for nc = 1:max(sources.columns)
                c_idx = find(sources.columns == nc);
                c_higher = find(sources.columns > nc);
                if strcmp(sources.scelta, 'centro')
                    over = any(Ths(c_idx) > sources.Tmax(c_idx));
                else
                    over = any([Ths(2*c_idx-1) Ths(2*c_idx)] > [sources.Tmax(2*c_idx-1) sources.Tmax(2*c_idx)]);
                end
                if over
                    x_g1(c_idx) = x_g1(c_idx) + params.Dx;
                    x_g1(c_higher) = x_g1(c_higher) + 2 * params.Dx;
                    Nmovex = Nmovex + 1;
                end
            end
        end

        if b < geom.b_max
            for nr = 1:max(sources.rows)
                r_idx = find(sources.rows == nr);
                r_higher = find(sources.rows > nr);
                if strcmp(sources.scelta, 'centro')
                    over = any(Ths(r_idx) > sources.Tmax(r_idx));
                else
                    over = any([Ths(2*r_idx-1) Ths(2*r_idx)] > [sources.Tmax(2*r_idx-1) sources.Tmax(2*r_idx)]);
                end
                if over
                    y_g1(r_idx) = y_g1(r_idx) + params.Dy;
                    y_g1(r_higher) = y_g1(r_higher) + 2 * params.Dy;
                    Nmovey = Nmovey + 1;
                end
            end
        end

        % Update heatsink dimensions
        a_new = a + 2 * Nmovex * params.Dx;
        b_new = b + 2 * Nmovey * params.Dy;
        a = min(a_new, geom.a_max);
        b = min(b_new, geom.b_max);

        if strcmp(sol.vent_type, 'impinge')
            s = sol.impinge_opening;
        else
            s = a;
        end

        % Exit if at max size
        if a >= geom.a_max && b >= geom.b_max
            break;
        end
    end

    % Check solution validity
    if Qv_f > Qvmin && Qv_f < Qvmax
        solved_hydr = true;
    else
        solved_hydr = false;
    end
    solved_therm = all(Ths <= sources.Tmax);

    % Build result
    result.a = a;
    result.b = b;
    result.tf = geom.tf;
    result.Hf = geom.Hf;
    result.bch = geom.bch;
    result.tb = geom.tb;
    result.tr = geom.tr;
    result.Nf = Nf;
    result.Ths = Ths;
    result.Tmax = sources.Tmax;
    result.Th_BP = Th_BP;
    result.Rth_fin = Rth_fin1;
    result.hf_eq = hf_eq;
    result.Qv_f = Qv_f;
    result.Hv_f = Hv_f;
    result.Re_hydr = Re_hydr;
    result.Re_therm = Re_therm;
    result.Vch2 = Vch2;
    result.Tair = Tair;
    result.x_g = x_g1;
    result.y_g = y_g1;
    result.solved_hydr = solved_hydr;
    result.solved_therm = solved_therm;
    result.iterations = iter;
    result.sol_desc = sprintf('%s %s %dx%s', sol.hs_type, sol.vent_type, sol.n_fans, sol.fan_model);
end
```

- [ ] **Step 2: Write `tests/test_multi_sim.m`**

```matlab
function results = test_multi_sim()
    results = {};

    % Test 1: core solver runs without error on a simple config
    r.name = 'multi_sim_core: runs without error';
    try
        sol.hs_type = 'all_aluminum';
        sol.fan_model = 'EBMW1G180_axial_DC';
        sol.n_fans = 2;
        sol.vent_type = 'impinge';
        sol.impinge_opening = 250;

        geom.a_init = 400; geom.b_init = 400;
        geom.a_max = 550; geom.b_max = 600;
        geom.tf = 1.5; geom.Hf = 48; geom.bch = 2.5; geom.tb = 10; geom.tr = 10;

        sources.a_n = [110 110 110];
        sources.b_n = [80 80 80];
        sources.p_n = [710 710 710];
        sources.x_g = [100 200 300];
        sources.y_g = [200 200 200];
        sources.columns = [1 2 3];
        sources.rows = [1 1 1];
        sources.Tmax = [93 93 93];
        sources.scelta = 'centro';

        params.Tin = 25; params.Niter = 10; params.piastra = 'no';
        params.Dx = 5; params.Dy = 5;

        res = multi_sim_core(sol, geom, sources, params);
        r.pass = isstruct(res) && isfield(res, 'solved_therm') && isfield(res, 'Rth_fin');
        r.detail = sprintf('solved_therm=%d, Rth=%.4f, a=%d, b=%d, iter=%d', ...
            res.solved_therm, res.Rth_fin, res.a, res.b, res.iterations);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 2: heatsink grows when temps exceed limits
    r.name = 'multi_sim_core: heatsink grows when over temp';
    try
        % Use very high power to force resizing
        sources2 = sources;
        sources2.p_n = [2000 2000 2000];
        res2 = multi_sim_core(sol, geom, sources2, params);
        r.pass = res2.a > geom.a_init || res2.b > geom.b_init;
        r.detail = sprintf('a: %d->%d, b: %d->%d', geom.a_init, res2.a, geom.b_init, res2.b);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 3: result has all required fields
    r.name = 'multi_sim_core: result has all fields';
    try
        res = multi_sim_core(sol, geom, sources, params);
        required = {'a','b','tf','Hf','Nf','Ths','Th_BP','Rth_fin','Qv_f','solved_hydr','solved_therm'};
        missing = {};
        for i = 1:length(required)
            if ~isfield(res, required{i})
                missing{end+1} = required{i};
            end
        end
        r.pass = isempty(missing);
        r.detail = sprintf('missing: %s', strjoin(missing, ', '));
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;
end
```

- [ ] **Step 3: Run tests**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui tests/run_tests.m
```

- [ ] **Step 4: Commit**

```bash
git add lib/multi_sim_core.m tests/test_multi_sim.m
git commit -m "feat(multi-sim): add core solver with auto-resize logic

Refs: #2"
```

---

### Task 2: Create workflow_multi_sim — sweep orchestrator

**Files:**
- Create: `lib/workflow_multi_sim.m`
- Create: `configs/example_multi_sim.m`
- Modify: `thermal_cli.m`

- [ ] **Step 1: Write `configs/example_multi_sim.m`**

```matlab
function cfg = example_multi_sim()
    % Example multi-sim config (simplified from Dati_multipla.m)

    cfg.title = 'example_multi_sim';
    cfg.Tin = 25;           % [C] inlet air temperature
    cfg.Niter = 10;         % Fourier iterations (lower for speed)
    cfg.piastra = 'no';
    cfg.Dx = 5;             % [mm] column shift
    cfg.Dy = 5;             % [mm] row shift

    % Geometry sweep ranges [mm]
    cfg.sweep.tb = [10 15];
    cfg.sweep.Hf = [48 63];
    cfg.sweep.Tp = [4 5.5];      % pitch (bch = Tp - tf)
    cfg.sweep.tf = [1.5 2];
    cfg.sweep.tr = [10];

    % Heat sources [mm, W]
    cfg.sources.a_n = [110 110 110];
    cfg.sources.b_n = [80 80 80];
    cfg.sources.p_n = [710 710 710];
    cfg.sources.columns = [1 2 3];
    cfg.sources.rows = [1 1 1];
    cfg.sources.Tmax = [93 93 93];
    cfg.sources.scelta = 'centro';

    % Solutions to evaluate (each is a fan+material+geometry combo)
    cfg.solutions(1).hs_type = 'all_aluminum';
    cfg.solutions(1).fan_model = 'EBMW1G180_axial_DC';
    cfg.solutions(1).n_fans = 2;
    cfg.solutions(1).vent_type = 'impinge';
    cfg.solutions(1).impinge_opening = 250;
    cfg.solutions(1).a_init = 400;
    cfg.solutions(1).b_init = 400;
    cfg.solutions(1).a_max = 550;
    cfg.solutions(1).b_max = 600;
    cfg.solutions(1).x_g = [65 200 335];
    cfg.solutions(1).y_g = [200 200 200];
end
```

- [ ] **Step 2: Write `lib/workflow_multi_sim.m`**

```matlab
function result = workflow_multi_sim(parsed)
    % workflow_multi_sim - multi-configuration heatsink optimization
    % Sweeps geometry parameters, checks temperature limits, auto-resizes.

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m multi-sim --config <file>\n');
        fprintf('Sweeps heatsink geometry, checks temperature limits, auto-resizes.\n');
        result = struct();
        return;
    end

    cfg = cli_load_config(parsed);

    fprintf('--- Multi-Configuration Simulation: %s ---\n', cfg.title);

    params.Tin = cfg.Tin;
    params.Niter = cfg.Niter;
    params.piastra = cfg.piastra;
    params.Dx = cfg.Dx;
    params.Dy = cfg.Dy;

    all_results = {};
    count = 0;

    for ns = 1:length(cfg.solutions)
        sol = cfg.solutions(ns);

        for k1 = 1:length(cfg.sweep.tf)
            for k2 = 1:length(cfg.sweep.Hf)
                for k3 = 1:length(cfg.sweep.Tp)
                    bch = cfg.sweep.Tp(k3) - cfg.sweep.tf(k1);
                    if bch < 2
                        continue;  % channel too narrow
                    end

                    for k4 = 1:length(cfg.sweep.tb)
                        for k5 = 1:length(cfg.sweep.tr)
                            % Build geometry struct
                            geom.a_init = sol.a_init;
                            geom.b_init = sol.b_init;
                            geom.a_max = sol.a_max;
                            geom.b_max = sol.b_max;
                            geom.tf = cfg.sweep.tf(k1);
                            geom.Hf = cfg.sweep.Hf(k2);
                            geom.bch = bch;
                            geom.tb = cfg.sweep.tb(k4);
                            geom.tr = cfg.sweep.tr(k5);

                            % Build sources struct
                            sources = cfg.sources;
                            sources.x_g = sol.x_g;
                            sources.y_g = sol.y_g;

                            % Run core solver
                            count = count + 1;
                            fprintf('  [%d] %s tf=%.1f Hf=%.0f Tp=%.1f tb=%.0f tr=%.0f ... ', ...
                                count, sol.hs_type, geom.tf, geom.Hf, ...
                                cfg.sweep.Tp(k3), geom.tb, geom.tr);

                            res = multi_sim_core(sol, geom, sources, params);

                            if res.solved_therm
                                fprintf('OK (Tmax=%.0fC, a=%d, b=%d)\n', max(res.Ths), res.a, res.b);
                            else
                                fprintf('FAIL (Tmax=%.0fC, limit=%.0fC)\n', max(res.Ths), max(sources.Tmax));
                            end

                            all_results{count} = res;

                            if strcmp(cfg.piastra, 'no')
                                break;  % skip tr sweep if no plate
                            end
                        end
                    end
                end
            end
        end
    end

    % Summary table
    fprintf('\n--- Results Summary ---\n');
    fprintf('%-4s %-30s %6s %6s %5s %5s %5s %5s %6s %6s %8s %5s\n', ...
        '#', 'Solution', 'a[mm]', 'b[mm]', 'tf', 'Hf', 'tb', 'Tp', 'Rth', 'Tmax', 'Therm', 'Hydr');
    fprintf('%s\n', repmat('-', 1, 110));

    for i = 1:count
        r = all_results{i};
        fprintf('%-4d %-30s %6.0f %6.0f %5.1f %5.0f %5.0f %5.1f %6.4f %6.0f %8s %5s\n', ...
            i, r.sol_desc, r.a, r.b, r.tf, r.Hf, r.tb, r.tf + r.bch, ...
            r.Rth_fin, max(r.Ths), ...
            iif(r.solved_therm, 'OK', 'FAIL'), ...
            iif(r.solved_hydr, 'OK', 'FAIL'));
    end

    result.all_results = all_results;
    result.count = count;

    % CSV export
    if isfield(parsed, 'save_csv')
        fid = fopen(parsed.save_csv, 'w');
        fprintf(fid, 'idx,solution,a_mm,b_mm,tf_mm,Hf_mm,tb_mm,Tp_mm,Rth_fin,Tmax_C,solved_therm,solved_hydr,Qv_f,Re_hydr\n');
        for i = 1:count
            r = all_results{i};
            fprintf(fid, '%d,%s,%.0f,%.0f,%.1f,%.0f,%.0f,%.1f,%.6f,%.1f,%d,%d,%.6f,%.1f\n', ...
                i, r.sol_desc, r.a, r.b, r.tf, r.Hf, r.tb, r.tf + r.bch, ...
                r.Rth_fin, max(r.Ths), r.solved_therm, r.solved_hydr, r.Qv_f, r.Re_hydr);
        end
        fclose(fid);
        fprintf('\nResults saved to: %s\n', parsed.save_csv);
    end

    fprintf('\n--- Complete (%d configurations evaluated) ---\n', count);
end

function out = iif(cond, t, f)
    if cond, out = t; else, out = f; end
end
```

- [ ] **Step 3: Add to thermal_cli.m dispatcher**

```matlab
        case 'multi-sim'
            workflow_multi_sim(parsed);
```

- [ ] **Step 4: Test**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m multi-sim --config configs/example_multi_sim.m
```

This will take a while (multiple Fourier calculations). Use `Niter=10` and small sweep ranges in the example.

- [ ] **Step 5: Commit**

```bash
git add lib/workflow_multi_sim.m configs/example_multi_sim.m thermal_cli.m
git commit -m "feat(multi-sim): add multi-sim workflow with geometry sweep

Closes #2"
```

---

### Task 3: Final integration test and PR

- [ ] **Step 1: Run full test suite**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui tests/run_tests.m
```

- [ ] **Step 2: Push and create PR**

```bash
git push -u origin feat/issue-2-multi-sim
gh pr create --title "feat: add multi-sim workflow (Closes #2)" --body "..."
```

---

## Summary

After Phase 8:
- **1 new core function:** `multi_sim_core.m` (single config solver with auto-resize)
- **1 new workflow:** `multi-sim` (geometry sweep orchestrator)
- **1 example config:** `example_multi_sim.m`
- **3 new tests** for multi_sim_core
- Auto-resize logic preserved from original `Simulazione_Multipla.m`
- All dimensions in mm internally (matching SoftwareTermico convention)
- Config-driven (no `menu()` calls, no `Dati_multipla.m` script execution)
