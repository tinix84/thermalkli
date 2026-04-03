function result = cmd_stack_rth(parsed)
    % cmd_stack_rth - calculate thermal resistance through a layer stack
    % Usage: thermal_cli.m stack-rth --config <file> [--ain <m2>] [--aout <m2>] [--heff <W/m2K>]

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m stack-rth --config <file> [--ain <m2>] [--aout <m2>] [--heff <W/m2K>]\n');
        fprintf('Calculates thermal resistance through a multi-layer stack.\n');
        fprintf('Config must define cfg.layers as [[thick1,kOp1]; [thick2,kOp2]; ...] or\n');
        fprintf('  [[thick1,kOp1,kIp1]; [thick2,kOp2,kIp2]; ...]\n');
        fprintf('  --ain     Heat source area [m2]\n');
        fprintf('  --aout    Heat sink area [m2] (optional)\n');
        fprintf('  --heff    Effective heat transfer coefficient [W/(m2*K)] (required if aout given)\n');
        result = struct();
        return;
    end

    cfg = cli_load_config(parsed);

    stack = ThermalLayerStack();
    for i = 1:size(cfg.layers, 1)
        row = cfg.layers(i, :);
        if length(row) == 3
            stack.addLayer(ThermalLayer(row(1), row(2), row(3)));
        else
            stack.addLayer(ThermalLayer(row(1), row(2)));
        end
    end

    aIn = str2double(parsed.ain);

    if isfield(parsed, 'aout') && isfield(parsed, 'heff')
        aOut = str2double(parsed.aout);
        hEff = str2double(parsed.heff);
        [rTh, rThSpread, rThThrough] = stack.thermalLayerResistance(aIn, aOut, hEff);
        result.rth = rTh;
        result.rth_spread = rThSpread;
        result.rth_through = rThThrough;
        fprintf('rth=%.6f\n', rTh);
        fprintf('rth_spread=%.6f\n', rThSpread);
        fprintf('rth_through=%.6f\n', rThThrough);
    else
        rTh = stack.thermalLayerResistance(aIn);
        result.rth = rTh;
        fprintf('rth=%.6f\n', rTh);
    end

    fprintf('n_layers=%d\n', stack.n);
    fprintf('total_thick=%.6f\n', stack.thick);
    fprintf('kop_equiv=%.6f\n', stack.kOp);
    result.n_layers = stack.n;
    result.total_thick = stack.thick;
    result.kop_equiv = stack.kOp;
end
