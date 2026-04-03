function results = test_femm_generation()
% test_femm_generation - tests for femm_semi_on_pcb Lua generator

    results = {};

    % Build test config
    cfg.includeBottom = true;
    cfg.areaContact = 42e-6;
    cfg.pcbLayerStack = [[0.000635, 200]; [0.0003, 400]];
    cfg.sinkLayerStack = [[0.0048, 200]];
    cfg.areaDissBottom = 4 * 42e-6;
    cfg.hFluidBottom = 17000;
    cfg.tempFluidBottom = 343.15;
    cfg.includeTop = false;
    cfg.hFluidTop = 20;
    cfg.tempFluidTop = 343.15;
    cfg.pLossJunction = [67];

    lua = femm_semi_on_pcb(cfg);

    % Test 1: output is non-empty and contains newdocument(2)
    r.name = 'femm_semi_on_pcb: non-empty and contains newdocument(2)';
    try
        r.pass = ~isempty(lua) && ~isempty(strfind(lua, 'newdocument(2)'));
        r.detail = sprintf('lua length=%d chars', length(lua));
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 2: contains "axi" problem type
    r.name = 'femm_semi_on_pcb: contains "axi" problem type';
    try
        r.pass = ~isempty(strfind(lua, '"axi"'));
        r.detail = 'checked for hi_probdef axi string';
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 3: material definitions for each unique conductivity in PCB layers
    r.name = 'femm_semi_on_pcb: material definitions for PCB layer conductivities';
    try
        % PCB layers have k=200 and k=400; both should appear as hi_addmaterial
        has_200 = ~isempty(strfind(lua, 'hi_addmaterial("mat_k200"'));
        has_400 = ~isempty(strfind(lua, 'hi_addmaterial("mat_k400"'));
        r.pass = has_200 && has_400;
        r.detail = sprintf('k200=%d, k400=%d', has_200, has_400);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 4: heat flux boundary condition present
    r.name = 'femm_semi_on_pcb: heat flux boundary defined';
    try
        r.pass = ~isempty(strfind(lua, 'heatflux_source'));
        r.detail = 'checked for heatflux_source boundary';
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 5: convection boundary condition present
    r.name = 'femm_semi_on_pcb: convection boundary defined';
    try
        r.pass = ~isempty(strfind(lua, 'conv_bottom'));
        r.detail = 'checked for conv_bottom boundary';
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 6: solve and CSV extraction commands present
    r.name = 'femm_semi_on_pcb: hi_analyze and ho_getpointvalues present';
    try
        has_analyze = ~isempty(strfind(lua, 'hi_analyze()'));
        has_extract = ~isempty(strfind(lua, 'ho_getpointvalues'));
        has_csv     = ~isempty(strfind(lua, 'semi_on_pcb_results.csv'));
        r.pass = has_analyze && has_extract && has_csv;
        r.detail = sprintf('analyze=%d extract=%d csv=%d', has_analyze, has_extract, has_csv);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 7: source radius value correct
    r.name = 'femm_semi_on_pcb: correct source radius rc = sqrt(areaContact/pi)';
    try
        rc_expected = sqrt(cfg.areaContact / pi);
        % The Lua script should contain this value (up to float formatting)
        rc_str = sprintf('%.10g', rc_expected);
        r.pass = ~isempty(strfind(lua, rc_str));
        r.detail = sprintf('expected rc=%.10g in lua', rc_expected);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 8: includeTop=true adds conv_top boundary
    r.name = 'femm_semi_on_pcb: includeTop=true generates conv_top boundary';
    try
        cfg2 = cfg;
        cfg2.includeTop = true;
        lua2 = femm_semi_on_pcb(cfg2);
        r.pass = ~isempty(strfind(lua2, 'conv_top'));
        r.detail = 'checked conv_top in includeTop=true script';
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 9: includeTop=false uses insulated_top
    r.name = 'femm_semi_on_pcb: includeTop=false uses insulated_top boundary';
    try
        r.pass = ~isempty(strfind(lua, 'insulated_top'));
        r.detail = 'checked insulated_top when includeTop=false';
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 10: heat flux value is -P/A
    r.name = 'femm_semi_on_pcb: heat flux magnitude = pLoss/areaContact';
    try
        q_expected = -cfg.pLossJunction(1) / cfg.areaContact;
        q_str = sprintf('%.6g', q_expected);
        r.pass = ~isempty(strfind(lua, q_str));
        r.detail = sprintf('expected q=%.6g in heatflux_source definition', q_expected);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

end
