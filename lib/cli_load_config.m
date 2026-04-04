function cfg = cli_load_config(parsed)
    % cli_load_config - load config from .m file and merge CLI overrides
    % If parsed.config exists, calls the .m function to get base config.
    % Then merges any --key.sub value overrides from parsed.

    if isfield(parsed, 'config')
        config_path = parsed.config;
        [dir_path, func_name, ~] = fileparts(config_path);
        if ~isempty(dir_path)
            addpath(dir_path);
        end
        cfg = feval(func_name);
    else
        cfg = struct();
    end

    % Merge overrides: fields with underscores map to nested struct fields
    fnames = fieldnames(parsed);
    skip_fields = {'config', 'help', 'verbose', 'femm_lua', 'save_csv', 'output'};
    for i = 1:length(fnames)
        key = fnames{i};
        if any(strcmp(key, skip_fields))
            continue;
        end
        val = parsed.(key);
        parts = strsplit(key, '_');
        if length(parts) == 2
            % nested: fluid_flowrate -> cfg.fluid.flowrate
            num_val = str2double(val);
            if ~isnan(num_val)
                cfg.(parts{1}).(parts{2}) = num_val;
            else
                cfg.(parts{1}).(parts{2}) = val;
            end
        else
            % flat: power -> cfg.power (preserve original value type)
            cfg.(key) = val;
        end
    end
end
