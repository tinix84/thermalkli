function result = cmd_channel_rth(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m channel-rth --width <m> --height <m> --length <m> --flowrate <m3/s> [--t-air <C>]\n');
        result = struct(); return;
    end
    geom.width = str2double(parsed.width);
    geom.height = str2double(parsed.height);
    geom.length = str2double(parsed.length);
    fr = str2double(parsed.flowrate);
    if isfield(parsed, 't_air'), fluid = air_properties(str2double(parsed.t_air));
    else, fluid = air_properties(80); end
    [rth, Re, Nu, h] = channel_rth(geom, fr, fluid);
    result.rth = rth; result.Re = Re; result.Nu = Nu; result.h = h;
    fprintf('rth=%.6f\n', rth); fprintf('Re=%.1f\n', Re);
    fprintf('Nu=%.2f\n', Nu); fprintf('h=%.2f\n', h);
end
