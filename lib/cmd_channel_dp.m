function result = cmd_channel_dp(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m channel-dp --width <m> --height <m> --length <m> --flowrate <m3/s> [--t-air <C>]\n');
        result = struct(); return;
    end
    geom.width = str2double(parsed.width);
    geom.height = str2double(parsed.height);
    geom.length = str2double(parsed.length);
    fr = str2double(parsed.flowrate);
    if isfield(parsed, 't_air'), fluid = air_properties(str2double(parsed.t_air));
    else, fluid = air_properties(80); end
    [dp, Re] = channel_pressure_drop(geom, fr, fluid);
    result.dp = dp; result.Re = Re;
    fprintf('dp=%.4f\n', dp); fprintf('Re=%.1f\n', Re);
end
