# Phase 6: CSPI Metric, Drofenik Channel Model & Heat Transfer Coefficients

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add CSPI metric and optimizer (Drofenik/Kolar), port the ntbees2 channel model with Drofenik correlations, add standalone heat transfer coefficient commands, and add fan scaling law fit tool.

**Architecture:** New standalone functions in `lib/` following the same `cmd_*.m` pattern. The Drofenik channel model is self-contained (no dependency on SoftwareTermico). Fluid properties via simple struct OR auto-filled from GasProperty/LiquidProperty.

**References:**
- Drofenik & Kolar, CIPS06: "Analyzing the Theoretical Limits of Forced Air-Cooling..."
- Drofenik & Kolar, CIPS08: "Thermal Power Density Barriers..."
- Drofenik & Kolar, PCC07: "Sub-Optimum Design of a Forced Air Cooled Heat Sink..."
- ntbees2 code: `/home/tinix/claude_wsl/archive_ntbees2/total_optimal2/`

---

### Task 1: Port h-forced, h-natural, h-radiation as standalone commands

**Files:**
- Create: `lib/h_forced_convection.m`
- Create: `lib/h_natural_convection.m`
- Create: `lib/h_radiation.m`
- Create: `lib/cmd_h_coeff.m`
- Create: `tests/test_h_coefficients.m`
- Modify: `thermal_cli.m`

These are direct ports from ntbees2 `heat_transfer_coefficient/` with a unified CLI command `h-coeff --mode forced|natural|radiation`.

- [ ] **Step 1: Create `lib/h_forced_convection.m`**

Port from ntbees2. Function signature:
```matlab
function [h, Re] = h_forced_convection(L, U, T_ambient, T_surface)
    % h_forced_convection - forced convection heat transfer coefficient
    % Flat plate correlation (Incropera Ch.7)
    %   L: characteristic length [m]
    %   U: air velocity [m/s]
    %   T_ambient: ambient temperature [C]
    %   T_surface: surface temperature [C]
    %   Returns: h [W/(m2*K)], Re [-]

    T0 = 273.15;
    rho = @(T)(101325 / 287.058 / T);
    mu = @(T)(18.27e-6 * (291.15 + 120) / (T + 120) * (T / 291.15)^(3/2));
    Pr = 0.71;
    kf = @(T)(7e-5 * T + 5.1e-3);

    Ta = T_ambient + T0;
    Ts = T_surface + T0;
    Tf = (Ta + Ts) / 2;

    Re = rho(Tf) * U * L / mu(Tf);

    if Re < 5e5
        h = 0.664 * Re^(1/2) * Pr^(1/3) * kf(Tf) / L;
    else
        h = (0.037 * Re^(4/5) - 18030) * Pr^(1/3) * kf(Tf) / L;
    end
end
```

- [ ] **Step 2: Create `lib/h_natural_convection.m`**

```matlab
function [h, Ra] = h_natural_convection(orientation, L, T_ambient, T_surface)
    % h_natural_convection - natural convection heat transfer coefficient
    %   orientation: 'vertical', 'horizontal_top', 'horizontal_bottom'
    %   L: characteristic length [m]
    %   T_ambient, T_surface: temperatures [C]
    %   Returns: h [W/(m2*K)], Ra [-]

    T0 = 273.15;
    rho = @(T)(101325 / 287.058 / T);
    beta = @(T)(1 / T);
    mu = @(T)(18.27e-6 * (291.15 + 120) / (T + 120) * (T / 291.15)^(3/2));
    Pr = 0.71;
    kf = @(T)(7e-5 * T + 5.1e-3);

    Ta = T_ambient + T0;
    Ts = T_surface + T0;
    Tf = (Ta + Ts) / 2;

    Ra = Pr * rho(Tf)^2 * 9.81 * beta(Tf) * (Ts - Ta) * L^3 / mu(Tf)^2;

    switch orientation
        case 'vertical'
            if Ra < 1e9
                h = 0.59 * Ra^(1/4) * kf(Tf) / L;
            else
                h = 0.1 * Ra^(1/3) * kf(Tf) / L;
            end
        case 'horizontal_top'
            if Ra < 1e7
                h = 0.54 * Ra^(1/4) * kf(Tf) / L;
            else
                h = 0.15 * Ra^(1/3) * kf(Tf) / L;
            end
        case 'horizontal_bottom'
            h = 0.27 * Ra^(1/4) * kf(Tf) / L;
        otherwise
            error('Unknown orientation: %s. Use vertical, horizontal_top, or horizontal_bottom.', orientation);
    end
end
```

