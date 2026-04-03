function result = cmd_hydraulic_op(parsed)
    % cmd_hydraulic_op - find fan-heatsink hydraulic operating point
    % Usage: thermal_cli.m hydraulic-op --config <file>
    % Config fields (all SI units):
    %   cfg.heatsink.profile  - heatsink name string (e.g. 'I117')
    %   cfg.heatsink.length   - heatsink length parallel to fins [m]
    %   cfg.heatsink.width    - heatsink width [m]
    %   cfg.fan.model         - fan name string (e.g. 'EBMW2E200_axial_AC_50Hz')
    %   cfg.fan.count         - number of fans in parallel
    %   cfg.ventilation.type  - 'push' or 'impinge'
    %   cfg.ventilation.impingeOpening - opening width for impinge type [m]
    %   cfg.ambient.tInlet    - inlet air temperature [K]

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m hydraulic-op --config <file>\n');
        fprintf('Finds fan-heatsink hydraulic operating point.\n');
        fprintf('Outputs: reynolds, pressure [Pa], flowrate [m^3/s], num_fins\n');
        result = struct();
        return;
    end

    cfg = cli_load_config(parsed);

    % --- Heatsink geometry from database (returns mm) ---
    [~, Hf_mm, tf_mm, bch_mm] = HS_Type(cfg.heatsink.profile);

    % --- Fan curve from database; scale for multiple fans in parallel ---
    [Hv1, Qv1, ~, ~, ~, ~] = Fan_Model(cfg.fan.model);
    nFans = cfg.fan.count;
    Qv = nFans * Qv1;   % parallel fans: flowrates add, pressure unchanged
    Hv = Hv1;

    % --- Derived geometry (convert SI to mm for idraulico) ---
    b_mm = cfg.heatsink.length * 1000;
    a_mm = cfg.heatsink.width  * 1000;
    Nf   = round(a_mm / (bch_mm + tf_mm));

    % --- Air temperature estimate (convert K -> °C; use inlet + 5 K margin) ---
    Tin_C  = cfg.ambient.tInlet - 273.15;
    Tair_C = Tin_C + 5;

    % --- Opening dimension for impinge; full width for push ---
    vent_type = cfg.ventilation.type;
    if strcmp(vent_type, 'impinge')
        s_mm = cfg.ventilation.impingeOpening * 1000;
    else
        s_mm = a_mm;
    end

    % --- Hydraulic operating point (idraulico works in mm / °C) ---
    [Redhavg, Hv_f, Qv_f] = idraulico(b_mm, s_mm, Nf, tf_mm, bch_mm, Hf_mm, Tair_C, vent_type, Qv, Hv);

    result.reynolds = Redhavg;
    result.pressure = Hv_f;
    result.flowrate = Qv_f;
    result.numFins  = Nf;

    fprintf('reynolds=%.1f\n',   Redhavg);
    fprintf('pressure=%.2f\n',   Hv_f);
    fprintf('flowrate=%.6f\n',   Qv_f);
    fprintf('num_fins=%d\n',     Nf);
end
