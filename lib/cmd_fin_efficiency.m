function result = cmd_fin_efficiency(parsed)
    % cmd_fin_efficiency - calculate fin efficiency
    % Usage: thermal_cli.m fin-efficiency --length <m> --h <W/m2K> --area <m2> --k <W/mK> --ac <m2>

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m fin-efficiency --length <m> --h <W/m2K> --area <m2> --k <W/mK> --ac <m2>\n');
        fprintf('Calculates fin efficiency using eta = tanh(mL)/mL.\n');
        fprintf('  --length  Fin length [m]\n');
        fprintf('  --h       Heat transfer coefficient [W/(m2*K)]\n');
        fprintf('  --area    Fin surface area [m2]\n');
        fprintf('  --k       Fin thermal conductivity [W/(m*K)]\n');
        fprintf('  --ac      Fin cross-sectional area [m2]\n');
        result = struct();
        return;
    end

    L  = str2double(parsed.length);
    h  = str2double(parsed.h);
    A  = str2double(parsed.area);
    k  = str2double(parsed.k);
    Ac = str2double(parsed.ac);

    eta = finEfficieny(L, h, A, k, Ac);

    result.eta = eta;
    fprintf('eta=%.6f\n', eta);
end
