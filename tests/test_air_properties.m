function results = test_air_properties()
    results = {};

    r.name = 'rho_air: density at 20C';
    rho = rho_air(20);
    r.pass = assert_near(rho, 1.204, 0.02, r.name);
    r.detail = sprintf('got %.4f, expected ~1.204 kg/m3', rho);
    results{end+1} = r;

    r.name = 'rho_air: density at 50C';
    rho = rho_air(50);
    r.pass = assert_near(rho, 1.093, 0.03, r.name);
    r.detail = sprintf('got %.4f, expected ~1.093 kg/m3', rho);
    results{end+1} = r;

    r.name = 'rho_air: density at 100C';
    rho = rho_air(100);
    r.pass = assert_near(rho, 0.946, 0.03, r.name);
    r.detail = sprintf('got %.4f, expected ~0.946 kg/m3', rho);
    results{end+1} = r;

    r.name = 'Cp_air: specific heat at 20C';
    cp = Cp_air(20);
    r.pass = assert_near(cp, 1005, 10, r.name);
    r.detail = sprintf('got %.1f, expected ~1005 J/(kg*K)', cp);
    results{end+1} = r;

    r.name = 'Cp_air: specific heat at 50C';
    cp = Cp_air(50);
    r.pass = assert_near(cp, 1007, 10, r.name);
    r.detail = sprintf('got %.1f, expected ~1007 J/(kg*K)', cp);
    results{end+1} = r;

    r.name = 'mu_air: viscosity at 20C';
    mu = mu_air(20);
    r.pass = assert_near(mu, 1.825e-5, 2e-7, r.name);
    r.detail = sprintf('got %.4e, expected ~1.825e-5 Pa*s', mu);
    results{end+1} = r;

    r.name = 'mu_air: viscosity at 100C';
    mu = mu_air(100);
    r.pass = assert_near(mu, 2.18e-5, 3e-7, r.name);
    r.detail = sprintf('got %.4e, expected ~2.18e-5 Pa*s', mu);
    results{end+1} = r;

    r.name = 'Kt_air: conductivity at 20C';
    kt = Kt_air(20);
    r.pass = assert_near(kt, 0.0257, 0.002, r.name);
    r.detail = sprintf('got %.4f, expected ~0.0257 W/(m*K)', kt);
    results{end+1} = r;

    r.name = 'Kt_air: conductivity at 100C';
    kt = Kt_air(100);
    r.pass = assert_near(kt, 0.0308, 0.002, r.name);
    r.detail = sprintf('got %.4f, expected ~0.0308 W/(m*K)', kt);
    results{end+1} = r;
end
