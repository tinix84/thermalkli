function result = cmd_water_cooling(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m water-cooling --p-loss <W> --flow <l/min> --t-in <C> --rth-jc <K/W> --n-devices <int>\n');
        fprintf('  --p-loss      Total power loss [W]\n');
        fprintf('  --flow        Coolant flow rate [l/min]\n');
        fprintf('  --t-in        Coolant inlet temperature [C]\n');
        fprintf('  --rth-jc      Junction-to-case Rth per device [K/W]\n');
        fprintf('  --n-devices   Number of devices\n');
        fprintf('  --cp          Coolant specific heat [J/(kg*K)] (default 3483)\n');
        fprintf('  --rho         Coolant density [kg/m3] (default 1064)\n');
        fprintf('  --rth-cl      Case-to-liquid Rth per device [K/W] (default 0)\n');
        result = struct(); return;
    end
    P_loss = str2double(parsed.p_loss);
    q_lmin = str2double(parsed.flow);
    T_in = str2double(parsed.t_in);
    Rjc = str2double(parsed.rth_jc);
    n_dev = str2double(parsed.n_devices);
    if isfield(parsed, 'cp'), cp = str2double(parsed.cp); else, cp = 3483; end
    if isfield(parsed, 'rho'), rho = str2double(parsed.rho); else, rho = 1064; end
    if isfield(parsed, 'rth_cl'), Rcl = str2double(parsed.rth_cl); else, Rcl = 0; end

    q_m3s = q_lmin / 1000 / 60;
    m_dot = rho * q_m3s;
    dT = P_loss / (cp * m_dot);
    T_out = T_in + dT;
    P_dev = P_loss / n_dev;
    T_j = T_out + P_dev * (Rjc + Rcl);

    result.dT_coolant = dT; result.T_out = T_out; result.T_junction = T_j;
    result.m_dot = m_dot; result.P_per_device = P_dev;
    fprintf('dt_coolant=%.2f\n', dT);
    fprintf('t_out=%.2f\n', T_out);
    fprintf('t_junction=%.2f\n', T_j);
    fprintf('mass_flow=%.4f\n', m_dot);
    fprintf('p_per_device=%.2f\n', P_dev);
end
