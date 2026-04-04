function [dp, Re] = channel_pressure_drop(geom, flow_rate, fluid)
    if isfield(geom, 'diameter')
        dh = geom.diameter; ff = 64;
        Ac = (geom.diameter / 2)^2 * pi; P = pi * geom.diameter;
    else
        dh = 4 * geom.width * geom.height / 2 / (geom.height + geom.width);
        ratio = max([geom.width geom.height]) / min([geom.width geom.height]);
        if ratio <= 14
            ff = interp1([1 1.43 2 3 4 8 14], [57 59 62 69 73 82 96], ratio, 'linear');
        else
            ff = 96;
        end
        Ac = geom.width * geom.height; P = 2 * (geom.width + geom.height);
    end
    v = flow_rate / Ac; Re = v * dh / fluid.cinematic_viscosity;
    if Re <= 2300
        dp = ff * fluid.density * fluid.cinematic_viscosity * geom.length * flow_rate / (2 * Ac * dh^2);
    else
        dp = geom.length * fluid.density * 0.5 * v^2 / (dh * (0.79 * log(4 * flow_rate / P / fluid.cinematic_viscosity) - 1.64)^2);
    end
end
