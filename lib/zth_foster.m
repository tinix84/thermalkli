function [Zth, t] = zth_foster(R, tau, t_end, n_points)
    % zth_foster - compute transient thermal impedance using Foster network
    %   R: array of thermal resistances [K/W]
    %   tau: array of time constants [s] (tau_i = R_i * C_i)
    %   t_end: end time [s]
    %   n_points: number of time points (default 200)
    %   Returns: Zth array [K/W], t array [s]

    if nargin < 4, n_points = 200; end

    t = logspace(log10(min(tau)/10), log10(t_end), n_points);
    Zth = zeros(size(t));
    for i = 1:length(R)
        Zth = Zth + R(i) * (1 - exp(-t / tau(i)));
    end
end
