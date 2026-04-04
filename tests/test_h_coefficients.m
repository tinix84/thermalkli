function results = test_h_coefficients()
    results = {};

    r.name = 'h_forced: laminar flat plate 1m/s';
    [h, Re] = h_forced_convection(0.05, 1, 40, 80);
    r.pass = h > 5 && h < 50 && Re < 5e5;
    r.detail = sprintf('h=%.2f W/(m2K), Re=%.0f', h, Re);
    results{end+1} = r;

    r.name = 'h_forced: higher velocity increases h';
    [h1, ~] = h_forced_convection(0.05, 1, 40, 80);
    [h2, ~] = h_forced_convection(0.05, 5, 40, 80);
    r.pass = h2 > h1;
    r.detail = sprintf('h(1)=%.2f, h(5)=%.2f', h1, h2);
    results{end+1} = r;

    r.name = 'h_natural: vertical plate';
    [h, Ra] = h_natural_convection('vertical', 0.05, 40, 80);
    r.pass = h > 3 && h < 30 && Ra > 0;
    r.detail = sprintf('h=%.2f, Ra=%.2e', h, Ra);
    results{end+1} = r;

    r.name = 'h_natural: horizontal_top > horizontal_bottom';
    [h_top, ~] = h_natural_convection('horizontal_top', 0.05, 40, 80);
    [h_bot, ~] = h_natural_convection('horizontal_bottom', 0.05, 40, 80);
    r.pass = h_top > h_bot;
    r.detail = sprintf('top=%.2f, bot=%.2f', h_top, h_bot);
    results{end+1} = r;

    r.name = 'h_radiation: typical value at 80C';
    h = h_radiation(0.9, 40, 80);
    r.pass = assert_near(h, 6.5, 1.5, r.name);
    r.detail = sprintf('h=%.2f', h);
    results{end+1} = r;

    r.name = 'h_radiation: blackbody at 100C';
    h = h_radiation(1.0, 25, 100);
    r.pass = h > 6 && h < 12;
    r.detail = sprintf('h=%.2f', h);
    results{end+1} = r;
end
