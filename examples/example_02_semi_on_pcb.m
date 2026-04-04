% Example 02: Semiconductor on PCB thermal model
% A QFN package (5x5mm exposed pad) on a 4-layer PCB with thermal vias
%
% Run: octave examples/example_02_semi_on_pcb.m

addpath('../lib');
addpath(genpath('../mfiles'));

fprintf('=== Example 02: QFN on 4-Layer PCB ===\n\n');

% QFN-48 package, 5x5mm exposed pad, 2W power
fprintf('Package: QFN-48, 5x5mm exposed pad\n');
fprintf('Power: 2W\n');
fprintf('PCB: 4-layer, 1.6mm total, FR4+Cu\n');
fprintf('Cooling: natural convection h=10 W/(m2K) on bottom\n\n');

% Build input
input = ThermalModelSemiInput;
input.includeBottom = true;
input.rThJCBottom = [5];          % QFN Rth_jc ~ 5 K/W typical
input.areaContact = 25e-6;        % 5x5mm = 25mm2
input.thInsContactPadPcb = 0;     % soldered

% 4-layer PCB: Cu(35um)/FR4(0.36mm)/Cu(35um)/FR4(0.71mm)/Cu(35um)/FR4(0.36mm)/Cu(35um)
input.pcbLayerStack = [
    [35e-6, 400];     % top Cu
    [0.36e-3, 0.3];   % FR4
    [35e-6, 400];      % inner Cu
    [0.71e-3, 0.3];   % FR4 core
    [35e-6, 400];      % inner Cu
    [0.36e-3, 0.3];   % FR4
    [35e-6, 400]       % bottom Cu
];

% Thermal vias: 0.3mm drill, 25um plating, 1mm pitch
input.areaSingleVia = pi * ((0.15e-3)^2 - (0.125e-3)^2);
input.kVia = 400;
input.pcbNumVia = 0;
input.pcbEstimateNumVia = true;
input.pcbViaSpacing = 1e-3;

input.thInsContactPcbSink = 0;
input.sinkLayerStack = [];
input.areaDissBottom = 400e-6;    % 20x20mm dissipation area
input.hFluidBottom = 10;          % natural convection
input.tempFluidBottom = 25 + 273.15;

input.includeTop = false;
input.rThJCTop = 50;
input.areaCaseTop = 25e-6;
input.areaDissTop = 400e-6;
input.hFluidTop = 10;
input.tempFluidTop = 25 + 273.15;

input.pLossJunction = [2];
input.tempJunctionMax = 125 + 273.15;

% Run model
model = ThermalModelSemi(input);
model.calcRthFluidBot();
model.calcTJunction();
model.calcPLossMax();

output = model.output;

fprintf('Results:\n');
fprintf('  Rth junction-to-fluid = %.2f K/W\n', output.rThCaseFluidBot + input.rThJCBottom);
fprintf('  Rth case-to-fluid     = %.2f K/W\n', output.rThCaseFluidBot);
fprintf('  T_junction             = %.1f C\n', output.tJunction - 273.15);
fprintf('  P_loss_max             = %.2f W (at Tj_max=125C)\n', output.pLossMax);
fprintf('  PCB vias (estimated)   = %d\n', output.pcbNumVia);

fprintf('\nVerify: T_j = T_fluid + P * Rth_total\n');
Rth_total = output.rThCaseFluidBot + input.rThJCBottom;
T_j_check = (25 + 273.15) + 2 * Rth_total;
fprintf('  Check: %.1f + 2 * %.2f = %.1f C (model: %.1f C)\n', ...
    25, Rth_total, T_j_check - 273.15, output.tJunction - 273.15);
