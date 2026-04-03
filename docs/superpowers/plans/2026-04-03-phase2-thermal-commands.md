# Phase 2: Thermal/ Commands — Wrap OOP Code + Octave Compatibility

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix Octave classdef compatibility in ThermalLayerStack/ThermalPcb/ThermalModelSemi, wrap ThermalLayer and ThermalModelSemi as CLI commands, add the semi-on-pcb workflow, and write regression + literature tests.

**Architecture:** Same CLI dispatcher pattern from Phase 1. New `cmd_*.m` files in `lib/` call existing classes. The Octave compat fix changes object arrays (`layerArray`) to cell arrays (`layerArray{i}`).

**Tech Stack:** GNU Octave with `io` package (for xlsx in future phases). Existing classdef classes in `mfiles/Thermal/Designer/`.

**Design spec:** `docs/superpowers/specs/2026-04-03-cli-unification-design.md`

**Note:** `cmd_heatsink_create`, `cmd_heatsink_rth`, `cmd_free_conv`, and fluid property tests are deferred to Phase 2b because they depend on xlsx database loading and OPTI toolbox, which need separate setup work.

---

### Task 1: Fix ThermalLayerStack Octave compatibility

**Files:**
- Modify: `mfiles/Thermal/Designer/ThermalLayerStack.m`

The issue: Octave cannot concatenate classdef objects into arrays (`[obj.layerArray, newLayer]`). Fix: use cell arrays instead.

- [ ] **Step 1: Write a test that reproduces the failure**

Create `tests/test_thermal_layer.m`:

```matlab
function results = test_thermal_layer()
    results = {};

    % Test 1: ThermalLayer basic creation
    r.name = 'ThermalLayer: create isotropic';
    layer = ThermalLayer(0.001, 200);
    r.pass = layer.thick == 0.001 && layer.kOp == 200 && layer.kIp == 200;
    r.detail = sprintf('thick=%.4f kOp=%.1f kIp=%.1f', layer.thick, layer.kOp, layer.kIp);
    results{end+1} = r;

    % Test 2: ThermalLayer anisotropic
    r.name = 'ThermalLayer: create anisotropic';
    layer = ThermalLayer(0.001, 0.3, 200);
    r.pass = layer.thick == 0.001 && layer.kOp == 0.3 && layer.kIp == 200;
    r.detail = sprintf('kOp=%.1f kIp=%.1f', layer.kOp, layer.kIp);
    results{end+1} = r;

    % Test 3: ThermalLayer resistance without spreading (aIn only)
    r.name = 'ThermalLayer: resistance no spreading';
    layer = ThermalLayer(0.001, 200);
    rTh = layer.thermalLayerResistance(1e-4);
    expected = 0.001 / (200 * 1e-4);  % thick/(k*A) = 0.05
    r.pass = assert_near(rTh, expected, 1e-6, r.name);
    r.detail = sprintf('got %.6f, expected %.6f', rTh, expected);
    results{end+1} = r;

    % Test 4: ThermalLayer resistance with spreading (Lee model)
    % Reference: Lee et al. 1995, spreading from small source to larger area
    r.name = 'ThermalLayer: spreading resistance (Lee model)';
    layer = ThermalLayer(0.001, 200);
    aIn = 1e-4;    % 10mm x 10mm source
    aOut = 4e-4;   % 20mm x 20mm sink
    hEff = 500;    % W/(m2*K)
    [rTh, rThSpread, rThThrough] = layer.thermalLayerResistance(aIn, aOut, hEff);
    r.pass = rTh > rThThrough && rThSpread > 0 && rTh > 0;
    r.detail = sprintf('rTh=%.4f rThSpread=%.4f rThThrough=%.4f', rTh, rThSpread, rThThrough);
    results{end+1} = r;

    % Test 5: ThermalLayerStack creation and single layer
    r.name = 'ThermalLayerStack: single layer matches ThermalLayer';
    stack = ThermalLayerStack();
    stack.addLayer(ThermalLayer(0.001, 200));
    rThStack = stack.thermalLayerResistance(1e-4);
    rThSingle = ThermalLayer(0.001, 200).thermalLayerResistance(1e-4);
    r.pass = assert_near(rThStack, rThSingle, 1e-10, r.name);
    r.detail = sprintf('stack=%.6f single=%.6f', rThStack, rThSingle);
    results{end+1} = r;

    % Test 6: ThermalLayerStack multi-layer equivalent conductivity
    r.name = 'ThermalLayerStack: two-layer series resistance';
    stack = ThermalLayerStack();
    stack.addLayer(ThermalLayer(0.001, 200));   % copper 1mm
    stack.addLayer(ThermalLayer(0.0005, 0.3));  % FR4 0.5mm
    A = 1e-4;
    rThStack = stack.thermalLayerResistance(A);
    % Series: R = t1/(k1*A) + t2/(k2*A) = 0.001/(200*1e-4) + 0.0005/(0.3*1e-4)
    expected = 0.001/(200*1e-4) + 0.0005/(0.3*1e-4);  % 0.05 + 16.667 = 16.717
    r.pass = assert_near(rThStack, expected, 0.01, r.name);
    r.detail = sprintf('got %.4f, expected %.4f', rThStack, expected);
    results{end+1} = r;

    % Test 7: ThermalLayerStack with spreading
    r.name = 'ThermalLayerStack: multi-layer with spreading';
    stack = ThermalLayerStack();
    stack.addLayer(ThermalLayer(0.001, 200));
    stack.addLayer(ThermalLayer(0.0005, 0.3));
    aIn = 1e-4;
    aOut = 4e-4;
    hEff = 500;
    [rTh, rThSpread, rThThrough] = stack.thermalLayerResistance(aIn, aOut, hEff);
    r.pass = rTh > 0 && rThSpread >= 0;
    r.detail = sprintf('rTh=%.4f rThSpread=%.4f rThThrough=%.4f', rTh, rThSpread, rThThrough);
    results{end+1} = r;
end
```

