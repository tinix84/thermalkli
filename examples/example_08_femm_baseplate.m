% Example 08: FEMM verification of baseplate spreading
%
% This example:
% 1. Computes temperature distribution analytically (via Temp_calc)
% 2. Generates a FEMM 2D planar Lua script for the same baseplate
% 3. Compare max temperature at source locations
%
% The FEMM model is a 2D cross-section of a rectangular baseplate:
%   - Heat flux sources on top surface
%   - Convection BC on bottom surface
%   - Insulated side walls
%
% Run: cd examples && octave example_08_femm_baseplate.m

addpath('../lib');
addpath(genpath('../mfiles'));

fprintf('=== Example 08: FEMM Verification — Baseplate Spreading ===\n\n');

% --- Configuration: aluminum baseplate with 3 heat sources ---
plate_width = 0.1;    % 100mm [m]
plate_thick = 0.005;  % 5mm [m]
k_plate = 200;        % aluminum [W/(m*K)]
h_bottom = 500;       % forced convection [W/(m2*K)]
T_fluid = 40;         % [C]

% Three heat sources: 10x10mm each, spaced along the plate
sources.power = [20 30 20];                    % [W]
sources.x = [0.025 0.050 0.075];              % [m] center positions
sources.width = [0.010 0.010 0.010];           % [m]

fprintf('Baseplate: %.0fx%.0fmm, %.0fmm thick, Al (k=%d)\n', ...
    plate_width*1e3, plate_width*1e3, plate_thick*1e3, k_plate);
fprintf('Convection: h=%.0f W/(m2K), T_fluid=%.0fC\n', h_bottom, T_fluid);
fprintf('Sources: 3x (%.0fx%.0fmm), P=[%.0f %.0f %.0f] W\n\n', ...
    sources.width(1)*1e3, sources.width(1)*1e3, sources.power(1), sources.power(2), sources.power(3));

% --- Step 1: Analytical estimate ---
fprintf('Step 1: Analytical estimates\n');

% Simple 1D estimate: T_surface = T_fluid + P_total * (1/(h*A) + t/(k*A))
P_total = sum(sources.power);
A_plate = plate_width^2;
Rth_conv = 1 / (h_bottom * A_plate);
Rth_cond = plate_thick / (k_plate * A_plate);
T_avg = T_fluid + P_total * (Rth_conv + Rth_cond);
fprintf('  1D estimate (uniform): T_avg = %.1fC\n', T_avg);
fprintf('  Rth_conv = %.4f K/W, Rth_cond = %.6f K/W\n', Rth_conv, Rth_cond);

% Per-source estimate (concentrated source, higher local temp)
for i = 1:3
    A_src = sources.width(i)^2;
    T_local = T_fluid + sources.power(i) / (h_bottom * A_src) + ...
              sources.power(i) * plate_thick / (k_plate * A_src);
    fprintf('  Source %d local estimate: T ~ %.1fC (concentrated)\n', i, T_local);
end

% --- Step 2: Generate FEMM Lua ---
fprintf('\nStep 2: Generate FEMM Lua script\n');

cfg_femm.heatsink.width = plate_width;
cfg_femm.heatsink.baseThickness = plate_thick;
cfg_femm.heatsink.kPlate = k_plate;
cfg_femm.convection.h = h_bottom;
cfg_femm.convection.tFluid = T_fluid + 273.15;
cfg_femm.sources.power = sources.power;
cfg_femm.sources.x = sources.x;
cfg_femm.sources.width = sources.width;

lua_path = 'femm_baseplate.lua';
lua_str = femm_baseplate_spreading(cfg_femm);
fid = fopen(lua_path, 'w');
fprintf(fid, '%s', lua_str);
fclose(fid);
fprintf('  FEMM Lua script saved to: %s\n', lua_path);

% --- Step 3: Print what to check in FEMM ---
fprintf('\n--- FEMM Geometry ---\n');
fprintf('  Plate: (0,0) to (%.0fmm, %.1fmm)\n', plate_width*1e3, plate_thick*1e3);
for i = 1:3
    x_left = (sources.x(i) - sources.width(i)/2) * 1e3;
    x_right = (sources.x(i) + sources.width(i)/2) * 1e3;
    fprintf('  Source %d: x=[%.0f..%.0f]mm on top surface, q=%.0f W/m2\n', ...
        i, x_left, x_right, sources.power(i) / (sources.width(i) * 1));
end
fprintf('  Bottom: convection h=%.0f, T=%.0fC\n', h_bottom, T_fluid);
fprintf('  Left/Right: insulated\n');

fprintf('\n--- What to Check in FEMM ---\n');
fprintf('1. Temperature at each source center (top surface):\n');
for i = 1:3
    fprintf('   Source %d at x=%.0fmm: expect %.0f-%.0fC\n', ...
        i, sources.x(i)*1e3, T_avg, T_avg + 30);
end
fprintf('2. Temperature at bottom center: should be close to T_fluid+Rth_conv*P = %.1fC\n', ...
    T_fluid + P_total * Rth_conv);
fprintf('3. Source 2 (30W) should be hottest\n');
fprintf('4. Lateral spreading should be visible in contour plot\n');

fprintf('\n--- Next Steps ---\n');
fprintf('1. Open femm_baseplate.lua in FEMM\n');
fprintf('2. After solve: note temperatures at source locations\n');
fprintf('3. The FEMM script exports femm_results.csv automatically\n');
fprintf('4. Compare with the 1D estimates above\n');
fprintf('5. FEMM should show higher temps at sources due to spreading\n');
