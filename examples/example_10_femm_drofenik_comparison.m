% Example 10: FEMM vs Drofenik analytical — direct paper comparison
%
% Reproduces the exact geometry from:
%   Drofenik & Kolar, "Sub-Optimum Design of a Forced Air Cooled Heat Sink
%   for Simple Manufacturing", PCC'07, Fig.1
%
% Paper case: Aluminum heatsink, SanAce 40x40x28 fan
%   b = c = 40mm, d = 10mm, L = 80mm
%   Sub-optimum (1): n=16, s=1.5mm, t=1.0mm
%   Measured Rth = 0.26 K/W (one side), theoretical 0.254 K/W
%
% This script:
% 1. Computes Drofenik analytical Rth (eq.11-14)
% 2. Computes h from Drofenik channel model
% 3. Generates FEMM Lua matching paper Fig.1 exactly
% 4. The Lua script prints Rth comparison after solving
%
% Run: cd examples && octave example_10_femm_drofenik_comparison.m

addpath('../lib');
addpath(genpath('../mfiles'));

fprintf('=== Example 10: FEMM vs Drofenik Paper Direct Comparison ===\n');
fprintf('Reference: Drofenik & Kolar, PCC 2007, Fig.1 & Fig.4\n\n');

% =====================================================================
% Paper parameters (PCC07 sub-optimum design 1 for aluminum)
% =====================================================================
b = 0.040;       % [m] heatsink width (= fan diameter)
c = 0.040;       % [m] fin height (= channel height)
d = 0.010;       % [m] baseplate thickness
L = 0.080;       % [m] heatsink length (airflow direction)
n = 16;          % [-] number of fins
s = 1.5e-3;      % [m] channel width
t = 1.0e-3;      % [m] fin thickness
lambda = 210;    % [W/(m*K)] aluminum
P_V = 20;        % [W] total power (per paper: "fan losses limited to 20W")

fprintf('Geometry (PCC07 sub-optimum 1, aluminum):\n');
fprintf('  b = c = %.0f mm (fan diameter)\n', b*1e3);
fprintf('  d = %.0f mm (baseplate)\n', d*1e3);
fprintf('  L = %.0f mm (length)\n', L*1e3);
fprintf('  n = %d fins\n', n);
fprintf('  s = %.1f mm (channel width)\n', s*1e3);
fprintf('  t = %.1f mm (fin thickness)\n', t*1e3);
fprintf('  k = s/(b/n) = %.2f (fin spacing ratio)\n', s / (b/n));
fprintf('  lambda = %d W/(m*K)\n', lambda);
fprintf('  P_V = %.0f W\n\n', P_V);

% =====================================================================
% Step 1: Compute h from Drofenik channel model
% =====================================================================
fprintf('Step 1: Channel model (Drofenik correlations)\n');

fluid = air_properties(80);  % 80C reference (paper assumption)

geom_ch.width = s;
geom_ch.height = c;
geom_ch.length = L;

% Fan: SanAce 40x40x28, k1=6.85e-3, k2=4.29e-4
k1 = 6.85e-3; k2 = 4.29e-4; k3 = 1.31e-5;
N_fan = (P_V / (k3 * b^5))^(1/3);  % fan speed for max power
V_MAX = k1 * N_fan * b^3;  % max flow rate
V_per_channel = V_MAX / n;

fprintf('  N_fan = %.0f rpm\n', N_fan);
fprintf('  V_MAX = %.4f m3/s\n', V_MAX);
fprintf('  V per channel = %.6f m3/s\n', V_per_channel);

% Use half the max flow (typical operating point)
V_op = 0.5 * V_MAX;
V_ch = V_op / n;

[rth_ch, Re, Nu, h_ch] = channel_rth(geom_ch, V_ch, fluid);
fprintf('  V_operating = %.4f m3/s (50%% of max)\n', V_op);
if Re < 2300, flow_regime = 'laminar'; else, flow_regime = 'turbulent'; end
fprintf('  Re = %.1f (%s)\n', Re, flow_regime);
fprintf('  Nu = %.2f\n', Nu);
fprintf('  h = %.1f W/(m2K)\n\n', h_ch);

% =====================================================================
% Step 2: Drofenik analytical Rth (eq.11-14)
% =====================================================================
fprintf('Step 2: Drofenik analytical Rth (eq.11-14, PCC07)\n');

% eq.13: R_th,d = d / (A_HS/n * lambda)
A_HS_per_n = (b/n) * L;
R_th_d = d / (A_HS_per_n * lambda);

