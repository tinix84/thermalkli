function [h, Re] = h_forced_convection(L, U, T_ambient, T_surface)
    T0 = 273.15;
    rho = @(T)(101325 / 287.058 / T);
    mu = @(T)(18.27e-6 * (291.15 + 120) / (T + 120) * (T / 291.15)^(3/2));
    Pr = 0.71;
    kf = @(T)(7e-5 * T + 5.1e-3);
    Ta = T_ambient + T0; Ts = T_surface + T0; Tf = (Ta + Ts) / 2;
    Re = rho(Tf) * U * L / mu(Tf);
    if Re < 5e5
        h = 0.664 * Re^(1/2) * Pr^(1/3) * kf(Tf) / L;
    else
        h = (0.037 * Re^(4/5) - 18030) * Pr^(1/3) * kf(Tf) / L;
    end
end
