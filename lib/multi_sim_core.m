function result = multi_sim_core(sol, geom, sources, params)
    % multi_sim_core - solve one heatsink configuration
    % Runs hydraulic + thermal pipeline, checks temperature limits,
    % auto-resizes heatsink if limits exceeded.
    %
    % sol: struct with fan/material/ventilation definition
    %   .hs_type       string -> HS_Tech lookup
    %   .fan_model     string -> Fan_Model lookup
    %   .n_fans        number of parallel fans
    %   .vent_type     'push' or 'impinge'
    %   .impinge_opening  [mm] opening for impinge mode
    % geom: struct with heatsink geometry for this iteration
    %   .a_init        [mm] initial heatsink width (perp to fins)
    %   .b_init        [mm] initial heatsink length (parallel to fins)
    %   .a_max         [mm] max width
    %   .b_max         [mm] max length
    %   .tf            [mm] fin thickness
    %   .Hf            [mm] fin height
    %   .bch           [mm] channel width (= pitch - tf)
    %   .tb            [mm] base thickness
    %   .tr            [mm] plate thickness
    % sources: struct with heat source definition
    %   .a_n           [mm] array of source widths
    %   .b_n           [mm] array of source lengths
    %   .p_n           [W]  array of source powers
    %   .x_g           [mm] array of initial source X positions
    %   .y_g           [mm] array of initial source Y positions
    %   .columns       array mapping each source to a column group
    %   .rows          array mapping each source to a row group
    %   .Tmax          [C] array of max temperatures per measurement point
    %   .scelta        'centro' or 'side'
    % params: struct with solver parameters
    %   .Tin           [C] inlet air temperature
    %   .Niter         number of Fourier iterations
    %   .piastra       'yes' or 'no'
    %   .Dx            [mm] column shift increment
    %   .Dy            [mm] row shift increment

    % Get material properties
    [Kth_plate, Kth_fin, Kth_piastra, Cost_kg, Piastra_str, rho_arr] = HS_Tech(sol.hs_type);

    % Validate spreader plate: disable if material has no plate conductivity
    if ~strcmpi(Piastra_str, 'yes') || Kth_piastra <= 0
        params.piastra = 'no';
    end

    % Get fan curves
    [Hv1, Qv1, Qvmin1, Qvmax1, Cost_Fan1, Vol_Fan1] = Fan_Model(sol.fan_model);
    Qv = sol.n_fans * Qv1;
    Hv = Hv1;
    Qvmin = sol.n_fans * Qvmin1;
    Qvmax = sol.n_fans * Qvmax1;

    % Initialize geometry
    a = geom.a_init;
    b = geom.b_init;
    x_g1 = sources.x_g;
    y_g1 = sources.y_g;

    % Ventilation
    if strcmp(sol.vent_type, 'impinge')
        s = sol.impinge_opening;
    else
        s = a;
    end

    % Initial air temp estimate
    Qguess = (Qvmin + Qvmax) / 2;
    Tair = params.Tin + 0.5 * sum(sources.p_n) / (Cp_air(params.Tin) * rho_air(params.Tin) * Qguess);

    % Resize loop
    Nf = round(a / (geom.bch + geom.tf));
    Ths = sources.Tmax * 2;  % force entry into loop
    max_iterations = 50;
    iter = 0;

    while any(Ths > sources.Tmax) && iter < max_iterations
        iter = iter + 1;
        Nf = round(a / (geom.bch + geom.tf));
        if Nf < 2
            error('multi_sim_core: Nf=%d (must be >= 2). Channel too wide for heatsink width a=%.0fmm.', Nf, a);
        end

        % Hydraulic
        [Re_hydr, Hv_f, Qv_f] = idraulico(b, s, Nf, geom.tf, geom.bch, geom.Hf, Tair, sol.vent_type, Qv, Hv);
        Tair = params.Tin + 0.5 * sum(sources.p_n) / (Cp_air(params.Tin) * rho_air(params.Tin) * Qv_f);

        % Thermal resistance
        [Re_therm, Vch1, Vch2, Rth_fin1, hf_eq] = Rth_fin(Qv_f, a, b, s, geom.tf, geom.bch, geom.Hf, Tair, sol.vent_type, Kth_fin, Nf);

        % Baseplate temperature
        LMTD = Rth_fin1 * sum(sources.p_n);
        Tfluido_out = (Tair - params.Tin) * 2 + params.Tin;
        Th_BP = (params.Tin - Tfluido_out * exp((Tfluido_out - params.Tin) / LMTD)) / ...
                (1 - exp((Tfluido_out - params.Tin) / LMTD)) - LMTD;

        % Temperature at measurement points
        if ~strcmp(sources.scelta, 'centro')
            error('multi_sim_core: only scelta=''centro'' is supported. XY_Thscalc has a bug in ''side'' mode (undefined variable bn).');
        end
        [xThs, yThs] = XY_Thscalc(x_g1, y_g1, sources.a_n, sources.b_n, sources.scelta);
        Ths = zeros(1, length(sources.Tmax));
        for i = 1:length(sources.Tmax)
            [~, Ths(i)] = Temp_calc(xThs(i), yThs(i), params.Niter, params.piastra, ...
                sources.p_n, a, b, x_g1, y_g1, Kth_plate, geom.tb, ...
                sources.a_n, sources.b_n, Kth_piastra, geom.tr, Th_BP, hf_eq);
        end

        % Check if all temperatures OK
        if all(Ths <= sources.Tmax)
            break;
        end

        % Auto-resize: shift columns and rows that exceed limits
        Nmovex = 0;
        Nmovey = 0;

        if a < geom.a_max
            for nc = 1:max(sources.columns)
                c_idx = find(sources.columns == nc);
                c_higher = find(sources.columns > nc);
                if strcmp(sources.scelta, 'centro')
                    over = any(Ths(c_idx) > sources.Tmax(c_idx));
                else
                    over = any([Ths(2*c_idx-1) Ths(2*c_idx)] > [sources.Tmax(2*c_idx-1) sources.Tmax(2*c_idx)]);
                end
                if over
                    x_g1(c_idx) = x_g1(c_idx) + params.Dx;
                    x_g1(c_higher) = x_g1(c_higher) + 2 * params.Dx;
                    Nmovex = Nmovex + 1;
                end
            end
        end

        if b < geom.b_max
            for nr = 1:max(sources.rows)
                r_idx = find(sources.rows == nr);
                r_higher = find(sources.rows > nr);
                if strcmp(sources.scelta, 'centro')
                    over = any(Ths(r_idx) > sources.Tmax(r_idx));
                else
                    over = any([Ths(2*r_idx-1) Ths(2*r_idx)] > [sources.Tmax(2*r_idx-1) sources.Tmax(2*r_idx)]);
                end
                if over
                    y_g1(r_idx) = y_g1(r_idx) + params.Dy;
                    y_g1(r_higher) = y_g1(r_higher) + 2 * params.Dy;
                    Nmovey = Nmovey + 1;
                end
            end
        end

        % Update heatsink dimensions
        a_new = a + 2 * Nmovex * params.Dx;
        b_new = b + 2 * Nmovey * params.Dy;
        a = min(a_new, geom.a_max);
        b = min(b_new, geom.b_max);

        if strcmp(sol.vent_type, 'impinge')
            s = sol.impinge_opening;
        else
            s = a;
        end

        % Exit if at max size
        if a >= geom.a_max && b >= geom.b_max
            break;
        end
    end

    % Check solution validity
    if Qv_f > Qvmin && Qv_f < Qvmax
        solved_hydr = true;
    else
        solved_hydr = false;
    end
    solved_therm = all(Ths <= sources.Tmax);

    % Build result
    result.a = a;
    result.b = b;
    result.tf = geom.tf;
    result.Hf = geom.Hf;
    result.bch = geom.bch;
    result.tb = geom.tb;
    result.tr = geom.tr;
    result.Nf = Nf;
    result.Ths = Ths;
    result.Tmax = sources.Tmax;
    result.Th_BP = Th_BP;
    result.Rth_fin = Rth_fin1;
    result.hf_eq = hf_eq;
    result.Qv_f = Qv_f;
    result.Hv_f = Hv_f;
    result.Re_hydr = Re_hydr;
    result.Re_therm = Re_therm;
    result.Vch2 = Vch2;
    result.Tair = Tair;
    result.x_g = x_g1;
    result.y_g = y_g1;
    result.solved_hydr = solved_hydr;
    result.solved_therm = solved_therm;
    result.iterations = iter;
    result.sol_desc = sprintf('%s %s %dx%s', sol.hs_type, sol.vent_type, sol.n_fans, sol.fan_model);
end
