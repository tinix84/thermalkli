% Example 09: FEMM verification of forced-air heatsink with fan
%
% Full pipeline:
% 1. Define heatsink geometry + fan
% 2. Run hydraulic operating point (idraulico) to get flow rate
% 3. Run fin thermal resistance (Rth_fin) to get h on channel walls
% 4. Generate FEMM Lua with the computed h as convection BC
% 5. Compare FEMM temperature distribution with analytical
%
% The FEMM model shows a full cross-section with multiple fins,
% heat flux on the baseplate, and forced-air convection on channel walls.
%
% Run: cd examples && octave example_09_femm_forced_air_heatsink.m

addpath('../lib');
addpath(genpath('../mfiles'));

fprintf('=== Example 09: Forced-Air Heatsink + Fan -> FEMM ===\n\n');

% =====================================================================
% Step 1: Define heatsink + fan configuration
% =====================================================================
fprintf('Step 1: Configuration\n');

hs_profile = 'I117';
hs_material = 'all_aluminum';
fan_model_name = 'EBMW2E200_axial_AC_50Hz';
n_fans = 1;
vent_type = 'push';

a_mm = 200;    % heatsink width [mm] (perp to fins)
b_mm = 200;    % heatsink length [mm] (parallel to fins / airflow direction)
Tin_C = 40;    % inlet air temperature [C]

% Component: 30x30mm source, 50W
src_width = 30;  % [mm]
P_loss = 50;     % [W]

% Get geometry from database
[tb_mm, Hf_mm, tf_mm, bch_mm] = HS_Type(hs_profile);
[Kth_plate, Kth_fin, ~, ~, ~, ~] = HS_Tech(hs_material);
Nf = round(a_mm / (bch_mm + tf_mm));

fprintf('  Heatsink: %s, %dx%d mm, %d fins\n', hs_profile, a_mm, b_mm, Nf);
fprintf('  Geometry: tb=%.1f, Hf=%.1f, tf=%.1f, bch=%.1f mm\n', tb_mm, Hf_mm, tf_mm, bch_mm);
fprintf('  Fan: %s x%d (%s)\n', fan_model_name, n_fans, vent_type);
fprintf('  Source: %dx%d mm, %.0f W\n', src_width, src_width, P_loss);

% =====================================================================
% Step 2: Hydraulic operating point
% =====================================================================
fprintf('\nStep 2: Hydraulic operating point\n');

[Hv1, Qv1, Qvmin1, Qvmax1, ~, ~] = Fan_Model(fan_model_name);
Qv = n_fans * Qv1;
Hv = Hv1;

Tair_C = Tin_C + 0.5 * P_loss / (Cp_air(Tin_C) * rho_air(Tin_C) * mean(Qv));
[Re_hydr, Hv_f, Qv_f] = idraulico(b_mm, a_mm, Nf, tf_mm, bch_mm, Hf_mm, Tair_C, vent_type, Qv, Hv);
Tair_C = Tin_C + 0.5 * P_loss / (Cp_air(Tin_C) * rho_air(Tin_C) * Qv_f);

fprintf('  Flow rate: %.6f m3/s\n', Qv_f);
fprintf('  Pressure:  %.1f Pa\n', Hv_f);
fprintf('  Re_hydr:   %.1f\n', Re_hydr);
fprintf('  T_air_mean: %.1f C\n', Tair_C);

% =====================================================================
% Step 3: Fin thermal resistance -> get h
% =====================================================================
fprintf('\nStep 3: Fin thermal resistance\n');

[Re_therm, Vch1, Vch2, Rth_fin_val, hf_eq] = Rth_fin(Qv_f, a_mm, b_mm, a_mm, tf_mm, bch_mm, Hf_mm, Tair_C, vent_type, Kth_fin, Nf);

fprintf('  Rth_fin:  %.4f K/W\n', Rth_fin_val);
fprintf('  h_eq:     %.1f W/(m2K)\n', hf_eq);
fprintf('  V_air:    %.2f m/s\n', Vch2);
fprintf('  Re_therm: %.1f\n', Re_therm);

% Analytical temperature estimate
dT_air = P_loss / (Cp_air(Tair_C) * rho_air(Tair_C) * Qv_f);
T_base_est = Tin_C + dT_air / 2 + P_loss * Rth_fin_val;
fprintf('\n  Analytical estimate:\n');
fprintf('    dT_air = %.1f C\n', dT_air);
fprintf('    T_base ~ %.1f C (baseplate average)\n', T_base_est);

% =====================================================================
% Step 4: Generate FEMM Lua
% =====================================================================
fprintf('\nStep 4: Generate FEMM Lua script\n');

cfg_femm.baseThickness = tb_mm * 1e-3;
cfg_femm.finHeight = Hf_mm * 1e-3;
cfg_femm.finThickness = tf_mm * 1e-3;
cfg_femm.channelWidth = bch_mm * 1e-3;
cfg_femm.k = Kth_fin;
cfg_femm.tFluid = Tair_C + 273.15;
cfg_femm.heatSource.width = src_width * 1e-3;
cfg_femm.heatSource.flux = P_loss / (src_width * 1e-3 * b_mm * 1e-3);

% Show 15 fins centered on source (odd for symmetry)
n_show = 15;

lua_str = femm_forced_air_heatsink(cfg_femm, hf_eq, n_show);

lua_path = 'femm_forced_air_heatsink.lua';
fid = fopen(lua_path, 'w');
fprintf(fid, '%s', lua_str);
fclose(fid);
fprintf('  Lua script saved to: %s\n', lua_path);
fprintf('  Model: %d fins shown, h=%.1f W/(m2K) on channel walls\n', n_show, hf_eq);

% =====================================================================
% Summary
% =====================================================================
fprintf('\n--- Summary ---\n');
fprintf('  Fan operating point: %.4f m3/s at %.0f Pa\n', Qv_f, Hv_f);
fprintf('  h_channel (from Rth_fin): %.1f W/(m2K)\n', hf_eq);
fprintf('  Analytical Rth: %.4f K/W\n', Rth_fin_val);
fprintf('  Analytical T_base: ~%.1f C\n', T_base_est);

fprintf('\n--- FEMM Verification Steps ---\n');
fprintf('1. Open %s in FEMM\n', lua_path);
fprintf('2. Script auto-solves and creates femm_results.csv\n');
fprintf('3. Check temperatures:\n');
fprintf('   - Base center (under source): should be ~%.0f C\n', T_base_est + 5);
fprintf('   - Center fin tip: should be between %.0f C and %.0f C\n', Tair_C, T_base_est);
fprintf('   - Edge fin tip: should be close to T_air = %.0f C\n', Tair_C);
fprintf('4. Temperature gradient from center to edges should be visible\n');
fprintf('5. Fin tips should be cooler than fin roots (fin efficiency effect)\n');
