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

    % --- Radiation: literature values ---
    % Reference: Incropera 7th ed Ch.13, using Stefan-Boltzmann sigma = 5.670367e-8

    sigma = 5.670367e-8;

    % Parallel planes: two blackbodies (eps=1)
    r.name = 'radiation_parallel: blackbody 500K-300K';
    q = heatTransferParallelPlanesRadiation(500, 300, 1.0, 1.0, 1.0);
    expected = sigma * 1.0 * (500^4 - 300^4);
    r.pass = assert_near(q, expected, 0.01, r.name);
    r.detail = sprintf('got %.2f W, expected %.2f W', q, expected);
    results{end+1} = r;

    % Parallel planes: gray surfaces
    r.name = 'radiation_parallel: gray eps=0.5 500K-300K';
    q = heatTransferParallelPlanesRadiation(500, 300, 1.0, 0.5, 0.5);
    expected = sigma * 1.0 * (500^4 - 300^4) / (1/0.5 + 1/0.5 - 1);
    r.pass = assert_near(q, expected, 0.01, r.name);
    r.detail = sprintf('got %.2f W, expected %.2f W', q, expected);
    results{end+1} = r;

    % Concentric cylinders: blackbody
    r.name = 'radiation_cylinder: blackbody r1=0.05 r2=0.10 L=1';
    q = heatTransferConcentricCylinderRadiation(500, 300, 0.05, 0.10, 1.0, 1.0, 1.0);
    A1 = 2 * pi * 0.05 * 1.0;
    expected = sigma * A1 * (500^4 - 300^4) / (1/1.0 + (1-1.0)/1.0*(0.05/0.10));
    r.pass = assert_near(q, expected, 0.01, r.name);
    r.detail = sprintf('got %.2f W, expected %.2f W', q, expected);
    results{end+1} = r;

    % Concentric spheres: blackbody
    r.name = 'radiation_sphere: blackbody r1=0.05 r2=0.10';
    q = heatTransferConcentricSphereRadiation(500, 300, 0.05, 0.10, 1.0, 1.0);
    A1 = 4 * pi * 0.05^2;
    expected = sigma * A1 * (500^4 - 300^4) / (1/1.0 + (1-1.0)/1.0*(0.05/0.10)^2);
    r.pass = assert_near(q, expected, 0.01, r.name);
    r.detail = sprintf('got %.2f W, expected %.2f W', q, expected);
    results{end+1} = r;

    % Enclosure: two parallel surfaces forming enclosure, F12=1
    r.name = 'radiation_enclosure: F12=1 A1=A2=1 eps=0.8';
    q = heatTransferEnclosureRadiation(500, 300, 0.8, 0.8, 1.0, 1.0, 1.0);
    expected = sigma * (500^4 - 300^4) / ((1-0.8)/(0.8*1) + 1/(1*1) + (1-0.8)/(0.8*1));
    r.pass = assert_near(q, expected, 0.01, r.name);
    r.detail = sprintf('got %.2f W, expected %.2f W', q, expected);
    results{end+1} = r;

    % Small convex body in large cavity
    r.name = 'radiation_convex: small body eps=0.9 A=0.01';
    q = heatTransferSmallConvexRadiation(500, 300, 0.01, 0.9);
    expected = sigma * 0.01 * 0.9 * (500^4 - 300^4);
    r.pass = assert_near(q, expected, 0.01, r.name);
    r.detail = sprintf('got %.4f W, expected %.4f W', q, expected);
    results{end+1} = r;
end
