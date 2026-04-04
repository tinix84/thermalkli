function result = workflow_optimize_fin(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m optimize-fin --config <file>\n');
        fprintf('Parametric sweep over fin thickness and heatsink thickness.\n');
        fprintf('Finds geometry with minimum thermal resistance.\n');
        result = struct(); return;
    end

    pkg load io;
    cfg = cli_load_config(parsed);

    fprintf('--- Extruded Fin Optimization ---\n');
    fprintf('Fluid: %s, flowrate: %.2f L/min, T_inlet: %.1f K\n', ...
        cfg.fluid.type, cfg.fluid.flowrate * 1000 * 60, cfg.fluid.tInlet);
    fprintf('P_loss: %.1f W, contact: %.1fx%.1f mm\n', ...
        cfg.heating.pLoss, cfg.heating.widthContact*1e3, cfg.heating.lengthContact*1e3);
    fprintf('\n');

    th_arr = cfg.sweep.thickHeatsink;
    tw_arr = cfg.sweep.thickWall;

    rth_matrix = zeros(length(th_arr), length(tw_arr));
    best_rth = Inf;
    best_i = 1; best_j = 1;

    fprintf('%-12s', 'thick\\wall');
    for j = 1:length(tw_arr)
        fprintf('%10.1f', tw_arr(j)*1e3);
    end
    fprintf('\n');
    fprintf('%s\n', repmat('-', 1, 12 + 10*length(tw_arr)));

    for i = 1:length(th_arr)
        fprintf('%-12.1f', th_arr(i)*1e3);
        for j = 1:length(tw_arr)
            numChannel = ceil((cfg.heatsink.heightTotal - tw_arr(j)) / ...
                (cfg.heatsink.widthChannel + tw_arr(j)));

            try
                hs = extrudedFinModel(...
                    cfg.heatsink.rhoSink, cfg.heatsink.kSink, cfg.heatsink.specHeat, ...
                    numChannel, th_arr(i), tw_arr(j), cfg.heatsink.widthChannel, ...
                    cfg.heatsink.numBridge);

                hs.defineFluid(cfg.fluid.type);
                hs.TFluidIn = cfg.fluid.tInlet;
                hs.flowrate = cfg.fluid.flowrate;

                hs.defineHeatingArrangement(...
                    cfg.heating.widthContact, cfg.heating.lengthContact, ...
                    cfg.heating.numHeatedSides, cfg.heating.maxDissLength, ...
                    cfg.heating.numInSeries, cfg.heating.spacing);

                hs.pLossComponent = cfg.heating.pLoss;
                hs.thermalResistance();

                rth_matrix(i, j) = hs.rThTot;
                fprintf('%10.4f', hs.rThTot);

                if hs.rThTot < best_rth
                    best_rth = hs.rThTot;
                    best_i = i; best_j = j;
                    best_hs = hs;
                end
            catch e
                rth_matrix(i, j) = NaN;
                fprintf('%10s', 'ERR');
            end
        end
        fprintf('\n');
    end

    fprintf('\n--- Optimal Configuration ---\n');
    fprintf('thick_heatsink=%.4f\n', th_arr(best_i));
    fprintf('thick_wall=%.4f\n', tw_arr(best_j));
    fprintf('rth_tot=%.6f\n', best_rth);
    fprintf('num_channels=%d\n', best_hs.numChannel);
    fprintf('reynolds=%.1f\n', best_hs.Re);

    result.rth_matrix = rth_matrix;
    result.best_rth = best_rth;
    result.best_thickHeatsink = th_arr(best_i);
    result.best_thickWall = tw_arr(best_j);

    if isfield(parsed, 'save_csv')
        fid = fopen(parsed.save_csv, 'w');
        fprintf(fid, 'thick_heatsink_m,thick_wall_m,rth_tot\n');
        for i = 1:length(th_arr)
            for j = 1:length(tw_arr)
                fprintf(fid, '%.6f,%.6f,%.6f\n', th_arr(i), tw_arr(j), rth_matrix(i,j));
            end
        end
        fclose(fid);
        fprintf('Results saved to: %s\n', parsed.save_csv);
    end

    fprintf('--- Complete ---\n');
end
