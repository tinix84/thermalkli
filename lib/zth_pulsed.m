function Zth_pulsed = zth_pulsed(R, tau, t, D, T)
    % zth_pulsed - pulsed thermal impedance from Foster model
    % Uses superposition: Zth_pulse(t) = D * Zth(t) + (1-D) * sum correction terms
    % Simplified approach: Zth_pulse ≈ Zth(D*T) for t >> T (steady-state pulsing)
    % Full approach: Zth(t) - Zth(t-D*T) + Zth(t-T) - Zth(t-T-D*T) + ...

    Zth_pulsed = zeros(size(t));
    for i = 1:length(t)
        val = 0;
        n_pulses = floor(t(i) / T) + 1;
        n_pulses = min(n_pulses, 100);  % limit for computation
        for k = 0:n_pulses-1
            t_on = t(i) - k * T;
            t_off = t(i) - k * T - D * T;
            if t_on > 0
                for j = 1:length(R)
                    val = val + R(j) * (1 - exp(-t_on / tau(j)));
                end
            end
            if t_off > 0
                for j = 1:length(R)
                    val = val - R(j) * (1 - exp(-t_off / tau(j)));
                end
            end
        end
        Zth_pulsed(i) = val;
    end
end
