function h = h_radiation(epsilon, T_ambient, T_surface)
    T0 = 273.15; Ta = T_ambient + T0; Ts = T_surface + T0;
    h = epsilon * 5.67e-8 * (Ts^2 + Ta^2) * (Ts + Ta);
end