% eq.11: R_th,A/2 = 1 / (h * L * c/2) — convection from half-channel
R_th_A_half = 1 / (h_ch * L * c/2);

% eq.12: R_th,FIN/2 = (c/2) / (t/2 * L * lambda) — conduction through half-fin
R_th_FIN_half = (c/2) / (t/2 * L * lambda);

% eq.14: R_th,S-a^(HS) = 1/n * (R_th,d + 1/2*(R_th,FIN + R_th,A)) + 0.5/(rho*cp*V)
R_th_DT = 0.5 / (fluid.density * fluid.heat_capacity * V_op);
R_th_total = 1/n * (R_th_d + 0.5*(R_th_FIN_half + R_th_A_half)) + R_th_DT;

fprintf('  R_th,d     = %.4f K/W (baseplate conduction)\n', R_th_d);
fprintf('  R_th,A/2   = %.4f K/W (convection half-channel)\n', R_th_A_half);
fprintf('  R_th,FIN/2 = %.4f K/W (fin conduction)\n', R_th_FIN_half);
fprintf('  R_th,DT    = %.4f K/W (air temperature rise)\n', R_th_DT);
fprintf('  ---\n');
fprintf('  R_th,total (eq.14) = %.4f K/W\n', R_th_total);
fprintf('  Paper measured:      0.26 K/W (one side)\n');
fprintf('  Paper theoretical:   0.254 K/W\n\n');

% =====================================================================
% Step 3: Generate FEMM Lua
% =====================================================================
fprintf('Step 3: Generate FEMM Lua script\n');

params.b = b;
params.c = c;
params.d = d;
params.L = L;
params.n = n;
params.s = s;
params.t = t;
params.lambda = lambda;
params.h = h_ch;
params.T_air = 80 + 273.15;  % [K] match paper's 80C reference (Kelvin convention)
params.P_V = P_V;

lua_str = femm_drofenik_heatsink(params);

lua_path = 'femm_drofenik_heatsink.lua';
fid = fopen(lua_path, 'w');
fprintf(fid, '%s', lua_str);
fclose(fid);
fprintf('  Lua saved to: %s (%d lines)\n', lua_path, length(strsplit(lua_str, '\n')));

% =====================================================================
% Step 4: Also compute with our CSPI
% =====================================================================
fprintf('\nStep 4: CSPI metric\n');
Vol_CS = b * c * L * 1000;  % heatsink volume in liters (no fan volume)
CSPI = cspi_calc(R_th_total, Vol_CS);
fprintf('  Vol_CS = %.3f liters (heatsink only)\n', Vol_CS);
fprintf('  CSPI = %.1f W/(K*liter)\n', CSPI);
fprintf('  Paper measured CSPI: %.1f (Rth=0.26, Vol=0.22L incl fan)\n', cspi_calc(0.26, 0.22));

% =====================================================================
% Summary
% =====================================================================
fprintf('\n=== Comparison Table ===\n');
fprintf('%-25s %12s %12s\n', 'Quantity', 'Our model', 'Paper');
fprintf('%s\n', repmat('-', 1, 50));
fprintf('%-25s %12.4f %12.4f\n', 'Rth one side [K/W]', R_th_total, 0.254);
fprintf('%-25s %12.4f %12.4f\n', 'Rth both sides [K/W]', R_th_total/2, 0.254/2);
fprintf('%-25s %12.0f %12.0f\n', 'n fins', n, 16);
fprintf('%-25s %12.1f %12.1f\n', 's [mm]', s*1e3, 1.5);
fprintf('%-25s %12.1f %12.1f\n', 't [mm]', t*1e3, 1.0);
fprintf('%-25s %12.1f %12s\n', 'h [W/(m2K)]', h_ch, '(not given)');

fprintf('\n--- FEMM Verification ---\n');
fprintf('1. Open %s in FEMM\n', lua_path);
fprintf('2. Script solves and prints Rth comparison directly\n');
fprintf('3. FEMM Rth should match analytical within ~5%%\n');
fprintf('4. Temperature contour should show:\n');
fprintf('   - Hot spot at baseplate top (chip surface)\n');
fprintf('   - Gradient through baseplate (d=%.0fmm)\n', d*1e3);
fprintf('   - Fin tips close to air temperature (%.0fC)\n', params.T_air - 273.15);
fprintf('   - Center fins hotter than edge fins\n');
