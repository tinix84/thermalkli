function result = cmd_natural_conv_hs(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m natural-conv-hs --n-fins <int> --fin-height <m> --fin-length <m>\n');
        fprintf('  --fin-thickness <m> --channel-width <m> --base-thickness <m>\n');
        fprintf('  --k <W/mK> --t-ambient <C> --p-loss <W> [--emissivity <->]\n');
        fprintf('Estimates heatsink Rth under natural convection (no fan).\n');
        result = struct(); return;
    end

    n = str2double(parsed.n_fins);
    Hf = str2double(parsed.fin_height);
    L = str2double(parsed.fin_length);
    tf = str2double(parsed.fin_thickness);
    s = str2double(parsed.channel_width);
    tb = str2double(parsed.base_thickness);
    k = str2double(parsed.k);
    Ta = str2double(parsed.t_ambient);
    P = str2double(parsed.p_loss);

    if isfield(parsed, 'emissivity')
        eps = str2double(parsed.emissivity);
    else
        eps = 0.9;
    end

    % Iterative solve: find Ts such that Q(Ts) = P
    Ts_low = Ta + 0.1;
    Ts_high = Ta + 200;

    for iter = 1:100
        Ts = (Ts_low + Ts_high) / 2;

        % Fin heat transfer (vertical surfaces)
        [h_fin_nat, ~] = h_natural_convection('vertical', Hf, Ta, Ts);
        h_fin_rad = h_radiation(eps, Ta, Ts);
        h_fin = h_fin_nat + h_fin_rad;

        % Fin efficiency
        m = sqrt(2 * h_fin / (k * tf));
        eta_fin = tanh(m * Hf) / (m * Hf);

        % Base exposed area (horizontal top, between fins)
        A_base = (n - 1) * s * L;
        [h_base_nat, ~] = h_natural_convection('horizontal_top', s, Ta, Ts);
        h_base_rad = h_radiation(eps, Ta, Ts);
        h_base = h_base_nat + h_base_rad;

        % Total heat dissipation
        A_fin = n * 2 * Hf * L;
        Q = h_fin * eta_fin * A_fin * (Ts - Ta) + h_base * A_base * (Ts - Ta);

        if abs(Q - P) < P * 1e-4
            break;
        end
        if Q > P
            Ts_high = Ts;
        else
            Ts_low = Ts;
        end
    end

    Rth = (Ts - Ta) / P;

    result.Ts = Ts;
    result.Rth = Rth;
    result.h_fin = h_fin;
    result.h_base = h_base;
    result.eta_fin = eta_fin;
    result.Q = Q;

    fprintf('t_surface=%.2f\n', Ts);
    fprintf('rth=%.4f\n', Rth);
    fprintf('h_fin=%.2f\n', h_fin);
    fprintf('h_base=%.2f\n', h_base);
    fprintf('eta_fin=%.4f\n', eta_fin);
    fprintf('dt=%.2f\n', Ts - Ta);
end
