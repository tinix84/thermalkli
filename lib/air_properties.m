function fluid = air_properties(T_ref_C)
    if nargin == 0, T_ref_C = 80; end
    T0 = 273.15; T = T_ref_C + T0;
    fluid.density = 101325 / 287.058 / T;
    fluid.cinematic_viscosity = 18.27e-6 * (291.15 + 120) / (T + 120) * (T / 291.15)^(3/2) / fluid.density;
    fluid.prandtl_number = 0.71;
    fluid.thermal_conductivity = 7e-5 * T + 5.1e-3;
    fluid.heat_capacity = 1010;
    fluid.temperature = T_ref_C;
end