- [ ] **Step 2: Run test — Tests 1-4 should pass, Tests 5-7 should fail**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui tests/run_tests.m
```

Expected: test_thermal_layer has errors on Tests 5-7 due to `octave_base_value::parent_class_name_list` error.

- [ ] **Step 3: Fix `ThermalLayerStack.m` — change layerArray to cell array**

In `mfiles/Thermal/Designer/ThermalLayerStack.m`, make these changes:

**Line 14 (constructor):** Change `obj.layerArray = [];` to `obj.layerArray = {};`

**Line 28 (addLayer):** Change:
```matlab
obj.layerArray = [obj.layerArray, newLayer];
```
to:
```matlab
obj.layerArray = [obj.layerArray, {newLayer}];
```

**Lines 114-115, 122-123, 130 (thermalLayerResistance inner loops):** Change all `obj.layerArray(idx)` to `obj.layerArray{idx}`:

Line 114: `k_i = obj.layerArray{end-i+1}.kOp;`
Line 115: `thick_i = obj.layerArray{end-i+1}.thick;`
Line 122: `k_i = obj.layerArray{i-1}.kOp;`
Line 123: `thick_i = obj.layerArray{i-1}.thick;`
Line 130: `rThL = obj.layerArray{i}.thermalLayerResistance(aIn, aOut, hEffL);`

**Lines 166-167 (kOpEquiv):** Change:
```matlab
rLam = rLam + obj.layerArray(i).thick / (obj.thick*obj.layerArray(i).kOp);
```
to:
```matlab
rLam = rLam + obj.layerArray{i}.thick / (obj.thick*obj.layerArray{i}.kOp);
```

**Line 179 (kIpEquiv):** Change:
```matlab
kSum = kSum + obj.layerArray(i).thick*obj.layerArray(i).kIp;
```
to:
```matlab
kSum = kSum + obj.layerArray{i}.thick*obj.layerArray{i}.kIp;
```

- [ ] **Step 4: Run tests — all 7 should pass**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui tests/run_tests.m
```

Expected: `test_thermal_layer ... 7/7 PASS`

- [ ] **Step 5: Commit**

```bash
git add mfiles/Thermal/Designer/ThermalLayerStack.m tests/test_thermal_layer.m
git commit -m "fix: port ThermalLayerStack to Octave-compatible cell arrays

Replace object array concatenation with cell array storage for
layerArray property. Octave cannot concatenate classdef objects
into arrays like MATLAB."
```

---

### Task 2: Fix ThermalPcb and ThermalModelSemi Octave compatibility

