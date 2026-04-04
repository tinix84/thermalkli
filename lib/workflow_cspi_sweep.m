function result = workflow_cspi_sweep(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m cspi-sweep --config <file>\n');
        fprintf('Config: a_chip, p_fan_max, lambda (array), c (array), t_min\n');
        result = struct(); return;
    end
    cfg = cli_load_config(parsed);
    fprintf('--- CSPI Parametric Sweep ---\n');
    fprintf('A_CHIP = %.1f cm2, P_FAN_MAX = %.1f W, t_min = %.1f mm\n', ...
        cfg.a_chip * 1e4, cfg.p_fan_max, cfg.t_min * 1e3);
    fprintf('\n');
    fprintf('%-12s', 'c [mm]');
    for j = 1:length(cfg.lambda)
        fprintf('  lambda=%-4d', cfg.lambda(j));
    end
    fprintf('\n');
    fprintf('%s\n', repmat('-', 1, 12 + 12 * length(cfg.lambda)));
    result.c = cfg.c; result.lambda = cfg.lambda;
    result.cspi = zeros(length(cfg.c), length(cfg.lambda));
    result.rth = zeros(length(cfg.c), length(cfg.lambda));
    for i = 1:length(cfg.c)
        fprintf('%-12.0f', cfg.c(i) * 1e3);
        for j = 1:length(cfg.lambda)
            args = {};
            if isfield(cfg, 't_min') && cfg.t_min > 0
                args = {'t_min', cfg.t_min};
            end
            r = cspi_optimize(cfg.lambda(j), cfg.a_chip, cfg.c(i), cfg.p_fan_max, args{:});
            result.cspi(i, j) = r.cspi;
            result.rth(i, j) = r.rth;
            if r.feasible
                fprintf('  %10.1f', r.cspi);
            else
                fprintf('  %10s', 'N/A');
            end
        end
        fprintf('\n');
    end
    fprintf('\n--- Complete ---\n');
    if isfield(parsed, 'save_csv')
        fid = fopen(parsed.save_csv, 'w');
        fprintf(fid, 'c_mm');
        for j = 1:length(cfg.lambda), fprintf(fid, ',cspi_lambda%d,rth_lambda%d', cfg.lambda(j), cfg.lambda(j)); end
        fprintf(fid, '\n');
        for i = 1:length(cfg.c)
            fprintf(fid, '%.1f', cfg.c(i) * 1e3);
            for j = 1:length(cfg.lambda), fprintf(fid, ',%.2f,%.6f', result.cspi(i,j), result.rth(i,j)); end
            fprintf(fid, '\n');
        end
        fclose(fid);
        fprintf('Results saved to: %s\n', parsed.save_csv);
    end
end
