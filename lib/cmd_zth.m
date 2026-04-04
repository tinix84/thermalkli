function result = cmd_zth(parsed)
    % cmd_zth - transient thermal impedance (Foster network)
    % Usage: thermal_cli.m zth --r "0.1 0.3 0.5" --tau "1e-3 0.01 0.1" --t-end 1
    % Or: thermal_cli.m zth --config <file>

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m zth --r "R1 R2 ..." --tau "tau1 tau2 ..." --t-end <s> [--n-points <int>]\n');
        fprintf('Computes Zth(t) = sum(Ri * (1 - exp(-t/taui))) using Foster network model.\n');
        fprintf('  --r         Thermal resistances [K/W] (space-separated in quotes)\n');
        fprintf('  --tau       Time constants [s] (space-separated in quotes)\n');
        fprintf('  --t-end     End time [s]\n');
        fprintf('  --n-points  Number of output points (default 200)\n');
        fprintf('  --duty      Duty cycle for pulsed Zth (0-1, optional)\n');
        fprintf('  --period    Pulse period [s] (required if --duty given)\n');
        result = struct();
        return;
    end

    if isfield(parsed, 'config')
        cfg = cli_load_config(parsed);
        R = cfg.R;
        tau = cfg.tau;
        t_end = cfg.t_end;
    else
        R = str2num(parsed.r);
        tau = str2num(parsed.tau);
        t_end = str2double(parsed.t_end);
    end

    if isfield(parsed, 'n_points')
        n_points = str2double(parsed.n_points);
    else
        n_points = 200;
    end

    [Zth, t] = zth_foster(R, tau, t_end, n_points);

    % Pulsed Zth (duty cycle correction)
    if isfield(parsed, 'duty') && isfield(parsed, 'period')
        D = str2double(parsed.duty);
        T = str2double(parsed.period);
        Zth = zth_pulsed(R, tau, t, D, T);
        fprintf('duty_cycle=%.2f\n', D);
        fprintf('period=%.4e\n', T);
    end

    fprintf('rth_total=%.6f\n', sum(R));
    fprintf('zth_at_end=%.6f\n', Zth(end));

    % Print a few key time points
    targets = [0.001 0.01 0.1 1];
    for i = 1:length(targets)
        if targets(i) <= t_end
            [~, idx] = min(abs(t - targets(i)));
            fprintf('zth_at_%.0ems=%.6f\n', targets(i)*1e3, Zth(idx));
        end
    end

    result.Zth = Zth;
    result.t = t;
    result.R = R;
    result.tau = tau;
    result.rth_total = sum(R);

    % CSV export
    if isfield(parsed, 'save_csv')
        fid = fopen(parsed.save_csv, 'w');
        fprintf(fid, 'time_s,Zth_KW\n');
        for i = 1:length(t)
            fprintf(fid, '%.6e,%.6e\n', t(i), Zth(i));
        end
        fclose(fid);
        fprintf('Zth curve saved to: %s\n', parsed.save_csv);
    end
end