- [ ] **Step 3: Create `lib/h_radiation.m`**

```matlab
function h = h_radiation(epsilon, T_ambient, T_surface)
    % h_radiation - linearized radiation heat transfer coefficient
    %   epsilon: surface emissivity [-]
    %   T_ambient, T_surface: temperatures [C]
    %   Returns: h [W/(m2*K)]

    T0 = 273.15;
    Ta = T_ambient + T0;
    Ts = T_surface + T0;
    h = epsilon * 5.67e-8 * (Ts^2 + Ta^2) * (Ts + Ta);
end
```

- [ ] **Step 4: Create `lib/cmd_h_coeff.m`**

```matlab
function result = cmd_h_coeff(parsed)
    % cmd_h_coeff - heat transfer coefficient calculator
    % Usage: thermal_cli.m h-coeff --mode forced|natural|radiation [options]

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m h-coeff --mode <type> [options]\n\n');
        fprintf('Modes:\n');
        fprintf('  forced     --length <m> --velocity <m/s> --t-ambient <C> --t-surface <C>\n');
        fprintf('  natural    --orientation <vertical|horizontal_top|horizontal_bottom> --length <m> --t-ambient <C> --t-surface <C>\n');
        fprintf('  radiation  --epsilon <-> --t-ambient <C> --t-surface <C>\n');
        result = struct();
        return;
    end

    if ~isfield(parsed, 'mode')
        fprintf(2, 'Error: --mode is required (forced|natural|radiation)\n');
        result = struct();
        return;
    end

    switch parsed.mode
        case 'forced'
            L = str2double(parsed.length);
            U = str2double(parsed.velocity);
            Ta = str2double(parsed.t_ambient);
            Ts = str2double(parsed.t_surface);
            [h, Re] = h_forced_convection(L, U, Ta, Ts);
            result.h = h;
            result.Re = Re;
            fprintf('h=%.4f\n', h);
            fprintf('Re=%.1f\n', Re);

        case 'natural'
            orient = parsed.orientation;
            L = str2double(parsed.length);
            Ta = str2double(parsed.t_ambient);
            Ts = str2double(parsed.t_surface);
            [h, Ra] = h_natural_convection(orient, L, Ta, Ts);
            result.h = h;
            result.Ra = Ra;
            fprintf('h=%.4f\n', h);
            fprintf('Ra=%.2e\n', Ra);

        case 'radiation'
            eps = str2double(parsed.epsilon);
            Ta = str2double(parsed.t_ambient);
            Ts = str2double(parsed.t_surface);
            h = h_radiation(eps, Ta, Ts);
            result.h = h;
            fprintf('h=%.4f\n', h);

        otherwise
            fprintf(2, 'Error: unknown mode "%s"\n', parsed.mode);
            result = struct();
    end
end
```

- [ ] **Step 5: Create `tests/test_h_coefficients.m`**

```matlab
function results = test_h_coefficients()
    results = {};

    % --- h_forced_convection ---
    % Flat plate, laminar: h = 0.664 * Re^0.5 * Pr^(1/3) * k/L
    r.name = 'h_forced: laminar flat plate 1m/s';
    [h, Re] = h_forced_convection(0.05, 1, 40, 80);
    r.pass = h > 5 && h < 50 && Re < 5e5;
    r.detail = sprintf('h=%.2f W/(m2K), Re=%.0f', h, Re);
    results{end+1} = r;

    r.name = 'h_forced: higher velocity increases h';
    [h1, ~] = h_forced_convection(0.05, 1, 40, 80);
    [h2, ~] = h_forced_convection(0.05, 5, 40, 80);
    r.pass = h2 > h1;
    r.detail = sprintf('h(1m/s)=%.2f, h(5m/s)=%.2f', h1, h2);
    results{end+1} = r;

    % --- h_natural_convection ---
    r.name = 'h_natural: vertical plate';
    [h, Ra] = h_natural_convection('vertical', 0.05, 40, 80);
    r.pass = h > 3 && h < 30 && Ra > 0;
    r.detail = sprintf('h=%.2f W/(m2K), Ra=%.2e', h, Ra);
    results{end+1} = r;

    r.name = 'h_natural: horizontal_top > horizontal_bottom';
    [h_top, ~] = h_natural_convection('horizontal_top', 0.05, 40, 80);
    [h_bot, ~] = h_natural_convection('horizontal_bottom', 0.05, 40, 80);
    r.pass = h_top > h_bot;
    r.detail = sprintf('h_top=%.2f, h_bot=%.2f', h_top, h_bot);
    results{end+1} = r;

    % --- h_radiation ---
    % At 80C surface, 40C ambient: h_rad ~ 6-7 W/(m2K) for eps=0.9
    r.name = 'h_radiation: typical value at 80C';
    h = h_radiation(0.9, 40, 80);
    r.pass = assert_near(h, 6.5, 1.5, r.name);
    r.detail = sprintf('h=%.2f W/(m2K)', h);
    results{end+1} = r;

    r.name = 'h_radiation: blackbody at 100C';
    h = h_radiation(1.0, 25, 100);
    r.pass = h > 6 && h < 12;
    r.detail = sprintf('h=%.2f W/(m2K)', h);
    results{end+1} = r;
end
```

