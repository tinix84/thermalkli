% Example 03: CSPI comparison — aluminum vs copper heatsink
% Reproduces Drofenik/Kolar CIPS06 paper results
%
% Run: octave examples/example_03_cspi_comparison.m

addpath('../lib');

fprintf('=== Example 03: CSPI Material Comparison ===\n');
fprintf('Reference: Drofenik & Kolar, CIPS 2006, Fig.5\n\n');

% SanAce 40x40x28mm fan parameters (from fan-fit)
k1 = 6.85e-3; k2 = 4.29e-4; k3 = 1.31e-5;
A_CHIP = 32e-4;  % 32 cm2
P_FAN = 20;       % 20W max fan power

fprintf('Fan: SanAce 40x40x28, k1=%.2e, k2=%.2e, k3=%.2e\n', k1, k2, k3);
fprintf('Chip area: %.0f cm2\n', A_CHIP * 1e4);
fprintf('Max fan power: %.0f W\n\n', P_FAN);

% Compare materials at different fan diameters
materials = struct('name', {'Aluminum', 'Copper', 'Al-Diamond (MMC)'}, ...
                   'lambda', {210, 380, 650});

fan_diameters = [0.02 0.04 0.06 0.08 0.12];

fprintf('%-15s', 'c [mm]');
for m = 1:length(materials)
    fprintf('%15s', materials(m).name);
end
fprintf('\n');
fprintf('%s\n', repmat('-', 1, 15 + 15*length(materials)));

for i = 1:length(fan_diameters)
    c = fan_diameters(i);
    fprintf('%-15.0f', c * 1e3);
    for m = 1:length(materials)
        res = cspi_optimize(materials(m).lambda, A_CHIP, c, P_FAN, ...
            'k1', k1, 'k2', k2, 'k3', k3, 't_min', 0.5e-3);
        if res.feasible
            fprintf('%12.1f', res.cspi);
        else
            fprintf('%12s', 'N/A');
        end
    end
    fprintf('\n');
end

fprintf('\nPaper reference values (Fig.5, c=40mm, P_FAN=20W):\n');
fprintf('  Aluminum (210 W/mK): CSPI ~ 22 (measured prototype: 17.5)\n');
fprintf('  Copper   (380 W/mK): CSPI ~ 26 (measured prototype: 22.2)\n');
fprintf('  Note: our optimizer finds higher theoretical CSPI because it\n');
fprintf('  uses the full Nusselt correlation (not simplified equations)\n');
fprintf('  and explores thinner fin geometries than practical manufacturing.\n');

fprintf('\n--- Verify by computing CSPI from paper measured values ---\n');
fprintf('Paper Fig.7a Al: Rth=0.26 K/W, Vol=0.22L -> CSPI = %.1f\n', cspi_calc(0.26, 0.22));
fprintf('Paper Fig.7b Cu: Rth=0.22 K/W, Vol=0.22L -> CSPI = %.1f\n', cspi_calc(0.22, 0.22));
fprintf('Paper eq.18 Al: Rth=0.56 K/W, Vol=0.195L -> CSPI = %.1f\n', cspi_calc(0.56/2, 0.195));
