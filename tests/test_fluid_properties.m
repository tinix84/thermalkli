function results = test_fluid_properties()
    results = {};
    pkg load io;

    r.name = 'GasProperty: airDry loads';
    try
        gas = GasProperty('airDry');
        r.pass = ~isempty(gas.fluidData);
        r.detail = 'GasProperty created successfully';
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    r.name = 'GasProperty: airDry density at 300K';
    try
        rho = gas.calcDensity(300, 101325);
        r.pass = assert_near(rho, 1.177, 0.05, r.name);
        r.detail = sprintf('got %.4f, expected ~1.177 kg/m3', rho);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    r.name = 'LiquidProperty: H2OGly50 loads';
    try
        liq = LiquidProperty('H2OGly50');
        r.pass = ~isempty(liq.fluidData);
        r.detail = 'LiquidProperty created successfully';
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    r.name = 'LiquidProperty: H2OGly50 density at 320K';
    try
        rho = liq.calcDensity(320);
        r.pass = rho > 900 && rho < 1200;
        r.detail = sprintf('got %.1f kg/m3', rho);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;
end
