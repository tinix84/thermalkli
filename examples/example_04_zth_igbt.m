% Example 04: Transient thermal impedance for IGBT module
% Typical 4-layer Foster network from IGBT datasheet
%
% Run: octave examples/example_04_zth_igbt.m

addpath('../lib');

fprintf('=== Example 04: IGBT Transient Thermal Impedance ===\n\n');

% Typical IGBT Foster network parameters (e.g., Infineon FF600R12ME4)
% These are representative values, not from a specific datasheet
R   = [0.008  0.025  0.060  0.120];  % K/W
tau = [0.001  0.010  0.100  1.000];  % seconds

fprintf('Foster network: 4 RC elements\n');
fprintf('  R   = ['); fprintf('%.3f ', R); fprintf('] K/W\n');
fprintf('  tau = ['); fprintf('%.3f ', tau); fprintf('] s\n');
fprintf('  Rth_total = %.3f K/W\n\n', sum(R));

% Compute Zth curve
[Zth, t] = zth_foster(R, tau, 10, 200);

% Print key time points
fprintf('Zth at key times:\n');
targets = [0.001 0.01 0.1 1 10];
for i = 1:length(targets)
    [~, idx] = min(abs(t - targets(i)));
    pct = Zth(idx) / sum(R) * 100;
    fprintf('  t = %8.3f s -> Zth = %.4f K/W (%5.1f%% of Rth)\n', targets(i), Zth(idx), pct);
end

% Pulsed Zth at 50% duty cycle, 10Hz
fprintf('\n--- Pulsed Zth (D=0.5, f=10Hz) ---\n');
D = 0.5; T_period = 0.1;
Zth_pulse = zth_pulsed(R, tau, t, D, T_period);
fprintf('Steady-state pulsed Zth: %.4f K/W\n', Zth_pulse(end));
fprintf('Ratio to DC Zth: %.2f (should be ~D=%.1f for long pulses)\n', ...
    Zth_pulse(end) / Zth(end), D);

% Junction temperature rise for 100W pulse
P = 100;
fprintf('\nWith P_pulse = %dW:\n', P);
fprintf('  dT_junction (DC)    = %.1f C\n', sum(R) * P);
fprintf('  dT_junction (50%%)   = %.1f C\n', Zth_pulse(end) * P);
fprintf('  dT_junction (1ms)   = %.1f C\n', Zth(find(t >= 0.001, 1)) * P);

fprintf('\nVerify: Zth(t->inf) should equal Rth_total = %.3f K/W\n', sum(R));
fprintf('        Zth(10s)                          = %.3f K/W  OK=%d\n', ...
    Zth(end), abs(Zth(end) - sum(R)) < 0.001);
