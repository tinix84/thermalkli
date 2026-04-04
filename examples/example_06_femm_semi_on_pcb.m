% Example 06: FEMM verification of semiconductor-on-PCB model
%
% This example:
% 1. Runs the analytical semi-on-pcb model
% 2. Generates a FEMM Lua script for the same geometry
% 3. Saves analytical results to CSV
%
% After running this script:
% - Open FEMM (Windows)
% - File -> Open Lua Script -> select femm_semi_on_pcb.lua
% - The script auto-runs: builds geometry, solves, exports femm_results.csv
% - Then run: octave thermal_cli.m compare-femm --analytical analytical_result.csv --femm femm_results.csv
%
% Run: cd examples && octave example_06_femm_semi_on_pcb.m

addpath('../lib');
addpath(genpath('../mfiles'));

fprintf('=== Example 06: FEMM Verification — Semi-on-PCB ===\n\n');

% --- Configuration: simple 2-layer PCB with heatsink ---
% This is a simplified case that FEMM can solve accurately:
% - Axisymmetric model (circular equivalent areas)
% - 2 PCB layers: 70um Cu + 1.5mm FR4
% - 3mm aluminum heatsink below
% - Heat flux on top (chip), convection on bottom (forced air)

cfg.includeBottom = true;
cfg.rThJCBottom = [0];            % no junction-to-case (direct contact)
cfg.areaContact = 100e-6;         % 10x10mm chip -> circular r=5.64mm
cfg.thInsContactPadPcb = 0;
cfg.pcbLayerStack = [
    [70e-6, 400];                 % 70um copper
    [1.5e-3, 0.3]                 % 1.5mm FR4
];
cfg.areaSingleVia = 0;
cfg.kVia = 400;
cfg.pcbNumVia = 0;
cfg.pcbEstimateNumVia = false;
cfg.pcbViaSpacing = 0;
cfg.thInsContactPcbSink = 0;
cfg.sinkLayerStack = [
    [3e-3, 200]                   % 3mm aluminum heatsink
];
cfg.areaDissBottom = 900e-6;      % 30x30mm dissipation -> circular r=16.93mm
cfg.hFluidBottom = 500;           % forced air convection
cfg.tempFluidBottom = 25 + 273.15; % 25C ambient

cfg.includeTop = false;
cfg.rThJCTop = 0;
cfg.areaCaseTop = 100e-6;
cfg.areaDissTop = 900e-6;
cfg.hFluidTop = 10;
cfg.tempFluidTop = 25 + 273.15;

cfg.pLossJunction = [5];         % 5W dissipation
cfg.tempJunctionMax = 125 + 273.15;

% --- Step 1: Analytical solution ---
fprintf('Step 1: Analytical model\n');
input = ThermalModelSemiInput;
fields = fieldnames(cfg);
for i = 1:length(fields)
    input.(fields{i}) = cfg.(fields{i});
end

model = ThermalModelSemi(input);
model.calcRthFluidBot();
model.calcTJunction();

Rth_analytical = model.output.rThCaseFluidBot;
Tj_analytical = model.output.tJunction;

fprintf('  Rth (case-to-fluid) = %.4f K/W\n', Rth_analytical);
fprintf('  T_junction = %.2f K (%.2f C)\n', Tj_analytical, Tj_analytical - 273.15);
fprintf('  T_ambient  = %.2f C\n', 25);
fprintf('  dT = %.2f C\n', Tj_analytical - cfg.tempFluidBottom);

% --- Step 2: Save analytical CSV ---
csv_path = 'analytical_result.csv';
fid = fopen(csv_path, 'w');
fprintf(fid, 'point,value,unit\n');
fprintf(fid, 'junction_temperature_1,%.6f,K\n', Tj_analytical);
fprintf(fid, 'rth_case_fluid_bot,%.6f,K/W\n', Rth_analytical);
fclose(fid);
fprintf('\n  Analytical CSV saved to: %s\n', csv_path);

% --- Step 3: Generate FEMM Lua script ---
lua_path = 'femm_semi_on_pcb.lua';
lua_str = femm_semi_on_pcb(cfg);
fid = fopen(lua_path, 'w');
fprintf(fid, '%s', lua_str);
fclose(fid);
fprintf('  FEMM Lua script saved to: %s\n', lua_path);

% --- Step 4: Print geometry for visual verification ---
rc = sqrt(cfg.areaContact / pi);
b = sqrt(cfg.areaDissBottom / pi);
fprintf('\n--- Geometry Summary (for FEMM visual check) ---\n');
fprintf('  Source radius (rc):  %.4f mm\n', rc * 1e3);
fprintf('  Outer radius (b):   %.4f mm\n', b * 1e3);
fprintf('  PCB layer 1: Cu  %.0f um (k=400)\n', cfg.pcbLayerStack(1,1)*1e6);
fprintf('  PCB layer 2: FR4 %.1f mm (k=0.3)\n', cfg.pcbLayerStack(2,1)*1e3);
fprintf('  Heatsink:    Al  %.1f mm (k=200)\n', cfg.sinkLayerStack(1,1)*1e3);
fprintf('  Heat flux:   q = P/A = %.0f W/m2\n', cfg.pLossJunction / cfg.areaContact);
fprintf('  Convection:  h = %.0f W/(m2K), T = %.0f C\n', cfg.hFluidBottom, cfg.tempFluidBottom - 273.15);

fprintf('\n--- Next Steps ---\n');
fprintf('1. Copy femm_semi_on_pcb.lua to your Windows FEMM installation\n');
fprintf('2. In FEMM: File -> Open Lua Script -> femm_semi_on_pcb.lua\n');
fprintf('3. Script will auto-solve and create femm_results.csv\n');
fprintf('4. Copy femm_results.csv back here\n');
fprintf('5. Run: octave ../thermal_cli.m compare-femm --analytical analytical_result.csv --femm femm_results.csv\n');
fprintf('6. Expected deviation: < 5%% for this simple geometry\n');
