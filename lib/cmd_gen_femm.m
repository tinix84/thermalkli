function result = cmd_gen_femm(parsed)
    % cmd_gen_femm - generate a FEMM Lua script from a config file
    % Usage: thermal_cli.m gen-femm --model <type> --config <file> [--output <lua_file>]
    % Models: semi-on-pcb, extruded-fin, baseplate

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m gen-femm --model <type> --config <file> [--output <lua_file>]\n');
        fprintf('If --output is omitted, prints Lua script to stdout.\n');
        fprintf('Models: semi-on-pcb, extruded-fin, baseplate\n');
        result = struct();
        return;
    end

    if ~isfield(parsed, 'model')
        fprintf(2, 'Error: --model is required (semi-on-pcb|extruded-fin|baseplate)\n');
        result = struct();
        return;
    end

    cfg = cli_load_config(parsed);

    switch parsed.model
        case 'semi-on-pcb'
            lua_str = femm_semi_on_pcb(cfg);
        case 'extruded-fin'
            lua_str = femm_extruded_fin(cfg);
        case 'baseplate'
            lua_str = femm_baseplate_spreading(cfg);
        otherwise
            fprintf(2, 'Error: unknown model "%s"\n', parsed.model);
            result = struct();
            return;
    end

    if isfield(parsed, 'output')
        fid = fopen(parsed.output, 'w');
        fprintf(fid, '%s', lua_str);
        fclose(fid);
        fprintf('FEMM Lua script written to: %s\n', parsed.output);
    else
        fprintf('%s\n', lua_str);
    end

    result.lua = lua_str;
    result.model = parsed.model;
end
