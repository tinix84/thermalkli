function result = workflow_semi_on_pcb(parsed)
    % workflow_semi_on_pcb - full ThermalModelSemi pipeline
    % Usage: thermal_cli.m semi-on-pcb --config <file> [overrides]

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m semi-on-pcb --config <file>\n');
        fprintf('Runs full semiconductor-on-PCB thermal model.\n');
        fprintf('Config must define all ThermalModelSemiInput fields.\n');
        result = struct();
        return;
    end

    cfg = cli_load_config(parsed);

    % Build ThermalModelSemiInput from config
    input = ThermalModelSemiInput;

    input.includeBottom = cfg.includeBottom;
    input.rThJCBottom = cfg.rThJCBottom;
    input.areaContact = cfg.areaContact;
    input.thInsContactPadPcb = cfg.thInsContactPadPcb;
    input.pcbLayerStack = cfg.pcbLayerStack;
    input.areaSingleVia = cfg.areaSingleVia;
    input.kVia = cfg.kVia;
    input.pcbNumVia = cfg.pcbNumVia;
    input.pcbEstimateNumVia = cfg.pcbEstimateNumVia;
    input.pcbViaSpacing = cfg.pcbViaSpacing;
    input.thInsContactPcbSink = cfg.thInsContactPcbSink;
    input.sinkLayerStack = cfg.sinkLayerStack;
    input.areaDissBottom = cfg.areaDissBottom;
    input.hFluidBottom = cfg.hFluidBottom;
    input.tempFluidBottom = cfg.tempFluidBottom;

    input.includeTop = cfg.includeTop;
    input.rThJCTop = cfg.rThJCTop;
    input.areaCaseTop = cfg.areaCaseTop;
    input.areaDissTop = cfg.areaDissTop;
    input.hFluidTop = cfg.hFluidTop;
    input.tempFluidTop = cfg.tempFluidTop;

    input.pLossJunction = cfg.pLossJunction;
    input.tempJunctionMax = cfg.tempJunctionMax;

    % Run model
    fprintf('--- Semi-on-PCB Thermal Model ---\n');
    model = ThermalModelSemi(input);

    if input.includeBottom
        model.calcRthFluidBot();
        fprintf('rth_case_fluid_bot=%.6f\n', model.output.rThCaseFluidBot);
    end

    model.calcTJunction();
    tJ = model.output.tJunction;
    for i = 1:length(tJ)
        fprintf('t_junction_%d=%.4f\n', i, tJ(i));
    end

    model.calcPLossMax();
    fprintf('p_loss_max=%.4f\n', model.output.pLossMax);

    model.calcADissMin();
    fprintf('a_diss_min=%.6e\n', model.output.aDissipationMin);

    model.calcHFluidMin();
    fprintf('h_fluid_min=%.4f\n', model.output.hFluidMin);

    fprintf('pcb_num_via=%d\n', model.output.pcbNumVia);

    % CSV export if requested
    if isfield(parsed, 'save_csv')
        fid = fopen(parsed.save_csv, 'w');
        fprintf(fid, 'point,value,unit\n');
        for i = 1:length(tJ)
            fprintf(fid, 'junction_temperature_%d,%.6f,K\n', i, tJ(i));
        end
        if input.includeBottom
            fprintf(fid, 'rth_case_fluid_bot,%.6f,K/W\n', model.output.rThCaseFluidBot);
        end
        fprintf(fid, 'p_loss_max,%.6f,W\n', model.output.pLossMax);
        fprintf(fid, 'a_diss_min,%.6e,m2\n', model.output.aDissipationMin);
        fprintf(fid, 'h_fluid_min,%.6f,W/(m2*K)\n', model.output.hFluidMin);
        fclose(fid);
        fprintf('Analytical results saved to: %s\n', parsed.save_csv);
    end

    % FEMM Lua generation if requested
    if isfield(parsed, 'femm_lua')
        lua_str = femm_semi_on_pcb(cfg);
        fid = fopen(parsed.femm_lua, 'w');
        fprintf(fid, '%s', lua_str);
        fclose(fid);
        fprintf('FEMM Lua script written to: %s\n', parsed.femm_lua);
    end

    fprintf('--- Complete ---\n');

    % Build result struct
    result.rThCaseFluidBot = model.output.rThCaseFluidBot;
    result.tJunction = model.output.tJunction;
    result.pLossMax = model.output.pLossMax;
    result.aDissipationMin = model.output.aDissipationMin;
    result.hFluidMin = model.output.hFluidMin;
    result.pcbNumVia = model.output.pcbNumVia;
end
