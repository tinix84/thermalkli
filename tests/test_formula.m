function results = test_formula()
    results = {};

    % --- calc_rth_from_power_temp ---

    r.name = 'calc_rth: basic calculation';
    rth = calc_rth_from_power_temp(50, 300, 350);
    r.pass = assert_near(rth, 1.0, 1e-10, r.name);
    r.detail = sprintf('got %.6g, expected 1.0', rth);
    results{end+1} = r;

    r.name = 'calc_rth: high power';
    rth = calc_rth_from_power_temp(100, 298.15, 373.15);
    expected = (373.15 - 298.15) / 100;  % 0.75 K/W
    r.pass = assert_near(rth, expected, 1e-10, r.name);
    r.detail = sprintf('got %.6g, expected %.6g', rth, expected);
    results{end+1} = r;
end