**Files:**
- Modify: `mfiles/Thermal/Designer/ThermalPcb.m` (line 89: `layerArray(end)` → `layerArray{end}`)
- Modify: `mfiles/Thermal/Designer/ThermalModelSemi.m` (lines 289, 291: `layerArray(1)` → `layerArray{1}`)

- [ ] **Step 1: Fix ThermalPcb.m**

In `mfiles/Thermal/Designer/ThermalPcb.m`, line 89, change:
```matlab
obj.pcbLayerStack.layerArray(end), aHeat, aCool, hEff);
```
to:
```matlab
obj.pcbLayerStack.layerArray{end}, aHeat, aCool, hEff);
```

- [ ] **Step 2: Fix ThermalModelSemi.m**

In `mfiles/Thermal/Designer/ThermalModelSemi.m`:

Line 289, change:
```matlab
topSpreadLayer = obj.pcb.pcbLayerStack.layerArray(1);
```
to:
```matlab
topSpreadLayer = obj.pcb.pcbLayerStack.layerArray{1};
```

Line 291, change:
```matlab
topSpreadLayer = obj.sinkLayerStack.layerArray(1);
```
to:
```matlab
topSpreadLayer = obj.sinkLayerStack.layerArray{1};
```

- [ ] **Step 3: Write regression test for ThermalModelSemi**

Create `tests/test_thermal_model_semi.m`:

```matlab
function results = test_thermal_model_semi()
    results = {};

    % Test 1: ThermalModelSemi pathCase 2 (bottom, no vias)
    % Based on Designer/testScript.m with pcbNumVia=0, pcbEstimateNumVia=false
    r.name = 'ThermalModelSemi: pathCase 2 bottom no vias';
    input = ThermalModelSemiInput;
    input.includeBottom = true;
    input.rThJCBottom = [0.1];
    input.areaContact = 42e-6;
    input.thInsContactPadPcb = 0;
    input.pcbLayerStack = [[0.000635, 200]; [0.0003, 400]];
    input.areaSingleVia = 1.5795e-08;
    input.kVia = 400;
    input.pcbNumVia = 0;
    input.pcbEstimateNumVia = false;
    input.thInsContactPcbSink = 7e-6;
    input.sinkLayerStack = [[0.0048, 200]];
    input.areaDissBottom = 4*42e-6;
    input.hFluidBottom = 17000;
    input.tempFluidBottom = 70;
    input.includeTop = false;
    input.rThJCTop = 2;
    input.areaCaseTop = 300e-6;
    input.areaDissTop = 900e-6;
    input.hFluidTop = 20;
    input.tempFluidTop = 70;
    input.pLossJunction = [67];
    input.tempJunctionMax = 150;

    try
        model = ThermalModelSemi(input);
        model.calcTJunction();
        output = model.output;
        r.pass = output.tJunction > input.tempFluidBottom && output.tJunction < input.tempJunctionMax;
        r.detail = sprintf('tJunction=%.2f K', output.tJunction);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 2: CSC128 module (complex PCB, 238 vias)
    r.name = 'ThermalModelSemi: CSC128 with vias';
    input2 = ThermalModelSemiInput;
    input2.includeBottom = true;
    input2.rThJCBottom = [1];
    input2.areaContact = 100e-6;
    input2.thInsContactPadPcb = 0;
    input2.pcbLayerStack = [
        [0.070e-3, 400];
        [0.214e-3, 0.3];
        [0.105e-3, 400];
        [0.3e-3, 0.3];
        [0.105e-3, 400];
        [0.26e-3, 0.3];
        [0.105e-3, 400];
        [0.3e-3, 0.3];
        [0.105e-3, 400];
        [0.26e-3, 0.3];
        [0.105e-3, 400];
        [0.3e-3, 0.3];
        [0.105e-3, 400];
        [0.214e-3, 0.3];
        [0.07e-3, 400]
    ];
    input2.areaSingleVia = pi*(0.15^2 - ((0.3-0.02)/2)^2)*1e-6;
    input2.kVia = 400;
    input2.pcbNumVia = 17*14;
    input2.pcbEstimateNumVia = false;
    input2.pcbViaSpacing = 0;
    input2.thInsContactPcbSink = 77.4e-6;
    input2.sinkLayerStack = [[0.005, 200]];
    input2.areaDissBottom = 100e-6;
    input2.hFluidBottom = 1000;
    input2.tempFluidBottom = 74;
    input2.includeTop = false;
    input2.rThJCTop = 2;
    input2.areaCaseTop = 100e-6;
    input2.areaDissTop = 100e-6;
    input2.hFluidTop = 20;
    input2.tempFluidTop = 74;
    input2.pLossJunction = [20];
    input2.tempJunctionMax = 150;

    try
        model2 = ThermalModelSemi(input2);
        model2.calcRthJunctionFluidBot();
        model2.calcTJunction();
        output2 = model2.output;
        r.pass = output2.tJunction > input2.tempFluidBottom && output2.rThCaseFluidBot > 0;
        r.detail = sprintf('tJunction=%.2f K, rThCaseFluidBot=%.4f K/W', output2.tJunction, output2.rThCaseFluidBot);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 3: Verify calcPLossMax returns positive value
    r.name = 'ThermalModelSemi: calcPLossMax positive';
    try
        model.calcPLossMax();
        output = model.output;
        r.pass = output.pLossMax > 0;
        r.detail = sprintf('pLossMax=%.2f W', output.pLossMax);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;
end
```