- [ ] **Step 6: Add to thermal_cli.m dispatcher**

```matlab
        case 'h-coeff'
            cmd_h_coeff(parsed);
```

- [ ] **Step 7: Run tests, commit**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui tests/run_tests.m
git add lib/h_forced_convection.m lib/h_natural_convection.m lib/h_radiation.m lib/cmd_h_coeff.m tests/test_h_coefficients.m thermal_cli.m
git commit -m "feat: add h-coeff command (forced/natural/radiation heat transfer coefficients)"
```

---

### Task 2: Port Drofenik channel model

**Files:**
- Create: `lib/channel_rth.m`
- Create: `lib/channel_pressure_drop.m`
- Create: `lib/air_properties.m`
- Create: `lib/cmd_channel_rth.m`
- Create: `lib/cmd_channel_dp.m`
- Create: `tests/test_channel_model.m`
- Modify: `thermal_cli.m`

Port from ntbees2 `@channel/private/calc_thermal_resistance_from_flow_rate.m` and `calc_pressure_drop_from_flow_rate.m`. These use the Drofenik/Shabany correlations.

- [ ] **Step 1: Create `lib/air_properties.m`**

Helper to create a fluid struct at a reference temperature.

```matlab
function fluid = air_properties(T_ref_C)
    % air_properties - returns air property struct at reference temperature
    %   T_ref_C: reference temperature [C] (default 80)
    %   Returns struct with fields needed by channel model

    if nargin == 0
        T_ref_C = 80;
    end

    T0 = 273.15;
    T = T_ref_C + T0;

    fluid.density = 101325 / 287.058 / T;
    fluid.cinematic_viscosity = 18.27e-6 * (291.15 + 120) / (T + 120) * (T / 291.15)^(3/2) / fluid.density;
    fluid.prandtl_number = 0.71;
    fluid.thermal_conductivity = 7e-5 * T + 5.1e-3;
    fluid.heat_capacity = 1010;
    fluid.temperature = T_ref_C;
end
```

- [ ] **Step 2: Create `lib/channel_rth.m`**

```matlab
function [rth, Re, Nu, h] = channel_rth(geom, flow_rate, fluid)
    % channel_rth - thermal resistance of a rectangular or circular channel
    % Drofenik/Shabany correlations with entrance effects
    %   geom: struct with .width, .height (or .diameter), .length [m]
    %   flow_rate: volumetric flow rate per channel [m3/s]
    %   fluid: struct with .density, .cinematic_viscosity, .prandtl_number,
    %          .thermal_conductivity, .heat_capacity
    %   Returns: rth [K/W], Re [-], Nu [-], h [W/(m2*K)]

    if isfield(geom, 'diameter')
        dh = geom.diameter;
        Ac = (geom.diameter / 2)^2 * pi;
        P = pi * geom.diameter;
    else
        dh = 4 * geom.width * geom.height / 2 / (geom.height + geom.width);
        Ac = geom.width * geom.height;
        P = 2 * (geom.width + geom.height);
    end

    v = flow_rate / Ac;
    Re = v * dh / fluid.cinematic_viscosity;

    if Re <= 2300
        % Laminar: Baehr/Stephan correlation with entrance effects
        x = geom.length / dh / Re / fluid.prandtl_number;
        Nu = (3.657 / tanh(2.264 * x^(1/3) + 1.7 * x^(2/3)) + 0.0499 * tanh(x) / x) / ...
             tanh(2.432 * fluid.prandtl_number^(1/6) * x^(1/6));
    else
        % Turbulent: Gnielinski correlation with entrance effects
        f = 1 / (8 * (0.79 * log(Re) - 1.64)^2);
        Nu = (Re - 1000) * fluid.prandtl_number * (1 + (dh / geom.length)^(2/3)) / ...
             (8 * (0.79 * log(Re) - 1.64)^2) / ...
             (1 + 12.7 * sqrt(f) * (fluid.prandtl_number^(2/3) - 1));
    end

    h = Nu * fluid.thermal_conductivity / dh;
    rth = 1 / (h * geom.length * P) + 0.5 / (fluid.density * fluid.heat_capacity * flow_rate);
