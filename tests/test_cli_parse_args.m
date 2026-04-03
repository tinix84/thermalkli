function results = test_cli_parse_args()
    results = {};

    % Test 1: key-value pairs
    r.name = 'cli_parse_args: key-value pairs';
    parsed = cli_parse_args({'--power', '50', '--tref', '300'});
    r.pass = strcmp(parsed.power, '50') && strcmp(parsed.tref, '300');
    r.detail = 'should parse --power 50 --tref 300';
    results{end+1} = r;

    % Test 2: dotted keys become underscores
    r.name = 'cli_parse_args: dotted keys';
    parsed = cli_parse_args({'--fluid.flowrate', '0.01'});
    r.pass = isfield(parsed, 'fluid_flowrate') && strcmp(parsed.fluid_flowrate, '0.01');
    r.detail = 'should convert --fluid.flowrate to fluid_flowrate';
    results{end+1} = r;

    % Test 3: flag without value
    r.name = 'cli_parse_args: boolean flag';
    parsed = cli_parse_args({'--help'});
    r.pass = isfield(parsed, 'help') && parsed.help == true;
    r.detail = 'should set help=true';
    results{end+1} = r;

    % Test 4: flag followed by another flag
    r.name = 'cli_parse_args: two flags';
    parsed = cli_parse_args({'--verbose', '--help'});
    r.pass = parsed.verbose == true && parsed.help == true;
    r.detail = 'should set both flags to true';
    results{end+1} = r;

    % Test 5: mixed flags and key-value
    r.name = 'cli_parse_args: mixed';
    parsed = cli_parse_args({'--verbose', '--power', '50', '--help'});
    r.pass = parsed.verbose == true && strcmp(parsed.power, '50') && parsed.help == true;
    r.detail = 'should handle mixed flags and values';
    results{end+1} = r;

    % Test 6: empty args
    r.name = 'cli_parse_args: empty';
    parsed = cli_parse_args({});
    r.pass = isstruct(parsed) && isempty(fieldnames(parsed));
    r.detail = 'should return empty struct';
    results{end+1} = r;
end
