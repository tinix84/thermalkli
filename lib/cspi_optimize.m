function result = cspi_optimize(lambda_HS, A_CHIP, c, P_FAN_MAX, varargin)
    % cspi_optimize - find optimal heatsink channel width maximizing CSPI
    % Drofenik & Kolar, CIPS06
    %   lambda_HS: heatsink thermal conductivity [W/(m*K)]
    %   A_CHIP:    total chip footprint area [m2]
    %   c:         heatsink height (= fan diameter D) [m]
    %   P_FAN_MAX: maximum fan shaft power [W]
    %   Optional name-value pairs:
    %     't_min'  minimum fin thickness [m]   (default 0)
    %     'k1'     fan scaling: V_MAX = k1*N*D^3  (default 6e-3)
    %     'k2'     fan scaling: dp_MAX = k2*N^2*D^2 (default 5e-4)
    %     'k3'     fan scaling: P_FAN = k3*N^3*D^5  (default 30e-6)
    %     't_air'  reference air temperature [C]   (default 80)

    % --- defaults ---
    t_min  = 0;
    k1     = 6e-3;
    k2     = 5e-4;
    k3     = 30e-6;
    t_air  = 80;

    for i = 1:2:length(varargin)
        switch varargin{i}
            case 't_min', t_min = varargin{i+1};
            case 'k1',    k1    = varargin{i+1};
            case 'k2',    k2    = varargin{i+1};
            case 'k3',    k3    = varargin{i+1};
            case 't_air', t_air = varargin{i+1};
        end
    end

    % Heatsink is square cross-section b=c, length L along flow
    L = A_CHIP / c;

    % Fan operating point at max power: P = k3*N^3*D^5 => N [rev/s]
    N      = (P_FAN_MAX / (k3 * c^5))^(1/3);
    V_MAX  = k1 * N * c^3;    % max volumetric flow at zero pressure [m3/s]
    dp_MAX = k2 * N^2 * c^2;  % max static pressure at zero flow [Pa]

    % Air fluid properties
    fluid = air_properties(t_air);

    % --- sweep channel width s ---
    % Lower bound: laminar-flow onset (Re~2300)
    % Upper bound: channel pitch = heatsink height (single channel)
    s_min = max(t_min * 0.5, 0.2e-3);   % at least 0.2 mm channel
    s_max = c * 0.5;                      % at most half the height

    n_pts = 80;
    s_arr = linspace(s_min, s_max, n_pts);
    cspi_arr = zeros(1, n_pts);

    for idx = 1:n_pts
        s_try = s_arr(idx);

        % Number of channels that fit in width c
        % Channel pitch = s + t; estimate n and t together:
        %   n = floor(c / (s + t))
        % Start with t = t_min
        if t_min > 0
            n_try = floor(c / (s_try + t_min));
        else
            % Without min-thickness assume thin fins: t ~ s (aspect guess)
            n_try = floor(c / (2 * s_try));
        end

        if n_try < 2
            cspi_arr(idx) = 0;
            continue;
        end

        % Fin thickness from pitch
        t_try = c / n_try - s_try;
        if t_try < t_min || t_try <= 0
            cspi_arr(idx) = 0;
            continue;
        end

        % Flow per channel (fan operates at partial flow/pressure point)
        % Approximate: use half of V_MAX split equally (fan at mid-point)
        V_total = V_MAX * 0.5;       % operating point on fan curve
        V_ch    = V_total / n_try;

        if V_ch <= 0
            cspi_arr(idx) = 0;
            continue;
        end

        % Channel geometry (rectangular: width=s, height=c)
        geom.width  = s_try;
        geom.height = c;
        geom.length = L;

        % Channel thermal resistance (convection + outlet temperature rise)
        try
            [rth_ch, Re_ch, ~, ~] = channel_rth(geom, V_ch, fluid);
        catch
            cspi_arr(idx) = 0;
            continue;
        end

        if rth_ch <= 0 || ~isfinite(rth_ch)
            cspi_arr(idx) = 0;
            continue;
        end

        % Conductive resistance through half-fin to base
        rth_fin = (t_try / 2) / (lambda_HS * c * L);

        % Total heatsink Rth: n channels in parallel with fin conduction in series
        % Rth_total = (rth_fin + rth_ch) / n_try
        % (the outlet temp-rise term is already included in channel_rth's 0.5/(rho*cp*V))
        rth_total = (rth_fin + rth_ch) / n_try;

        if rth_total <= 0 || ~isfinite(rth_total)
            cspi_arr(idx) = 0;
            continue;
        end

        vol_cs = L * c * c * 1000;   % liters

        cspi_arr(idx) = cspi_calc(rth_total, vol_cs);
    end

    % Find optimal channel width
    [~, best_idx] = max(cspi_arr);
    s_opt = s_arr(best_idx);

    % --- Recompute final geometry at optimum ---
    if t_min > 0
        n_fin = floor(c / (s_opt + t_min));
    else
        n_fin = floor(c / (2 * s_opt));
    end
    if n_fin < 2, n_fin = 2; end

    t_fin = c / n_fin - s_opt;
    if t_fin < t_min
        t_fin = t_min;
        n_fin = floor(c / (s_opt + t_fin));
        if n_fin < 2, n_fin = 2; end
        t_fin = c / n_fin - s_opt;
    end
    if t_fin <= 0
        t_fin = 0.1e-3;
    end

    V_total = V_MAX * 0.5;
    V_ch    = V_total / n_fin;

    geom.width  = s_opt;
    geom.height = c;
    geom.length = L;

    [rth_ch, Re_fin, ~, ~] = channel_rth(geom, V_ch, fluid);
    rth_fin_cond = (t_fin / 2) / (lambda_HS * c * L);
    rth = (rth_fin_cond + rth_ch) / n_fin;

    vol_cs = L * c * c * 1000;   % liters

    result.cspi    = cspi_calc(rth, vol_cs);
    result.rth     = rth;
    result.vol     = vol_cs;
    result.n       = n_fin;
    result.s       = s_opt;
    result.t       = t_fin;
    result.Re      = Re_fin;
    result.N_fan   = N;
    result.L       = L;
    result.V_MAX   = V_MAX;
    result.dp_MAX  = dp_MAX;
    result.feasible = Re_fin < 2300 && t_fin > 0 && rth > 0 && isfinite(rth);
end