end
```

- [ ] **Step 3: Create `lib/channel_pressure_drop.m`**

```matlab
function [dp, Re] = channel_pressure_drop(geom, flow_rate, fluid)
    % channel_pressure_drop - pressure drop in a rectangular or circular channel
    % Drofenik/Shabany correlations
    %   geom: struct with .width, .height (or .diameter), .length [m]
    %   flow_rate: volumetric flow rate per channel [m3/s]
    %   fluid: struct with .density, .cinematic_viscosity
    %   Returns: dp [Pa], Re [-]

    if isfield(geom, 'diameter')
        dh = geom.diameter;
        ff = 64;
        Ac = (geom.diameter / 2)^2 * pi;
        P = pi * geom.diameter;
    else
        dh = 4 * geom.width * geom.height / 2 / (geom.height + geom.width);
        ratio = max([geom.width geom.height]) / min([geom.width geom.height]);
        if ratio <= 14
            ff = interp1([1 1.43 2 3 4 8 14], [57 59 62 69 73 82 96], ratio, 'linear');
        else
            ff = 96;
        end
        Ac = geom.width * geom.height;
        P = 2 * (geom.width + geom.height);
    end

    v = flow_rate / Ac;
    Re = v * dh / fluid.cinematic_viscosity;

    if Re <= 2300
        dp = ff * fluid.density * fluid.cinematic_viscosity * geom.length * flow_rate / ...
             (2 * Ac * dh^2);
    else
        dp = geom.length * fluid.density * 0.5 * v^2 / ...
             (dh * (0.79 * log(4 * flow_rate / P / fluid.cinematic_viscosity) - 1.64)^2);
    end
