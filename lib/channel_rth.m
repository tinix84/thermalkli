function [rth, Re, Nu, h] = channel_rth(geom, flow_rate, fluid)
    if isfield(geom, 'diameter')
        dh = geom.diameter;
        Ac = (geom.diameter / 2)^2 * pi;
        P = pi * geom.diameter;
    else
        dh = 4 * geom.width * geom.height / 2 / (geom.height + geom.width);
        Ac = geom.width * geom.height;
        P = 2 * (geom.width + geom.height);
    end
    v = flow_rate / Ac;
    Re = v * dh / fluid.cinematic_viscosity;
    if Re <= 2300
        x = geom.length / dh / Re / fluid.prandtl_number;
        Nu = (3.657 / tanh(2.264 * x^(1/3) + 1.7 * x^(2/3)) + 0.0499 * tanh(x) / x) / ...
             tanh(2.432 * fluid.prandtl_number^(1/6) * x^(1/6));
    else
        Nu = (Re - 1000) * fluid.prandtl_number * (1 + (dh / geom.length)^(2/3)) / ...
             (8 * (0.79 * log(Re) - 1.64)^2) / ...
             (1 + 12.7 * sqrt(1 / (8 * (0.79 * log(Re) - 1.64)^2)) * (fluid.prandtl_number^(2/3) - 1));
    end
    h = Nu * fluid.thermal_conductivity / dh;
    rth = 1 / (h * geom.length * P) + 0.5 / (fluid.density * fluid.heat_capacity * flow_rate);
end
