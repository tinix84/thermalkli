function results = test_channel_model()
    results = {};
    fluid = air_properties(80);

    r.name = 'channel_rth: laminar Re<2300';
    geom.width = 1e-3; geom.height = 40e-3; geom.length = 80e-3;
    [rth, Re, ~, ~] = channel_rth(geom, 1e-4, fluid);
    r.pass = Re < 2300 && rth > 0;
    r.detail = sprintf('rth=%.4f, Re=%.1f', rth, Re);
    results{end+1} = r;

    r.name = 'channel_rth: more flow -> lower Rth';
    [rth1, ~, ~, ~] = channel_rth(geom, 1e-4, fluid);
    [rth2, ~, ~, ~] = channel_rth(geom, 5e-4, fluid);
    r.pass = rth2 < rth1;
    r.detail = sprintf('rth(1e-4)=%.4f, rth(5e-4)=%.4f', rth1, rth2);
    results{end+1} = r;

    r.name = 'channel_dp: laminar positive';
    [dp, Re] = channel_pressure_drop(geom, 1e-4, fluid);
    r.pass = dp > 0 && Re < 2300;
    r.detail = sprintf('dp=%.2f Pa, Re=%.1f', dp, Re);
    results{end+1} = r;

    r.name = 'channel_dp: more flow -> more dp';
    [dp1, ~] = channel_pressure_drop(geom, 1e-4, fluid);
    [dp2, ~] = channel_pressure_drop(geom, 5e-4, fluid);
    r.pass = dp2 > dp1;
    r.detail = sprintf('dp(1e-4)=%.2f, dp(5e-4)=%.2f', dp1, dp2);
    results{end+1} = r;

    r.name = 'channel_dp: square channel';
    geom_sq.width = 5e-3; geom_sq.height = 5e-3; geom_sq.length = 80e-3;
    [dp_sq, Re_sq] = channel_pressure_drop(geom_sq, 1e-4, fluid);
    r.pass = dp_sq > 0 && Re_sq > 0;
    r.detail = sprintf('dp=%.4f, Re=%.1f', dp_sq, Re_sq);
    results{end+1} = r;

    r.name = 'air_properties: valid at 80C';
    f = air_properties(80);
    r.pass = f.density > 0.9 && f.density < 1.1 && f.prandtl_number == 0.71;
    r.detail = sprintf('rho=%.3f, nu=%.2e', f.density, f.cinematic_viscosity);
    results{end+1} = r;
end