end
```

- [ ] **Step 4: Create `lib/cmd_channel_rth.m` and `lib/cmd_channel_dp.m`**

```matlab
% cmd_channel_rth.m
function result = cmd_channel_rth(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m channel-rth --width <m> --height <m> --length <m> --flowrate <m3/s> [--t-air <C>]\n');
        fprintf('Drofenik channel thermal resistance model.\n');
        result = struct();
        return;
    end

    geom.width = str2double(parsed.width);
    geom.height = str2double(parsed.height);
    geom.length = str2double(parsed.length);
    fr = str2double(parsed.flowrate);

    if isfield(parsed, 't_air')
        fluid = air_properties(str2double(parsed.t_air));
    else
        fluid = air_properties(80);
    end

    [rth, Re, Nu, h] = channel_rth(geom, fr, fluid);

    result.rth = rth;
    result.Re = Re;
    result.Nu = Nu;
    result.h = h;
    fprintf('rth=%.6f\n', rth);
    fprintf('Re=%.1f\n', Re);
    fprintf('Nu=%.2f\n', Nu);
    fprintf('h=%.2f\n', h);
end
```

```matlab
% cmd_channel_dp.m
function result = cmd_channel_dp(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m channel-dp --width <m> --height <m> --length <m> --flowrate <m3/s> [--t-air <C>]\n');
        fprintf('Drofenik channel pressure drop model.\n');
        result = struct();
        return;
    end

    geom.width = str2double(parsed.width);
    geom.height = str2double(parsed.height);
    geom.length = str2double(parsed.length);
    fr = str2double(parsed.flowrate);

    if isfield(parsed, 't_air')
        fluid = air_properties(str2double(parsed.t_air));
    else
        fluid = air_properties(80);
    end

    [dp, Re] = channel_pressure_drop(geom, fr, fluid);

    result.dp = dp;
    result.Re = Re;
    fprintf('dp=%.4f\n', dp);
    fprintf('Re=%.1f\n', Re);
end
```

- [ ] **Step 5: Create `tests/test_channel_model.m`**

```matlab
function results = test_channel_model()
    results = {};

    fluid = air_properties(80);

    % Test 1: laminar channel Rth
    r.name = 'channel_rth: laminar Re<2300';
    geom.width = 1e-3;
    geom.height = 40e-3;
    geom.length = 80e-3;
    [rth, Re, ~, ~] = channel_rth(geom, 1e-4, fluid);
    r.pass = Re < 2300 && rth > 0;
    r.detail = sprintf('rth=%.4f K/W, Re=%.1f', rth, Re);
    results{end+1} = r;

    % Test 2: increasing flow reduces Rth
    r.name = 'channel_rth: more flow -> lower Rth';
    [rth1, ~, ~, ~] = channel_rth(geom, 1e-4, fluid);
    [rth2, ~, ~, ~] = channel_rth(geom, 5e-4, fluid);
    r.pass = rth2 < rth1;
    r.detail = sprintf('rth(1e-4)=%.4f, rth(5e-4)=%.4f', rth1, rth2);
    results{end+1} = r;

    % Test 3: pressure drop laminar
    r.name = 'channel_dp: laminar positive';
    [dp, Re] = channel_pressure_drop(geom, 1e-4, fluid);
    r.pass = dp > 0 && Re < 2300;
    r.detail = sprintf('dp=%.2f Pa, Re=%.1f', dp, Re);
    results{end+1} = r;

    % Test 4: pressure drop increases with flow
    r.name = 'channel_dp: more flow -> more dp';
    [dp1, ~] = channel_pressure_drop(geom, 1e-4, fluid);
    [dp2, ~] = channel_pressure_drop(geom, 5e-4, fluid);
    r.pass = dp2 > dp1;
    r.detail = sprintf('dp(1e-4)=%.2f, dp(5e-4)=%.2f', dp1, dp2);
    results{end+1} = r;

    % Test 5: rectangular friction factor interpolation
    r.name = 'channel_dp: square channel ff=57';
    geom_sq.width = 5e-3;
    geom_sq.height = 5e-3;
    geom_sq.length = 80e-3;
    [dp_sq, Re_sq] = channel_pressure_drop(geom_sq, 1e-4, fluid);
    r.pass = dp_sq > 0 && Re_sq > 0;
    r.detail = sprintf('dp=%.4f Pa, Re=%.1f (square)', dp_sq, Re_sq);
    results{end+1} = r;

    % Test 6: air_properties returns valid struct
    r.name = 'air_properties: valid at 80C';
    f = air_properties(80);
    r.pass = f.density > 0.9 && f.density < 1.1 && f.prandtl_number == 0.71;
    r.detail = sprintf('rho=%.3f, nu=%.2e, Pr=%.2f', f.density, f.cinematic_viscosity, f.prandtl_number);
    results{end+1} = r;
end
```

- [ ] **Step 6: Add to dispatcher, run tests, commit**

```bash
git add lib/air_properties.m lib/channel_rth.m lib/channel_pressure_drop.m lib/cmd_channel_rth.m lib/cmd_channel_dp.m tests/test_channel_model.m thermal_cli.m
git commit -m "feat: add Drofenik channel model (channel-rth, channel-dp) with tests"
```

---

### Task 3: Implement CSPI metric and optimizer

**Files:**
- Create: `lib/cspi_calc.m`
- Create: `lib/cspi_optimize.m`
- Create: `lib/cmd_cspi.m`
- Create: `lib/cmd_cspi_optimize.m`
- Create: `tests/test_cspi.m`
- Modify: `thermal_cli.m`

- [ ] **Step 1: Create `lib/cspi_calc.m`**

```matlab
function cspi = cspi_calc(rth, vol_cs)
    % cspi_calc - Cooling System Performance Index
    % Drofenik & Kolar, CIPS06 eq. 41
    %   rth: thermal resistance surface-to-ambient [K/W]
    %   vol_cs: cooling system volume [liters] (heatsink + fan)
    %   Returns: CSPI [W/(K*liter)]

    cspi = 1 / (rth * vol_cs);
end
```

- [ ] **Step 2: Create `lib/cspi_optimize.m`**

Implements Drofenik eq. 45/50: closed-form CSPI as function of (lambda_HS, A_CHIP, c, P_FAN_MAX).

```matlab
function result = cspi_optimize(lambda_HS, A_CHIP, c, P_FAN_MAX, varargin)
    % cspi_optimize - find optimal heatsink geometry maximizing CSPI
    % Drofenik & Kolar, CIPS06 eq. 45-50
    %
    %   lambda_HS: heatsink thermal conductivity [W/(m*K)]
    %   A_CHIP: total chip area to be cooled [m2]
    %   c: fan diameter = heatsink fin height [m]
    %   P_FAN_MAX: maximum acceptable fan power [W]
    %   Optional: 't_min', <value> - minimum fin thickness [m] (manufacturing constraint)
    %   Optional: 'k1', <value>, 'k2', <value>, 'k3', <value> - fan scaling constants
    %
    % Returns struct with:
    %   .cspi - optimal CSPI [W/(K*liter)]
    %   .rth  - optimal thermal resistance [K/W]
    %   .vol  - cooling system volume [liters]
    %   .n    - optimal number of fins
    %   .s    - optimal channel width [m]
    %   .t    - optimal fin thickness [m]
    %   .Re   - Reynolds number (must be < 2300 for validity)
    %   .N_fan - required fan speed [rpm]

    % Parse optional arguments
    t_min = 0;
    k1 = 6e-3;    % default from 65-fan survey midpoint
    k2 = 5e-4;
    k3 = 30e-6;
    for i = 1:2:length(varargin)
        switch varargin{i}
            case 't_min', t_min = varargin{i+1};
            case 'k1', k1 = varargin{i+1};
            case 'k2', k2 = varargin{i+1};
            case 'k3', k3 = varargin{i+1};
        end
    end

    % Derived constants (Drofenik eq. 36)
    A1 = 1e-3 * k1 / k2;
    A2 = 5e-4 / sqrt(k2);
    A3 = 6.5 * k2^0.5 / k1;
    A4 = 7.5e-4 / k1;

    % Fan speed from max power (eq. 49)
    N = (1/k3 * P_FAN_MAX)^(1/3) * c^(-5/3);

    % Optimal channel width s (eq. 46)
    s_min = sqrt(A1 * A_CHIP / (N * c^2));
    s_max = (A1 / 5 * A_CHIP / (N * c))^(1/2);

    % Use geometric mean as optimal s
    s = sqrt(s_min * s_max);

    % Optimal fin number (eq. 47)
    n = floor(A1 * A_CHIP / (N * s * c));
    if n < 5
        n = 5;
    end

    % Fin thickness (eq. 19)
    t = c / n - s;
    if t < t_min
        t = t_min;
        n = floor(c / (s + t));
    end
    if t <= 0
        result.cspi = 0;
        result.rth = Inf;
        result.vol = Inf;
        result.n = 0;
        result.s = s;
        result.t = 0;
        result.Re = 0;
        result.N_fan = N;
        result.feasible = false;
        return;
    end

    % Heatsink length L = A_CHIP / c (assuming b = c = D)
    L = A_CHIP / c;

    % Reynolds number check (eq. 48)
    Re = 6.35e4 * k1 * N * c^2 / n;

    % CSPI^-1 from eq. 45
    cspi_inv_fin = c^2 / (2 * lambda_HS * L) * (1 + c^2 / (3 * A_CHIP)) / ...
                   (1 - A1 * A_CHIP / (N * s^2 * c));
    cspi_inv_conv = A1 * (1 + c^2 / (3 * A_CHIP)) * s^2 / ...
                    (1 + A2 * A_CHIP / (s^2 * (k2^(1/3) * P_FAN_MAX^(1/3) * c^(1/3))));
    cspi_inv_dt = A4 * (A_CHIP + 0.5 * c^2) / ...
                  (sqrt(k2) * (k2^(1/3) * P_FAN_MAX^(1/3) * c^(1/3)));

    cspi_inv = cspi_inv_fin + cspi_inv_conv + cspi_inv_dt;

    % Volume
    vol_hs = L * c * c;  % heatsink volume [m3]
    vol_cs = vol_hs * 1000;  % convert to liters

    % Rth
    rth = cspi_inv / vol_cs;

    result.cspi = 1 / cspi_inv;
    result.rth = rth;
    result.vol = vol_cs;
    result.n = n;
    result.s = s;
    result.t = t;
    result.Re = Re;
    result.N_fan = N;
    result.L = L;
    result.feasible = Re < 2300 && t > 0;
end
```

- [ ] **Step 3: Create `lib/cmd_cspi.m`**

```matlab
function result = cmd_cspi(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m cspi --rth <K/W> --vol <liters>\n');
        fprintf('Computes CSPI = 1 / (Rth * Vol_CS).\n');
        result = struct();
        return;
    end

    rth = str2double(parsed.rth);
    vol = str2double(parsed.vol);
    cspi = cspi_calc(rth, vol);

    result.cspi = cspi;
    fprintf('cspi=%.2f\n', cspi);
end
```

- [ ] **Step 4: Create `lib/cmd_cspi_optimize.m`**

```matlab
function result = cmd_cspi_optimize(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m cspi-optimize --lambda <W/mK> --a-chip <m2> --c <m> --p-fan <W> [--t-min <m>]\n');
        fprintf('Finds optimal heatsink geometry maximizing CSPI (Drofenik eq.50).\n');
        result = struct();
        return;
    end

    lambda = str2double(parsed.lambda);
    a_chip = str2double(parsed.a_chip);
    c = str2double(parsed.c);
    p_fan = str2double(parsed.p_fan);

    args = {};
    if isfield(parsed, 't_min')
        args = [args, {'t_min', str2double(parsed.t_min)}];
    end
    if isfield(parsed, 'k1')
        args = [args, {'k1', str2double(parsed.k1)}];
    end
    if isfield(parsed, 'k2')
        args = [args, {'k2', str2double(parsed.k2)}];
    end
    if isfield(parsed, 'k3')
        args = [args, {'k3', str2double(parsed.k3)}];
    end

    r = cspi_optimize(lambda, a_chip, c, p_fan, args{:});

    fprintf('cspi=%.2f\n', r.cspi);
    fprintf('rth=%.6f\n', r.rth);
    fprintf('vol=%.4f\n', r.vol);
    fprintf('n_fins=%d\n', r.n);
    fprintf('s_channel=%.4e\n', r.s);
    fprintf('t_fin=%.4e\n', r.t);
    fprintf('Re=%.1f\n', r.Re);
    fprintf('N_fan=%.0f\n', r.N_fan);
    fprintf('feasible=%d\n', r.feasible);

    result = r;
end
```

- [ ] **Step 5: Create `tests/test_cspi.m`**

```matlab
function results = test_cspi()
    results = {};

    % Test 1: CSPI metric basic
    r.name = 'cspi_calc: basic 1/(0.5*0.2)=10';
    cspi = cspi_calc(0.5, 0.2);
    r.pass = assert_near(cspi, 10, 0.001, r.name);
    r.detail = sprintf('CSPI=%.2f', cspi);
    results{end+1} = r;

    % Test 2: CSPI from Drofenik paper Fig.7a (aluminum, measured Rth=0.26, Vol=0.22)
    r.name = 'cspi_calc: Drofenik Fig.7a aluminum CSPI~17.5';
    cspi = cspi_calc(0.26, 0.22);
    r.pass = assert_near(cspi, 17.5, 1, r.name);
    r.detail = sprintf('CSPI=%.1f (expected ~17.5)', cspi);
    results{end+1} = r;

    % Test 3: CSPI optimizer produces valid geometry
    r.name = 'cspi_optimize: aluminum 210W/mK, 32cm2, c=40mm, 20W fan';
    res = cspi_optimize(210, 32e-4, 0.04, 20);
    r.pass = res.cspi > 10 && res.n > 5 && res.s > 0 && res.t > 0;
    r.detail = sprintf('CSPI=%.1f, n=%d, s=%.2fmm, t=%.2fmm', res.cspi, res.n, res.s*1000, res.t*1000);
    results{end+1} = r;

    % Test 4: Copper gives higher CSPI than aluminum
    r.name = 'cspi_optimize: copper > aluminum CSPI';
    res_al = cspi_optimize(210, 32e-4, 0.04, 20);
    res_cu = cspi_optimize(380, 32e-4, 0.04, 20);
    r.pass = res_cu.cspi > res_al.cspi;
    r.detail = sprintf('CSPI_Al=%.1f, CSPI_Cu=%.1f', res_al.cspi, res_cu.cspi);
    results{end+1} = r;

    % Test 5: Manufacturing constraint reduces CSPI
    r.name = 'cspi_optimize: t_min constraint reduces CSPI';
    res_free = cspi_optimize(210, 32e-4, 0.04, 20);
    res_const = cspi_optimize(210, 32e-4, 0.04, 20, 't_min', 1.5e-3);
    r.pass = res_const.cspi <= res_free.cspi;
    r.detail = sprintf('free=%.1f, constrained=%.1f', res_free.cspi, res_const.cspi);
    results{end+1} = r;

    % Test 6: Reynolds check
    r.name = 'cspi_optimize: Re < 2300 for validity';
    res = cspi_optimize(210, 32e-4, 0.04, 20);
    r.pass = res.Re < 2300;
    r.detail = sprintf('Re=%.0f', res.Re);
    results{end+1} = r;
end
```

- [ ] **Step 6: Add to dispatcher, run tests, commit**

```bash
git add lib/cspi_calc.m lib/cspi_optimize.m lib/cmd_cspi.m lib/cmd_cspi_optimize.m tests/test_cspi.m thermal_cli.m
git commit -m "feat: add CSPI metric and Drofenik optimizer (cspi, cspi-optimize)"
```

---

### Task 4: Implement fan-fit command

**Files:**
- Create: `lib/fan_scaling_fit.m`
- Create: `lib/cmd_fan_fit.m`
- Modify: `thermal_cli.m`

Fits k1, k2, k3 fan scaling constants from fan PQ curve data.

- [ ] **Step 1: Create `lib/fan_scaling_fit.m`**

```matlab
function [k1, k2, k3] = fan_scaling_fit(V_max, dp_max, P_fan, D, N)
    % fan_scaling_fit - fit fan scaling law constants from datasheet values
    % Drofenik eq. 29-31:
    %   V_MAX = k1 * N * D^3
    %   dp_MAX = k2 * N^2 * D^2
    %   P_FAN = k3 * N^3 * D^5
    %
    %   V_max: max flow rate [m3/s]
    %   dp_max: max pressure [Pa]
    %   P_fan: rated power [W]
    %   D: fan diameter [m]
    %   N: fan speed [rpm]

    k1 = V_max / (N * D^3);
    k2 = dp_max / (N^2 * D^2);
    k3 = P_fan / (N^3 * D^5);
end
```

- [ ] **Step 2: Create `lib/cmd_fan_fit.m`**

```matlab
function result = cmd_fan_fit(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m fan-fit --v-max <m3/s> --dp-max <Pa> --p-fan <W> --diameter <m> --speed <rpm>\n');
        fprintf('Fits fan scaling law constants k1, k2, k3 from datasheet values.\n');
        result = struct();
        return;
    end

    V_max = str2double(parsed.v_max);
    dp_max = str2double(parsed.dp_max);
    P_fan = str2double(parsed.p_fan);
    D = str2double(parsed.diameter);
    N = str2double(parsed.speed);

    [k1, k2, k3] = fan_scaling_fit(V_max, dp_max, P_fan, D, N);

    result.k1 = k1;
    result.k2 = k2;
    result.k3 = k3;
    fprintf('k1=%.4e\n', k1);
    fprintf('k2=%.4e\n', k2);
    fprintf('k3=%.4e\n', k3);
    fprintf('\nDrofenik survey ranges:\n');
    fprintf('  k1: [0.5e-3 .. 13.5e-3] (got %.2e)\n', k1);
    fprintf('  k2: [3.9e-4 .. 8.85e-4] (got %.2e)\n', k2);
    fprintf('  k3: [3.0e-6 .. 76.5e-6] (got %.2e)\n', k3);
end
```

- [ ] **Step 3: Add to dispatcher, commit**

```bash
git add lib/fan_scaling_fit.m lib/cmd_fan_fit.m thermal_cli.m
git commit -m "feat: add fan-fit command for fan scaling law constants"
```

---

### Task 5: Final integration test

- [ ] **Step 1: Run full test suite**

```bash
cd /home/tinix/claude_wsl/octave/thermal && octave --no-gui tests/run_tests.m
```

Expected: ~76 tests pass (58 + 6 h_coeff + 6 channel + 6 cspi).

- [ ] **Step 2: Test all new commands**

```bash
octave --no-gui thermal_cli.m h-coeff --mode forced --length 0.05 --velocity 2 --t-ambient 40 --t-surface 80
octave --no-gui thermal_cli.m h-coeff --mode natural --orientation vertical --length 0.05 --t-ambient 40 --t-surface 80
octave --no-gui thermal_cli.m h-coeff --mode radiation --epsilon 0.9 --t-ambient 40 --t-surface 80
octave --no-gui thermal_cli.m channel-rth --width 1e-3 --height 40e-3 --length 80e-3 --flowrate 1e-4
octave --no-gui thermal_cli.m channel-dp --width 1e-3 --height 40e-3 --length 80e-3 --flowrate 1e-4
octave --no-gui thermal_cli.m cspi --rth 0.26 --vol 0.22
octave --no-gui thermal_cli.m cspi-optimize --lambda 210 --a-chip 32e-4 --c 0.04 --p-fan 20
octave --no-gui thermal_cli.m fan-fit --v-max 0.0068 --dp-max 165 --diameter 0.04 --speed 15500 --p-fan 5
```

- [ ] **Step 3: Commit any fixups**

---

## Summary

After Phase 6:
- **6 new core functions:** h_forced_convection, h_natural_convection, h_radiation, channel_rth, channel_pressure_drop, cspi_calc, cspi_optimize, fan_scaling_fit, air_properties
- **6 new CLI commands:** h-coeff, channel-rth, channel-dp, cspi, cspi-optimize, fan-fit
- **~18 new tests** (h_coefficients + channel + cspi)
- **Total: ~76 tests**
- **Total CLI commands: 16** + 3 workflows