- [ ] **Step 4: Run tests**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui tests/run_tests.m
```

Expected: `test_thermal_model_semi ... 3/3 PASS`

- [ ] **Step 5: Commit**

```bash
git add mfiles/Thermal/Designer/ThermalPcb.m mfiles/Thermal/Designer/ThermalModelSemi.m tests/test_thermal_model_semi.m
git commit -m "fix: port ThermalPcb and ThermalModelSemi to Octave cell arrays

Update layerArray indexing from () to {} in ThermalPcb and
ThermalModelSemi to match ThermalLayerStack cell array change.
Add regression tests for ThermalModelSemi pipeline."
```

---

### Task 3: Implement cmd_layer_rth and cmd_stack_rth

**Files:**
- Create: `lib/cmd_layer_rth.m`
- Create: `lib/cmd_stack_rth.m`
- Modify: `thermal_cli.m` (add cases to dispatcher)

- [ ] **Step 1: Write `lib/cmd_layer_rth.m`**

```matlab
function result = cmd_layer_rth(parsed)
    % cmd_layer_rth - calculate thermal resistance through a single layer
    % Usage: thermal_cli.m layer-rth --thick <m> --kop <W/mK> [--kip <W/mK>] --ain <m2> [--aout <m2>] [--heff <W/m2K>]

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m layer-rth --thick <m> --kop <W/mK> [--kip <W/mK>] --ain <m2> [--aout <m2>] [--heff <W/m2K>]\n');
        fprintf('Calculates thermal resistance through a single material layer.\n');
        fprintf('  --thick   Layer thickness [m]\n');
        fprintf('  --kop     Out-of-plane thermal conductivity [W/(m*K)]\n');
        fprintf('  --kip     In-plane thermal conductivity [W/(m*K)] (optional, defaults to kop)\n');
        fprintf('  --ain     Heat source area [m2]\n');
        fprintf('  --aout    Heat sink area [m2] (optional, for spreading calculation)\n');
        fprintf('  --heff    Effective heat transfer coefficient [W/(m2*K)] (required if aout != ain)\n');
        result = struct();
        return;
    end

    thick = str2double(parsed.thick);
    kOp = str2double(parsed.kop);

    if isfield(parsed, 'kip')
        kIp = str2double(parsed.kip);
        layer = ThermalLayer(thick, kOp, kIp);
    else
        layer = ThermalLayer(thick, kOp);
    end

    aIn = str2double(parsed.ain);

    if isfield(parsed, 'aout') && isfield(parsed, 'heff')
        aOut = str2double(parsed.aout);
        hEff = str2double(parsed.heff);
        [rTh, rThSpread, rThThrough] = layer.thermalLayerResistance(aIn, aOut, hEff);
        result.rth = rTh;
        result.rth_spread = rThSpread;
        result.rth_through = rThThrough;
        fprintf('rth=%.6f\n', rTh);
        fprintf('rth_spread=%.6f\n', rThSpread);
        fprintf('rth_through=%.6f\n', rThThrough);
    else
        rTh = layer.thermalLayerResistance(aIn);
        result.rth = rTh;
        fprintf('rth=%.6f\n', rTh);
    end
