% Example 01: Basic thermal resistance calculations
% Verify these results by hand calculation
%
% Run: octave examples/example_01_basic_rth.m

addpath('../lib');
addpath(genpath('../mfiles'));

fprintf('=== Example 01: Basic Thermal Resistance ===\n\n');

% 1. Conduction through a copper plate
% R = L / (k * A)
% 2mm copper (k=400 W/mK), 10x10mm area
L = 0.002; k = 400; A = 0.01 * 0.01;
R = L / (k * A);
fprintf('1. Copper plate 2mm, 10x10mm: R = %.4f K/W (hand: 0.002/(400*0.0001) = 0.05)\n', R);

% 2. Convection from a surface
% R = 1 / (h * A)
% h=50 W/(m2K), 10x10mm
h = 50; A = 0.01 * 0.01;
R_conv = 1 / (h * A);
fprintf('2. Convection h=50, 10x10mm: R = %.1f K/W (hand: 1/(50*0.0001) = 200)\n', R_conv);

% 3. Series resistance: copper plate + convection
R_total = R + R_conv;
fprintf('3. Series (plate+conv): R = %.4f K/W (hand: 0.05 + 200 = 200.05)\n', R_total);

% 4. Using ThermalLayer with spreading
fprintf('\n--- ThermalLayer with spreading ---\n');
layer = ThermalLayer(0.003, 200);  % 3mm aluminum
aIn = 1e-4;   % 10x10mm source
aOut = 9e-4;  % 30x30mm sink
hEff = 1000;  % W/(m2K)
[rTh, rThSpread, rThThrough] = layer.thermalLayerResistance(aIn, aOut, hEff);
fprintf('4. Al 3mm, 10x10mm->30x30mm, h=1000:\n');
fprintf('   R_total = %.4f K/W\n', rTh);
fprintf('   R_spread = %.4f K/W (spreading adds %.0f%%)\n', rThSpread, rThSpread/rTh*100);
fprintf('   R_through = %.4f K/W\n', rThThrough);

% 5. Fin efficiency
fprintf('\n--- Fin Efficiency ---\n');
% Aluminum fin: L=25mm, t=1mm, h=50 W/(m2K), k=200 W/(m*K)
L_fin = 0.025; t = 0.001; h_fin = 50; k_fin = 200;
W = 1;  % per unit width
A_fin = 2 * L_fin * W;
Ac = t * W;
eta = finEfficieny(L_fin, h_fin, A_fin, k_fin, Ac);
mL = sqrt(h_fin * A_fin / (k_fin * Ac * L_fin)) * L_fin;
fprintf('5. Al fin 25mm tall, 1mm thick, h=50:\n');
fprintf('   mL = %.4f\n', mL);
fprintf('   eta = %.4f (tanh(%.4f)/%.4f = %.4f)\n', eta, mL, mL, tanh(mL)/mL);

fprintf('\n=== Verify all values match hand calculations ===\n');
