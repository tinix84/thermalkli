function results = test_multi_sim()
    results = {};

    % Test 1: core solver runs without error on a simple config
    r.name = 'multi_sim_core: runs without error';
    try
        sol.hs_type = 'all_aluminum';
        sol.fan_model = 'EBMW1G180_axial_DC';
        sol.n_fans = 2;
        sol.vent_type = 'impinge';
        sol.impinge_opening = 250;

        geom.a_init = 400; geom.b_init = 400;
        geom.a_max = 550; geom.b_max = 600;
        geom.tf = 1.5; geom.Hf = 48; geom.bch = 2.5; geom.tb = 10; geom.tr = 10;

        sources.a_n = [110 110 110];
        sources.b_n = [80 80 80];
        sources.p_n = [710 710 710];
        sources.x_g = [100 200 300];
        sources.y_g = [200 200 200];
        sources.columns = [1 2 3];
        sources.rows = [1 1 1];
        sources.Tmax = [93 93 93];
        sources.scelta = 'centro';

        params.Tin = 25; params.Niter = 10; params.piastra = 'no';
        params.Dx = 5; params.Dy = 5;

        res = multi_sim_core(sol, geom, sources, params);
        r.pass = isstruct(res) && isfield(res, 'solved_therm') && isfield(res, 'Rth_fin');
        r.detail = sprintf('solved_therm=%d, Rth=%.4f, a=%d, b=%d, iter=%d', ...
            res.solved_therm, res.Rth_fin, res.a, res.b, res.iterations);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 2: heatsink grows when temps exceed limits
    r.name = 'multi_sim_core: heatsink grows when over temp';
    try
        % Use very high power to force resizing
        sources2 = sources;
        sources2.p_n = [2000 2000 2000];
        res2 = multi_sim_core(sol, geom, sources2, params);
        r.pass = res2.a > geom.a_init || res2.b > geom.b_init;
        r.detail = sprintf('a: %d->%d, b: %d->%d', geom.a_init, res2.a, geom.b_init, res2.b);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 3: result has all required fields
    r.name = 'multi_sim_core: result has all fields';
    try
        res = multi_sim_core(sol, geom, sources, params);
        required = {'a','b','tf','Hf','Nf','Ths','Th_BP','Rth_fin','Qv_f','solved_hydr','solved_therm'};
        missing = {};
        for i = 1:length(required)
            if ~isfield(res, required{i})
                missing{end+1} = required{i};
            end
        end
        r.pass = isempty(missing);
        r.detail = sprintf('missing: %s', strjoin(missing, ', '));
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;
end