end
```

- [ ] **Step 2: Write `lib/cmd_stack_rth.m`**

```matlab
function result = cmd_stack_rth(parsed)
    % cmd_stack_rth - calculate thermal resistance through a layer stack
    % Usage: thermal_cli.m stack-rth --config <file> [--ain <m2>] [--aout <m2>] [--heff <W/m2K>]

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m stack-rth --config <file> [--ain <m2>] [--aout <m2>] [--heff <W/m2K>]\n');
        fprintf('Calculates thermal resistance through a multi-layer stack.\n');
        fprintf('Config must define cfg.layers as [[thick1,kOp1]; [thick2,kOp2]; ...] or\n');
        fprintf('  [[thick1,kOp1,kIp1]; [thick2,kOp2,kIp2]; ...]\n');
        fprintf('  --ain     Heat source area [m2]\n');
        fprintf('  --aout    Heat sink area [m2] (optional)\n');
        fprintf('  --heff    Effective heat transfer coefficient [W/(m2*K)] (required if aout given)\n');
        result = struct();
        return;
    end

    cfg = cli_load_config(parsed);

    stack = ThermalLayerStack();
    for i = 1:size(cfg.layers, 1)
        row = cfg.layers(i, :);
        if length(row) == 3
            stack.addLayer(ThermalLayer(row(1), row(2), row(3)));
        else
            stack.addLayer(ThermalLayer(row(1), row(2)));
        end
    end

    aIn = str2double(parsed.ain);

    if isfield(parsed, 'aout') && isfield(parsed, 'heff')
        aOut = str2double(parsed.aout);
        hEff = str2double(parsed.heff);
        [rTh, rThSpread, rThThrough] = stack.thermalLayerResistance(aIn, aOut, hEff);
        result.rth = rTh;
        result.rth_spread = rThSpread;
        result.rth_through = rThThrough;
        fprintf('rth=%.6f\n', rTh);
        fprintf('rth_spread=%.6f\n', rThSpread);
        fprintf('rth_through=%.6f\n', rThThrough);
    else
        rTh = stack.thermalLayerResistance(aIn);
        result.rth = rTh;
        fprintf('rth=%.6f\n', rTh);
    end

    fprintf('n_layers=%d\n', stack.n);
    fprintf('total_thick=%.6f\n', stack.thick);
    fprintf('kop_equiv=%.6f\n', stack.kOp);
    result.n_layers = stack.n;
    result.total_thick = stack.thick;
    result.kop_equiv = stack.kOp;
end
```

- [ ] **Step 3: Add dispatcher cases in `thermal_cli.m`**

Add these two cases to the switch statement in `thermal_cli.m`, after the `'radiation'` case:

```matlab
        case 'layer-rth'
            cmd_layer_rth(parsed);
        case 'stack-rth'
            cmd_stack_rth(parsed);
```

- [ ] **Step 4: Test via CLI**

```bash
cd /home/tinix/claude_wsl/octave/thermal

# layer-rth without spreading
octave --no-gui thermal_cli.m layer-rth --thick 0.001 --kop 200 --ain 1e-4

# layer-rth with spreading
octave --no-gui thermal_cli.m layer-rth --thick 0.001 --kop 200 --ain 1e-4 --aout 4e-4 --heff 500
```

Expected first: `rth=0.050000`
Expected second: `rth=...` with spread/through breakdown

- [ ] **Step 5: Commit**

```bash
git add lib/cmd_layer_rth.m lib/cmd_stack_rth.m thermal_cli.m
git commit -m "feat: add layer-rth and stack-rth CLI commands"
```

---

### Task 4: Implement workflow_semi_on_pcb

**Files:**
- Create: `lib/workflow_semi_on_pcb.m`
- Create: `configs/example_semi_on_pcb.m`
- Modify: `thermal_cli.m` (add case)

- [ ] **Step 1: Write `configs/example_semi_on_pcb.m`**

```matlab
function cfg = example_semi_on_pcb()
    % Example: semiconductor on PCB (from Designer/testScript.m)
    cfg.includeBottom = true;
    cfg.rThJCBottom = [0.1];
    cfg.areaContact = 42e-6;
    cfg.thInsContactPadPcb = 0;
    cfg.pcbLayerStack = [[0.000635, 200]; [0.0003, 400]];
    cfg.areaSingleVia = 1.5795e-08;
    cfg.kVia = 400;
    cfg.pcbNumVia = 0;
    cfg.pcbEstimateNumVia = false;
    cfg.pcbViaSpacing = 0;
    cfg.thInsContactPcbSink = 7e-6;
    cfg.sinkLayerStack = [[0.0048, 200]];
    cfg.areaDissBottom = 4*42e-6;
    cfg.hFluidBottom = 17000;
    cfg.tempFluidBottom = 70;

    cfg.includeTop = false;
    cfg.rThJCTop = 2;
    cfg.areaCaseTop = 300e-6;
    cfg.areaDissTop = 900e-6;
    cfg.hFluidTop = 20;
    cfg.tempFluidTop = 70;

    cfg.pLossJunction = [67];
    cfg.tempJunctionMax = 150;
