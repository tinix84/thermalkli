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
        case 'channel-rth'
            cmd_channel_rth(parsed);
        case 'channel-dp'
            cmd_channel_dp(parsed);
        case 'cspi'
            cmd_cspi(parsed);
        case 'cspi-optimize'
            cmd_cspi_optimize(parsed);
        case 'fan-fit'
            cmd_fan_fit(parsed);
        case 'water-cooling'
            cmd_water_cooling(parsed);
        case 'cspi-sweep'
            workflow_cspi_sweep(parsed);
        case 'multi-sim'
            workflow_multi_sim(parsed);
        case 'optimize-fin'
            workflow_optimize_fin(parsed);
        case 'heatsink-create'
            cmd_heatsink_create(parsed);
        case 'heatsink-rth'
            cmd_heatsink_rth(parsed);
        case 'free-conv'
            cmd_free_conv(parsed);
        case 'zth'
            cmd_zth(parsed);
        case 'tim-lookup'
            cmd_tim_lookup(parsed);
        otherwise
            fprintf(2, 'Unknown command: %s\n', command);
            cli_print_help();
            exit(1);
    end
end
