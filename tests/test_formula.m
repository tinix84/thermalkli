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

    % --- finEfficieny: literature values ---
    % Reference: Incropera 7th ed, analytical: eta = tanh(mL)/mL
    % Setup: L=1, A=1, Ac=1, k=1 -> mL = sqrt(h)

    r.name = 'fin_efficiency: mL=0.5 (Incropera)';
    eta = finEfficieny(1, 0.25, 1, 1, 1);  % mL = sqrt(0.25) = 0.5
    expected = tanh(0.5) / 0.5;  % 0.92424
    r.pass = assert_near(eta, expected, 0.001, r.name);
    r.detail = sprintf('got %.6f, expected %.6f', eta, expected);
    results{end+1} = r;

    r.name = 'fin_efficiency: mL=1.0 (Incropera)';
    eta = finEfficieny(1, 1, 1, 1, 1);  % mL = sqrt(1) = 1.0
    expected = tanh(1.0) / 1.0;  % 0.76159
    r.pass = assert_near(eta, expected, 0.001, r.name);
    r.detail = sprintf('got %.6f, expected %.6f', eta, expected);
    results{end+1} = r;

    r.name = 'fin_efficiency: mL=2.0 (Incropera)';
    eta = finEfficieny(1, 4, 1, 1, 1);  % mL = sqrt(4) = 2.0
    expected = tanh(2.0) / 2.0;  % 0.48201
    r.pass = assert_near(eta, expected, 0.001, r.name);
    r.detail = sprintf('got %.6f, expected %.6f', eta, expected);
    results{end+1} = r;

    % Realistic case: aluminum fin, L=20mm, t=1mm, h=50 W/m2K, k=200 W/mK
    r.name = 'fin_efficiency: realistic aluminum fin';
    L = 0.02; t = 0.001; h = 50; k = 200;
    W = 1;  % per unit width
    A = 2 * L * W;   % both sides of fin
    Ac = t * W;       % cross section
    eta = finEfficieny(L, h, A, k, Ac);
    mL = sqrt(h * A / (k * Ac * L)) * L;
    expected = tanh(mL) / mL;
    r.pass = assert_near(eta, expected, 0.001, r.name);
    r.detail = sprintf('got %.6f, expected %.6f (mL=%.4f)', eta, expected, mL);
    results{end+1} = r;
end
