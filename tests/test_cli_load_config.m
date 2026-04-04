function results = test_cli_load_config()
    results = {};

    % Test 1: load config from file
    r.name = 'cli_load_config: load from file';
    parsed = struct('config', fullfile(fileparts(mfilename('fullpath')), 'fixtures', 'test_config.m'));
    cfg = cli_load_config(parsed);
    r.pass = strcmp(cfg.heatsink.type, 'extruded') && cfg.fluid.flowrate == 0.005;
    r.detail = sprintf('heatsink.type=%s, fluid.flowrate=%g', cfg.heatsink.type, cfg.fluid.flowrate);
    results{end+1} = r;

    % Test 2: override nested field
    r.name = 'cli_load_config: override nested field';
    parsed = struct('config', fullfile(fileparts(mfilename('fullpath')), 'fixtures', 'test_config.m'), ...
                    'fluid_flowrate', '0.01');
    cfg = cli_load_config(parsed);
    r.pass = cfg.fluid.flowrate == 0.01;
    r.detail = sprintf('fluid.flowrate=%g, expected 0.01', cfg.fluid.flowrate);
    results{end+1} = r;

    % Test 3: no config file, just args
    r.name = 'cli_load_config: no config file';
    parsed = struct('power', '50');
    cfg = cli_load_config(parsed);
    r.pass = isstruct(cfg) && strcmp(cfg.power, '50');
    r.detail = 'should return struct with flat args';
    results{end+1} = r;
end