end
```

- [ ] **Step 2: Write `lib/workflow_semi_on_pcb.m`**

```matlab
function result = workflow_semi_on_pcb(parsed)
    % workflow_semi_on_pcb - full ThermalModelSemi pipeline
    % Usage: thermal_cli.m semi-on-pcb --config <file> [overrides]

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m semi-on-pcb --config <file>\n');
        fprintf('Runs full semiconductor-on-PCB thermal model.\n');
        fprintf('Config must define all ThermalModelSemiInput fields.\n');
        result = struct();
        return;
    end

    cfg = cli_load_config(parsed);

    % Build ThermalModelSemiInput from config
    input = ThermalModelSemiInput;

    input.includeBottom = cfg.includeBottom;
    input.rThJCBottom = cfg.rThJCBottom;
    input.areaContact = cfg.areaContact;
    input.thInsContactPadPcb = cfg.thInsContactPadPcb;
    input.pcbLayerStack = cfg.pcbLayerStack;
    input.areaSingleVia = cfg.areaSingleVia;
    input.kVia = cfg.kVia;
    input.pcbNumVia = cfg.pcbNumVia;
    input.pcbEstimateNumVia = cfg.pcbEstimateNumVia;
    input.pcbViaSpacing = cfg.pcbViaSpacing;
    input.thInsContactPcbSink = cfg.thInsContactPcbSink;
    input.sinkLayerStack = cfg.sinkLayerStack;
    input.areaDissBottom = cfg.areaDissBottom;
    input.hFluidBottom = cfg.hFluidBottom;
    input.tempFluidBottom = cfg.tempFluidBottom;

    input.includeTop = cfg.includeTop;
    input.rThJCTop = cfg.rThJCTop;
    input.areaCaseTop = cfg.areaCaseTop;
    input.areaDissTop = cfg.areaDissTop;
    input.hFluidTop = cfg.hFluidTop;
    input.tempFluidTop = cfg.tempFluidTop;

    input.pLossJunction = cfg.pLossJunction;
    input.tempJunctionMax = cfg.tempJunctionMax;

    % Run model
    fprintf('--- Semi-on-PCB Thermal Model ---\n');
    model = ThermalModelSemi(input);

    if input.includeBottom
        model.calcRthJunctionFluidBot();
        fprintf('rth_junction_fluid_bot=%.6f\n', model.output.rThCaseFluidBot);
    end

    model.calcTJunction();
    tJ = model.output.tJunction;
    for i = 1:length(tJ)
        fprintf('t_junction_%d=%.4f\n', i, tJ(i));
    end

    model.calcPLossMax();
    fprintf('p_loss_max=%.4f\n', model.output.pLossMax);

    model.calcADissMin();
    fprintf('a_diss_min=%.6e\n', model.output.aDissipationMin);

    model.calcHFluidMin();
    fprintf('h_fluid_min=%.4f\n', model.output.hFluidMin);

    fprintf('pcb_num_via=%d\n', model.output.pcbNumVia);
    fprintf('--- Complete ---\n');

    % Build result struct
    result.rThCaseFluidBot = model.output.rThCaseFluidBot;
    result.tJunction = model.output.tJunction;
    result.pLossMax = model.output.pLossMax;
    result.aDissipationMin = model.output.aDissipationMin;
    result.hFluidMin = model.output.hFluidMin;
    result.pcbNumVia = model.output.pcbNumVia;

    % FEMM Lua generation if requested
    if isfield(parsed, 'femm_lua')
        lua_str = femm_semi_on_pcb(cfg);
        fid = fopen(parsed.femm_lua, 'w');
        fprintf(fid, '%s', lua_str);
        fclose(fid);
        fprintf('FEMM Lua script written to: %s\n', parsed.femm_lua);
    end
