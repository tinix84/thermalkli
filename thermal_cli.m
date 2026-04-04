function thermal_cli()
    % thermal_cli - main entry point for the thermal toolbox CLI
    % Usage: octave thermal_cli.m <command> [options]

    root_dir = fileparts(mfilename('fullpath'));
    addpath(fullfile(root_dir, 'lib'));
    addpath(genpath(fullfile(root_dir, 'mfiles')));

    args = argv();
    if isempty(args) || strcmp(args{1}, '--help') || strcmp(args{1}, '-h')
        cli_print_help();
        return;
    end

    command = args{1};
    rest = args(2:end);
    parsed = cli_parse_args(rest);

    switch command
        case 'calc-rth'
            cmd_calc_rth(parsed);
        case 'fin-efficiency'
            cmd_fin_efficiency(parsed);
        case 'radiation'
            cmd_radiation(parsed);
        case 'layer-rth'
            cmd_layer_rth(parsed);
        case 'stack-rth'
            cmd_stack_rth(parsed);
        case 'semi-on-pcb'
            workflow_semi_on_pcb(parsed);
        case 'hydraulic-op'
            cmd_hydraulic_op(parsed);
        case 'fin-rth'
            cmd_fin_rth(parsed);
        case 'forced-conv-sim'
            workflow_forced_conv_sim(parsed);
        case 'extruded-fin'
            workflow_extruded_fin(parsed);
        case 'gen-femm'
            cmd_gen_femm(parsed);
        case 'compare-femm'
            cmd_compare_femm(parsed);
        case 'h-coeff'
            cmd_h_coeff(parsed);
        otherwise
            fprintf(2, 'Unknown command: %s\n', command);
            cli_print_help();
            exit(1);
    end
end
