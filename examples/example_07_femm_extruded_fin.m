% Example 07: FEMM verification of extruded fin heatsink
%
% This example:
% 1. Computes analytical Rth for one fin channel using the Drofenik model
% 2. Generates a FEMM 2D planar Lua script for the same half-channel
% 3. Compare base temperature, fin tip temperature
%
% The FEMM model is a 2D cross-section of half a fin + half a channel:
%   - Left boundary: symmetry (fin center)
%   - Right boundary: symmetry (channel center)
%   - Bottom: heat flux from component
%   - Channel walls: convection BC
%
% Run: cd examples && octave example_07_femm_extruded_fin.m

addpath('../lib');
addpath(genpath('../mfiles'));

fprintf('=== Example 07: FEMM Verification — Extruded Fin ===\n\n');

% --- Configuration: aluminum heatsink, 1 channel ---
cfg.heatsink.thickWall = 1e-3;          % 1mm fin thickness
cfg.heatsink.widthChannel = 2e-3;       % 2mm channel width
cfg.heatsink.thickHeatsink = 5e-3;      % 5mm base plate
cfg.heatsink.heightTotal = 25e-3;       % 25mm total (base + fin)
cfg.heatsink.kSink = 200;               % aluminum [W/(m*K)]

cfg.fluid.tInlet = 273.15 + 40;         % 40C fluid
cfg.heating.pLoss = 50;                 % 50W total
cfg.heating.widthContact = 20e-3;       % 20mm contact width
cfg.heating.lengthContact = 20e-3;      % 20mm contact length

% Estimated channel h from Drofenik model at ~2 m/s air velocity
cfg.h_channel = 80;                     % W/(m2*K) — typical for 2mm channel

% Derived geometry
tf = cfg.heatsink.thickWall;
wch = cfg.heatsink.widthChannel;
tb = cfg.heatsink.thickHeatsink;
Hf = cfg.heatsink.heightTotal - tb;     % 20mm fin height
k = cfg.heatsink.kSink;

fprintf('Geometry:\n');
fprintf('  Fin thickness:    %.1f mm\n', tf * 1e3);
fprintf('  Channel width:    %.1f mm\n', wch * 1e3);
fprintf('  Base thickness:   %.1f mm\n', tb * 1e3);
fprintf('  Fin height:       %.1f mm\n', Hf * 1e3);
fprintf('  Material:         Aluminum (k=%d W/mK)\n', k);
fprintf('  Channel h:        %.0f W/(m2K)\n', cfg.h_channel);

% --- Step 1: Analytical estimates ---
fprintf('\nStep 1: Analytical estimates\n');

% Heat flux
q_flux = cfg.heating.pLoss / (cfg.heating.widthContact * cfg.heating.lengthContact);
fprintf('  Heat flux: %.0f W/m2\n', q_flux);

% Conductive Rth through base
Rth_base = tb / (k * cfg.heating.widthContact * cfg.heating.lengthContact);
fprintf('  Rth_base (conduction): %.4f K/W\n', Rth_base);

% Fin efficiency
m = sqrt(2 * cfg.h_channel / (k * tf));
eta_fin = tanh(m * Hf) / (m * Hf);
fprintf('  Fin efficiency: %.3f (mL=%.3f)\n', eta_fin, m * Hf);

% Convective Rth (simplified, per unit depth)
A_fin = 2 * Hf * cfg.heating.lengthContact;  % both sides of fin
A_base_exposed = wch * cfg.heating.lengthContact;
h_eff_area = cfg.h_channel * (eta_fin * A_fin + A_base_exposed);
Rth_conv = 1 / h_eff_area;
fprintf('  Rth_conv (1 channel): %.4f K/W\n', Rth_conv);

% Estimate base temperature
dT_base = cfg.heating.pLoss * Rth_base;
dT_conv = cfg.heating.pLoss * Rth_conv;
T_base = (cfg.fluid.tInlet - 273.15) + dT_conv + dT_base;
fprintf('  Estimated T_base: %.1f C (above fluid by %.1f C)\n', T_base, T_base - 40);

% --- Step 2: Generate FEMM Lua ---
lua_path = 'femm_extruded_fin.lua';
lua_str = femm_extruded_fin(cfg);
fid = fopen(lua_path, 'w');
fprintf(fid, '%s', lua_str);
fclose(fid);
fprintf('\n  FEMM Lua script saved to: %s\n', lua_path);

% --- Step 3: Print FEMM geometry for verification ---
half_tf = tf / 2;
half_wch = wch / 2;
W = half_tf + half_wch;
fprintf('\n--- FEMM Geometry (half-channel cross section) ---\n');
fprintf('  Model width:  %.2f mm (half_fin=%.2f + half_channel=%.2f)\n', W*1e3, half_tf*1e3, half_wch*1e3);
fprintf('  Base:         (0,0) to (%.2f, %.2f) mm\n', W*1e3, tb*1e3);
fprintf('  Fin:          (0,%.2f) to (%.2f, %.2f) mm\n', tb*1e3, half_tf*1e3, (tb+Hf)*1e3);
fprintf('  Heat flux BC: bottom edge, q=%.0f W/m2\n', q_flux);
fprintf('  Convection:   fin right wall + channel top + fin top, h=%.0f\n', cfg.h_channel);
fprintf('  Symmetry:     left edge + right edge (insulated)\n');

fprintf('\n--- Next Steps ---\n');
fprintf('1. Open femm_extruded_fin.lua in FEMM\n');
fprintf('2. After solve: check temperature at (0,0) = base bottom center\n');
fprintf('3. Check temperature at (0,%.1f mm) = fin tip\n', (tb+Hf)*1e3);
fprintf('4. Base temp should be ~%.0f C, fin tip should be cooler\n', T_base);
fprintf('5. Compare FEMM contour plot with analytical fin efficiency = %.3f\n', eta_fin);
