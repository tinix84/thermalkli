function results = test_zth()
    results = {};

    % Test 1: single RC element
    r.name = 'zth_foster: single RC Zth(inf) = R';
    [Zth, t] = zth_foster(1.0, 0.01, 1.0, 100);
    r.pass = assert_near(Zth(end), 1.0, 0.01, r.name);
    r.detail = sprintf('Zth(1s)=%.4f, expected 1.0', Zth(end));
    results{end+1} = r;

    % Test 2: Zth at t=0 is approximately 0
    r.name = 'zth_foster: Zth near t=0 is small';
    r.pass = Zth(1) < 0.1;
    r.detail = sprintf('Zth(%.2ems)=%.4f', t(1)*1e3, Zth(1));
    results{end+1} = r;

    % Test 3: Zth is monotonically increasing
    r.name = 'zth_foster: monotonically increasing';
    r.pass = all(diff(Zth) >= 0);
    r.detail = 'all dZth >= 0';
    results{end+1} = r;

    % Test 4: multi-RC Foster network
    r.name = 'zth_foster: 3-element Foster Rth=sum(R)';
    R = [0.1 0.3 0.5];
    tau = [1e-3 0.01 0.1];
    [Zth3, ~] = zth_foster(R, tau, 10, 200);
    r.pass = assert_near(Zth3(end), sum(R), 0.01, r.name);
    r.detail = sprintf('Zth(10s)=%.4f, Rth=%.1f', Zth3(end), sum(R));
    results{end+1} = r;

    % Test 5: pulsed Zth < steady-state Zth
    r.name = 'zth_pulsed: pulsed < steady for D<1';
    R = [0.5]; tau = [0.01];
    [Zth_ss, t] = zth_foster(R, tau, 1.0, 50);
    Zth_p = zth_pulsed(R, tau, t, 0.5, 0.1);
    r.pass = Zth_p(end) < Zth_ss(end);
    r.detail = sprintf('pulsed=%.4f, steady=%.4f', Zth_p(end), Zth_ss(end));
    results{end+1} = r;
end
