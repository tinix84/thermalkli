function [h, Ra] = h_natural_convection(orientation, L, T_ambient, T_surface)
    T0 = 273.15;
    rho = @(T)(101325 / 287.058 / T);
    beta = @(T)(1 / T);
    mu = @(T)(18.27e-6 * (291.15 + 120) / (T + 120) * (T / 291.15)^(3/2));
    Pr = 0.71;
    kf = @(T)(7e-5 * T + 5.1e-3);
    Ta = T_ambient + T0; Ts = T_surface + T0; Tf = (Ta + Ts) / 2;
    Ra = Pr * rho(Tf)^2 * 9.81 * beta(Tf) * (Ts - Ta) * L^3 / mu(Tf)^2;
    switch orientation
        case 'vertical'
            if Ra < 1e9, h = 0.59 * Ra^(1/4) * kf(Tf) / L;
            else, h = 0.1 * Ra^(1/3) * kf(Tf) / L; end
        case 'horizontal_top'
            if Ra < 1e7, h = 0.54 * Ra^(1/4) * kf(Tf) / L;
            else, h = 0.15 * Ra^(1/3) * kf(Tf) / L; end
        case 'horizontal_bottom'
            h = 0.27 * Ra^(1/4) * kf(Tf) / L;
        otherwise, error('Unknown orientation: %s', orientation);
    end
end
