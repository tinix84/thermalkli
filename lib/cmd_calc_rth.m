function result = cmd_calc_rth(parsed)
    % cmd_calc_rth - calculate thermal resistance from power and temperatures
    % Usage: thermal_cli.m calc-rth --power <W> --tref <K> --tmeas <K>

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m calc-rth --power <W> --tref <K> --tmeas <K>\n');
        fprintf('Calculates thermal resistance: Rth = (Tmeas - Tref) / P\n');
        result = struct();
        return;
    end

    P = str2double(parsed.power);
    Tref = str2double(parsed.tref);
    Tmeas = str2double(parsed.tmeas);

    rth = calc_rth_from_power_temp(P, Tref, Tmeas);

    result.rth = rth;
    fprintf('rth=%.6f\n', rth);
end
