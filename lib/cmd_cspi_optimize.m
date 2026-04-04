function result = cmd_cspi_optimize(parsed)
    % cmd_cspi_optimize - find optimal heatsink geometry maximizing CSPI
    % Usage: thermal_cli.m cspi-optimize --lambda <W/mK> --a-chip <m2> --c <m> --p-fan <W> [options]
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m cspi-optimize --lambda <W/mK> --a-chip <m2> --c <m> --p-fan <W>\n');
        fprintf('                     [--t-min <m>] [--k1 <val>] [--k2 <val>] [--k3 <val>] [--t-air <C>]\n');
        fprintf('Finds optimal heatsink channel width maximizing CSPI (Drofenik & Kolar CIPS06).\n');
        fprintf('\nRequired:\n');
        fprintf('  --lambda  heatsink thermal conductivity [W/(m*K)]\n');
        fprintf('  --a-chip  total chip footprint area [m2]\n');
        fprintf('  --c       heatsink height = fan diameter [m]\n');
        fprintf('  --p-fan   maximum fan shaft power [W]\n');
        fprintf('\nOptional:\n');
        fprintf('  --t-min   minimum fin thickness [m]     (default 0)\n');
        fprintf('  --k1      fan scaling: V_MAX=k1*N*D^3   (default 6e-3)\n');
        fprintf('  --k2      fan scaling: dp_MAX=k2*N^2*D^2 (default 5e-4)\n');
        fprintf('  --k3      fan scaling: P_FAN=k3*N^3*D^5 (default 30e-6)\n');
        fprintf('  --t-air   reference air temperature [C] (default 80)\n');
        result = struct(); return;
    end

    lambda = str2double(parsed.lambda);
    a_chip = str2double(parsed.a_chip);
    c      = str2double(parsed.c);
    p_fan  = str2double(parsed.p_fan);

    args = {};
    if isfield(parsed, 't_min'), args = [args, {'t_min', str2double(parsed.t_min)}]; end
    if isfield(parsed, 'k1'),    args = [args, {'k1',    str2double(parsed.k1)}];    end
    if isfield(parsed, 'k2'),    args = [args, {'k2',    str2double(parsed.k2)}];    end
    if isfield(parsed, 'k3'),    args = [args, {'k3',    str2double(parsed.k3)}];    end
    if isfield(parsed, 't_air'), args = [args, {'t_air', str2double(parsed.t_air)}]; end

    r = cspi_optimize(lambda, a_chip, c, p_fan, args{:});

    fprintf('cspi=%.4f\n',     r.cspi);
    fprintf('rth=%.6f\n',      r.rth);
    fprintf('vol=%.4f\n',      r.vol);
    fprintf('n_fins=%d\n',     r.n);
    fprintf('s_channel=%.4e\n', r.s);
    fprintf('t_fin=%.4e\n',    r.t);
    fprintf('Re=%.1f\n',       r.Re);
    fprintf('N_fan=%.0f\n',    r.N_fan);
    fprintf('V_MAX=%.4e\n',    r.V_MAX);
    fprintf('dp_MAX=%.2f\n',   r.dp_MAX);
    fprintf('feasible=%d\n',   r.feasible);

    result = r;
end
