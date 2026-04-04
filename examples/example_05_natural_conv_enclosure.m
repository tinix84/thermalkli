% Example 05: Natural convection cooling of a sealed electronics enclosure
% Estimate surface temperature of a box dissipating heat via natural convection
%
% Run: octave examples/example_05_natural_conv_enclosure.m

addpath('../lib');

fprintf('=== Example 05: Electronics Enclosure Natural Convection ===\n\n');

% Aluminum enclosure: 200 x 150 x 80mm, 30W total dissipation, 40C ambient
W = 0.200; D = 0.150; H = 0.080;  % width, depth, height [m]
P = 30;  % watts
Ta = 40; % ambient [C]
eps = 0.85; % painted aluminum

fprintf('Enclosure: %.0fx%.0fx%.0fmm (WxDxH)\n', W*1e3, D*1e3, H*1e3);
fprintf('Power: %.0fW, Ambient: %.0fC, Emissivity: %.2f\n\n', P, Ta, eps);

% Define faces
faces(1).area = 2 * W * H;      % two side faces (vertical)
faces(1).char_length = H;
faces(1).orientation = 'vertical';
faces(1).emissivity = eps;

faces(2).area = 2 * D * H;      % front + back (vertical)
faces(2).char_length = H;
faces(2).orientation = 'vertical';
faces(2).emissivity = eps;

faces(3).area = W * D;           % top (horizontal heated up)
faces(3).char_length = W * D / (2 * (W + D));  % A/P characteristic length
faces(3).orientation = 'horizontal_top';
faces(3).emissivity = eps;

faces(4).area = W * D;           % bottom (horizontal heated down)
faces(4).char_length = W * D / (2 * (W + D));
faces(4).orientation = 'horizontal_bottom';
faces(4).emissivity = eps;

% Solve
[Ts, h_arr, q_arr] = free_conv_surface_temp(faces, Ta, P);

fprintf('Results:\n');
fprintf('  Surface temperature: %.1f C\n', Ts);
fprintf('  Temperature rise:    %.1f C\n', Ts - Ta);
fprintf('  Rth (surface-to-ambient): %.2f K/W\n', (Ts - Ta) / P);
fprintf('\nPer-face breakdown:\n');
face_names = {'Sides (2x)', 'Front+Back (2x)', 'Top', 'Bottom'};
for i = 1:4
    fprintf('  %-16s  A=%.4fm2  h=%.1f W/(m2K)  Q=%.1fW (%.0f%%)\n', ...
        face_names{i}, faces(i).area, h_arr(i), q_arr(i), q_arr(i)/P*100);
end
fprintf('  Total Q = %.2fW (should be %.0fW)\n', sum(q_arr), P);

fprintf('\nTypical range check:\n');
fprintf('  h natural conv (air, vertical): 5-25 W/(m2K)\n');
fprintf('  h radiation (eps=0.85, 60-80C): 5-8 W/(m2K)\n');
fprintf('  Combined h: 10-30 W/(m2K)\n');
fprintf('  Our h values: %.1f - %.1f W/(m2K) -> %s\n', ...
    min(h_arr), max(h_arr), ...
    iif(min(h_arr) > 5 && max(h_arr) < 40, 'OK', 'CHECK'));
end

function out = iif(cond, t, f)
    if cond, out = t; else, out = f; end
end
