function result = cmd_free_conv(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m free-conv --config <file>\n');
        fprintf('Finds surface temperature from natural convection + radiation.\n');
        fprintf('Config defines faces array with area, char_length, orientation, emissivity.\n');
        result = struct(); return;
    end

    cfg = cli_load_config(parsed);

    % Build faces struct array from config
    n_faces = length(cfg.faces.area);
    for i = 1:n_faces
        faces(i).area = cfg.faces.area(i);
        faces(i).char_length = cfg.faces.char_length(i);
        faces(i).orientation = cfg.faces.orientation{i};
        if isfield(cfg.faces, 'emissivity')
            faces(i).emissivity = cfg.faces.emissivity(i);
        else
            faces(i).emissivity = 0.9;
        end
    end

    [T_s, h_arr, q_arr] = free_conv_surface_temp(faces, cfg.t_ambient, cfg.p_total);

    fprintf('t_surface=%.2f\n', T_s);
    fprintf('dt=%.2f\n', T_s - cfg.t_ambient);
    for i = 1:n_faces
        fprintf('face_%d_h=%.2f\n', i, h_arr(i));
        fprintf('face_%d_q=%.4f\n', i, q_arr(i));
    end
    fprintf('q_total=%.4f\n', sum(q_arr));

    result.T_surface = T_s;
    result.h_arr = h_arr;
    result.q_arr = q_arr;
end
