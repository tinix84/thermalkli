function result = workflow_forced_conv_sim(parsed)
    % workflow_forced_conv_sim - forced convection heatsink simulation
    % Replaces interactive Simulazione_Singola.m
    % Chains: hydraulic OP -> fin Rth -> temperature distribution
    %
    % Usage: thermal_cli.m forced-conv-sim --config <file>
    % Config fields (SI units — meters, Kelvin):
    %   cfg.heatsink.profile   - heatsink name string
    %   cfg.heatsink.width     - heatsink width [m]
    %   cfg.heatsink.length    - heatsink length parallel to fins [m]
    %   cfg.heatsink.material  - material name (e.g. 'all_aluminum')
    %   cfg.fan.model          - fan name string
    %   cfg.fan.count          - number of fans in parallel
    %   cfg.ventilation.type   - 'push' or 'impinge'
    %   cfg.ventilation.impingeOpening - opening width for impinge [m]
    %   cfg.ambient.tInlet     - inlet air temperature [K]
    %   cfg.sources.power      - power vector [W]
    %   cfg.sources.width      - source width vector [m]
    %   cfg.sources.length     - source length vector [m]
    %   cfg.sources.x          - source x-centroid vector [m]
    %   cfg.sources.y          - source y-centroid vector [m]
    %   cfg.niter              - Fourier series iteration count
    %   cfg.piastra            - 'yes' or 'no' (copper spreader plate)
    %   cfg.grid_points        - number of grid points per axis

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m forced-conv-sim --config <file>\n');
        fprintf('Runs forced convection heatsink simulation.\n');
        result = struct();
        return;
    end

    cfg = cli_load_config(parsed);
    fprintf('--- Forced Convection Simulation ---\n');

    % --- Heatsink geometry from database (returns mm) ---
    [tb_mm, Hf_mm, tf_mm, bch_mm] = HS_Type(cfg.heatsink.profile);

    % --- Material thermal conductivity ---
    [Kth_plate, Kth_fin, Kth_piastra, ~, Piastra_flag, ~] = HS_Tech(cfg.heatsink.material);

    % --- Convert SI dimensions to mm for SoftwareTermico functions ---
    a_mm = cfg.heatsink.width  * 1000;
    b_mm = cfg.heatsink.length * 1000;
    Nf   = round(a_mm / (bch_mm + tf_mm));

    % --- Fan curve (parallel fans: flowrates add, pressure unchanged) ---
    [Hv1, Qv1, ~, ~, ~, ~] = Fan_Model(cfg.fan.model);
    Qv = cfg.fan.count * Qv1;
    Hv = Hv1;

    % --- Ventilation opening ---
    vent_type = cfg.ventilation.type;
    if strcmp(vent_type, 'impinge')
        s_mm = cfg.ventilation.impingeOpening * 1000;
    else
        s_mm = a_mm;
    end

    % --- Source arrays: convert SI to mm ---
    p_n = cfg.sources.power;
    a_n = cfg.sources.width  * 1000;
    b_n = cfg.sources.length * 1000;
    x_g = cfg.sources.x     * 1000;
    y_g = cfg.sources.y     * 1000;

    % --- Inlet temperature: K -> degC ---
    Tin_C = cfg.ambient.tInlet - 273.15;

    % --- Step 1: Hydraulic operating point ---
    fprintf('Step 1: Hydraulic operating point\n');
    % First-pass air temperature estimate
    Tair_C = Tin_C + 0.5 * sum(p_n) / (Cp_air(Tin_C) * rho_air(Tin_C) * mean(Qv));
    [Redhavg, Hv_f, Qv_f] = idraulico(b_mm, s_mm, Nf, tf_mm, bch_mm, Hf_mm, Tair_C, vent_type, Qv, Hv);
    fprintf('  flowrate=%.6f m3/s\n', Qv_f);
    % Refine Tair with actual flowrate
    Tair_C = Tin_C + 0.5 * sum(p_n) / (Cp_air(Tin_C) * rho_air(Tin_C) * Qv_f);

    % --- Step 2: Fin thermal resistance ---
    fprintf('Step 2: Fin thermal resistance\n');
    [~, Vch1, Vch2, Rth, hf_eq] = Rth_fin(Qv_f, a_mm, b_mm, s_mm, tf_mm, bch_mm, Hf_mm, Tair_C, vent_type, Kth_fin, Nf);
    fprintf('  rth_fin=%.6f K/W\n', Rth);
    fprintf('  h_eq=%.2f W/(m2*K)\n', hf_eq);

    % --- Step 3: Temperature distribution ---
    fprintf('Step 3: Temperature distribution\n');
    tr_mm    = 1;       % copper spreader thickness [mm] (used only when Piastra='yes')
    Piastra  = cfg.piastra;
    Niter    = cfg.niter;
    n_grid   = cfg.grid_points;
    Xp = linspace(0, a_mm, n_grid);
    Yp = linspace(0, b_mm, n_grid);

    % Tplane_dist contains figure/contourf plotting code; use gnuplot toolkit
    % so the plot is rendered off-screen without requiring a display.
    try
        graphics_toolkit('gnuplot');
    catch
        % ignore if gnuplot is unavailable; plot may silently fail
    end

    [Ths, Th_BP] = Tplane_dist(Rth, p_n, Tair_C, Tin_C, Niter, Piastra, ...
        a_mm, b_mm, x_g, y_g, Kth_plate, tb_mm, a_n, b_n, Kth_piastra, tr_mm, hf_eq, Xp, Yp);

    close all;  % close any figures created by Tplane_dist

    T_max = max(Ths(:));
    [row, col] = find(Ths == T_max, 1);
    x_max_m = Xp(col) / 1000;
    y_max_m = Yp(row) / 1000;

    fprintf('  baseplate_temp=%.2f C\n', Th_BP);
    fprintf('  max_surface_temp=%.2f C\n', T_max);
    fprintf('  max_temp_x=%.4f m\n', x_max_m);
    fprintf('  max_temp_y=%.4f m\n', y_max_m);

    % --- Build result struct ---
    result.flowrate         = Qv_f;
    result.rth_fin          = Rth;
    result.h_eq             = hf_eq;
    result.baseplate_temp   = Th_BP;
    result.max_surface_temp = T_max;

    % --- Optional CSV output ---
    if isfield(parsed, 'save_csv')
        fid = fopen(parsed.save_csv, 'w');
        fprintf(fid, 'point,value,unit\n');
        fprintf(fid, 'flowrate,%.6f,m3/s\n',         Qv_f);
        fprintf(fid, 'rth_fin,%.6f,K/W\n',            Rth);
        fprintf(fid, 'baseplate_temp,%.2f,C\n',       Th_BP);
        fprintf(fid, 'max_surface_temp,%.2f,C\n',     T_max);
        fclose(fid);
        fprintf('Results saved to: %s\n', parsed.save_csv);
    end

    fprintf('--- Complete ---\n');
end
