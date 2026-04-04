function result = cmd_cspi(parsed)
    % cmd_cspi - compute CSPI = 1 / (Rth * Vol)
    % Usage: thermal_cli.m cspi --rth <K/W> --vol <liters>
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m cspi --rth <K/W> --vol <liters>\n');
        fprintf('Computes CSPI = 1 / (Rth_S-a * Vol_CS) [W/(K*liter)].\n');
        fprintf('\nOptions:\n');
        fprintf('  --rth   heatsink thermal resistance [K/W]\n');
        fprintf('  --vol   heatsink volume [liters]\n');
        result = struct(); return;
    end

    rth = str2double(parsed.rth);
    vol = str2double(parsed.vol);

    cspi = cspi_calc(rth, vol);

    result.cspi = cspi;
    fprintf('cspi=%.4f\n', cspi);
end
