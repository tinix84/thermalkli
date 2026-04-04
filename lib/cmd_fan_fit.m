function result = cmd_fan_fit(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m fan-fit --v-max <m3/s> --dp-max <Pa> --p-fan <W> --diameter <m> --speed <rpm>\n');
        fprintf('Fits fan scaling law constants k1, k2, k3.\n');
        result = struct(); return;
    end
    V_max = str2double(parsed.v_max);
    dp_max = str2double(parsed.dp_max);
    P_fan = str2double(parsed.p_fan);
    D = str2double(parsed.diameter);
    N = str2double(parsed.speed);
    [k1, k2, k3] = fan_scaling_fit(V_max, dp_max, P_fan, D, N);
    result.k1 = k1; result.k2 = k2; result.k3 = k3;
    fprintf('k1=%.4e\n', k1);
    fprintf('k2=%.4e\n', k2);
    fprintf('k3=%.4e\n', k3);
    fprintf('\nDrofenik survey ranges (65 fans):\n');
    fprintf('  k1: [0.5e-3 .. 13.5e-3] (got %.2e)\n', k1);
    fprintf('  k2: [3.9e-4 .. 8.85e-4] (got %.2e)\n', k2);
    fprintf('  k3: [3.0e-6 .. 76.5e-6] (got %.2e)\n', k3);
end
