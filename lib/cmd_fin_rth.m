function result = cmd_fin_rth(parsed)
    % cmd_fin_rth - calculate finned heatsink thermal resistance
    % Usage: thermal_cli.m fin-rth --config <file> --flowrate <m3/s>
    % Config fields (all SI units):
    %   cfg.heatsink.profile  - heatsink name string (e.g. 'I117')
    %   cfg.heatsink.length   - heatsink length parallel to fins [m]
    %   cfg.heatsink.width    - heatsink width [m]
    %   cfg.heatsink.material - material name (e.g. 'all_aluminum')
    %   cfg.ventilation.type  - 'push' or 'impinge'
    %   cfg.ventilation.impingeOpening - opening width for impinge type [m]
    %   cfg.ambient.tInlet    - inlet air temperature [K]
    % Option:
    %   --flowrate <m3/s>     - volumetric airflow rate [m^3/s]

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m fin-rth --config <file> --flowrate <m3/s>\n');
        fprintf('Calculates finned heatsink thermal resistance.\n');
        fprintf('Outputs: rth [K/W], h_eq [W/(m^2.K)], reynolds, v_ch1, v_ch2 [m/s]\n');
        result = struct();
        return;
    end

    cfg = cli_load_config(parsed);
    Qv_f = str2double(parsed.flowrate);

    % --- Heatsink geometry from database (returns mm) ---
    [~, Hf_mm, tf_mm, bch_mm] = HS_Type(cfg.heatsink.profile);

    % --- Material thermal conductivity ---
    [~, Kth_fin, ~, ~, ~, ~] = HS_Tech(cfg.heatsink.material);

    % --- Derived geometry (convert SI to mm for Rth_fin) ---
    a_mm = cfg.heatsink.width  * 1000;
    b_mm = cfg.heatsink.length * 1000;
    Nf   = round(a_mm / (bch_mm + tf_mm));

    % --- Opening dimension for impinge; full width for push ---
    vent_type = cfg.ventilation.type;
    if strcmp(vent_type, 'impinge')
        s_mm = cfg.ventilation.impingeOpening * 1000;
    else
        s_mm = a_mm;
    end

    % --- Air temperature estimate (convert K -> degC; use inlet + 5 K margin) ---
    Tin_C  = cfg.ambient.tInlet - 273.15;
    Tair_C = Tin_C + 5;

    % --- Thermal resistance calculation (Rth_fin works in mm / degC) ---
    [Rebavg, Vch1, Vch2, Rth, hf_eq] = Rth_fin(Qv_f, a_mm, b_mm, s_mm, tf_mm, bch_mm, Hf_mm, Tair_C, vent_type, Kth_fin, Nf);

    result.reynolds = Rebavg;
    result.rth      = Rth;
    result.h_eq     = hf_eq;
    result.v_ch1    = Vch1;
    result.v_ch2    = Vch2;

    fprintf('rth=%.6f\n',     Rth);
    fprintf('h_eq=%.2f\n',    hf_eq);
    fprintf('reynolds=%.1f\n', Rebavg);
    fprintf('v_ch1=%.4f\n',   Vch1);
    fprintf('v_ch2=%.4f\n',   Vch2);
end