end
```

- [ ] **Step 3: Add dispatcher case in `thermal_cli.m`**

Add after the `'stack-rth'` case:
```matlab
        case 'semi-on-pcb'
            workflow_semi_on_pcb(parsed);
```

- [ ] **Step 4: Test via CLI**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m semi-on-pcb --config configs/example_semi_on_pcb.m
```

Expected: prints rth, junction temperature, pLossMax, etc. without errors.

- [ ] **Step 5: Commit**

```bash
git add lib/workflow_semi_on_pcb.m configs/example_semi_on_pcb.m thermal_cli.m
git commit -m "feat: add semi-on-pcb workflow with example config"
```

---

### Task 5: Add --save-csv flag to workflow_semi_on_pcb

**Files:**
- Modify: `lib/workflow_semi_on_pcb.m`

This enables analytical result export for later FEMM comparison.

- [ ] **Step 1: Add CSV export to `workflow_semi_on_pcb.m`**

Add this block after the result struct is built, before the FEMM Lua section:

```matlab
    % CSV export if requested
    if isfield(parsed, 'save_csv')
        fid = fopen(parsed.save_csv, 'w');
        fprintf(fid, 'point,value,unit\n');
        for i = 1:length(tJ)
            fprintf(fid, 'junction_temperature_%d,%.6f,K\n', i, tJ(i));
        end
        if input.includeBottom
            fprintf(fid, 'rth_junction_fluid_bot,%.6f,K/W\n', model.output.rThCaseFluidBot);
        end
        fprintf(fid, 'p_loss_max,%.6f,W\n', model.output.pLossMax);
        fprintf(fid, 'a_diss_min,%.6e,m2\n', model.output.aDissipationMin);
        fprintf(fid, 'h_fluid_min,%.6f,W/(m2*K)\n', model.output.hFluidMin);
        fclose(fid);
        fprintf('Analytical results saved to: %s\n', parsed.save_csv);
    end
```

- [ ] **Step 2: Test CSV export**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui thermal_cli.m semi-on-pcb --config configs/example_semi_on_pcb.m --save-csv /tmp/test_result.csv && cat /tmp/test_result.csv
```

Expected: CSV with point,value,unit rows.

- [ ] **Step 3: Commit**

```bash
git add lib/workflow_semi_on_pcb.m
git commit -m "feat: add --save-csv flag to semi-on-pcb workflow"
```

---

### Task 6: Final integration test

- [ ] **Step 1: Run full test suite**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui tests/run_tests.m
```

Expected: All tests pass (21 from Phase 1 + 7 thermal_layer + 3 thermal_model_semi = 31 total).

- [ ] **Step 2: Test all new CLI commands**

```bash
cd /home/tinix/claude_wsl/octave/thermal

octave --no-gui thermal_cli.m layer-rth --help
octave --no-gui thermal_cli.m layer-rth --thick 0.001 --kop 200 --ain 1e-4
octave --no-gui thermal_cli.m layer-rth --thick 0.001 --kop 200 --ain 1e-4 --aout 4e-4 --heff 500
octave --no-gui thermal_cli.m semi-on-pcb --config configs/example_semi_on_pcb.m
octave --no-gui thermal_cli.m semi-on-pcb --config configs/example_semi_on_pcb.m --save-csv /tmp/test.csv
```

All should work without errors.

- [ ] **Step 3: Commit any fixups**

```bash
git add -p
git commit -m "fix: phase 2 integration fixups"
```

---

## Summary

After Phase 2, the project has:
- **Octave compatibility fixes** for ThermalLayerStack, ThermalPcb, ThermalModelSemi (cell arrays)
- **2 new CLI commands:** `layer-rth`, `stack-rth`
- **1 new workflow:** `semi-on-pcb` with `--save-csv` flag
- **1 example config:** `configs/example_semi_on_pcb.m`
- **10 new tests:** 7 thermal_layer + 3 thermal_model_semi
- **Total: ~31 tests, all passing**

**Deferred to Phase 2b:**
- `cmd_heatsink_create`, `cmd_heatsink_rth` (need xlsx database loading setup)
- `cmd_free_conv` (needs OPTI toolbox or alternative solver)
- `cmd_water_cooling` (simple, can be added anytime)
- `test_fluid_properties.m`, `test_heatsink_model.m`
- `workflow_extruded_fin`
