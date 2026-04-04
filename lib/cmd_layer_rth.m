function result = cmd_layer_rth(parsed)
    % cmd_layer_rth - calculate thermal resistance through a single layer
    % Usage: thermal_cli.m layer-rth --thick <m> --kop <W/mK> [--kip <W/mK>] --ain <m2> [--aout <m2>] [--heff <W/m2K>]

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m layer-rth --thick <m> --kop <W/mK> [--kip <W/mK>] --ain <m2> [--aout <m2>] [--heff <W/m2K>]\n');
        fprintf('Calculates thermal resistance through a single material layer.\n');
        fprintf('  --thick   Layer thickness [m]\n');
        fprintf('  --kop     Out-of-plane thermal conductivity [W/(m*K)]\n');
        fprintf('  --kip     In-plane thermal conductivity [W/(m*K)] (optional, defaults to kop)\n');
        fprintf('  --ain     Heat source area [m2]\n');
        fprintf('  --aout    Heat sink area [m2] (optional, for spreading calculation)\n');
        fprintf('  --heff    Effective heat transfer coefficient [W/(m2*K)] (required if aout != ain)\n');
        result = struct();
        return;
    end

    thick = str2double(parsed.thick);
    kOp = str2double(parsed.kop);

    if isfield(parsed, 'kip')
        kIp = str2double(parsed.kip);
        layer = ThermalLayer(thick, kOp, kIp);
    else
        layer = ThermalLayer(thick, kOp);
    end

    aIn = str2double(parsed.ain);

    if isfield(parsed, 'aout') && isfield(parsed, 'heff')
        aOut = str2double(parsed.aout);
        hEff = str2double(parsed.heff);
        [rTh, rThSpread, rThThrough] = layer.thermalLayerResistance(aIn, aOut, hEff);
        result.rth = rTh;
        result.rth_spread = rThSpread;
        result.rth_through = rThThrough;
        fprintf('rth=%.6f\n', rTh);
        fprintf('rth_spread=%.6f\n', rThSpread);
        fprintf('rth_through=%.6f\n', rThThrough);
    else
        rTh = layer.thermalLayerResistance(aIn);
        result.rth = rTh;
        fprintf('rth=%.6f\n', rTh);
    end
end
