function results = test_literature()
    % test_literature - tests verified against published literature values
    % Each test cites a specific reference for the expected value.
    results = {};

    sigma = 5.670374419e-8;  % Stefan-Boltzmann constant [W/(m2*K4)]

    % =====================================================================
    % CONDUCTION
    % Ref: Incropera 7th ed, "Fundamentals of Heat and Mass Transfer"
    % =====================================================================

    % Incropera Table A.1: thermal conductivity of aluminum at 300K = 237 W/(m*K)
    % R = L/(k*A) for 1mm plate, 1cm2 area
    r.name = 'lit: conduction Rth = L/(k*A) [Incropera eq.3.6]';
    layer = ThermalLayer(0.001, 237);
    rth = layer.thermalLayerResistance(1e-4);
    expected = 0.001 / (237 * 1e-4);  % = 0.04219 K/W
    r.pass = assert_near(rth, expected, 1e-6, r.name);
    r.detail = sprintf('R=%.5f, expected %.5f', rth, expected);
    results{end+1} = r;

    % =====================================================================
    % FIN EFFICIENCY
    % Ref: Incropera 7th ed, Table 3.5
    % eta = tanh(mL)/(mL), exact analytical
    % =====================================================================

    % Case: mL = 1 (exact: tanh(1)/1 = 0.7616)
    r.name = 'lit: fin efficiency mL=1.0 [Incropera Table 3.5]';
    eta = finEfficieny(1, 1, 1, 1, 1);  % L=1,h=1,A=1,k=1,Ac=1 -> mL=sqrt(1)=1
    expected = tanh(1.0) / 1.0;  % 0.76159
    r.pass = assert_near(eta, expected, 1e-4, r.name);
    r.detail = sprintf('eta=%.5f, expected %.5f', eta, expected);
    results{end+1} = r;

    % Case: mL = 3 (efficiency drops to ~0.33)
    r.name = 'lit: fin efficiency mL=3.0 [Incropera Table 3.5]';
    eta = finEfficieny(1, 9, 1, 1, 1);  % mL=sqrt(9)=3
    expected = tanh(3.0) / 3.0;  % 0.33165
    r.pass = assert_near(eta, expected, 1e-4, r.name);
    r.detail = sprintf('eta=%.5f, expected %.5f', eta, expected);
    results{end+1} = r;

    % =====================================================================
    % RADIATION
    % Ref: Incropera 7th ed, Ch.13
    % =====================================================================

    % Stefan-Boltzmann: blackbody q = sigma*(T1^4 - T2^4)*A
    r.name = 'lit: blackbody radiation 1000K-300K [Stefan-Boltzmann law]';
    q = heatTransferParallelPlanesRadiation(1000, 300, 1.0, 1.0, 1.0);
    expected = sigma * (1000^4 - 300^4) * 1.0;  % = 56.24 kW
    r.pass = assert_near(q, expected, 1, r.name);
    r.detail = sprintf('q=%.1f W, expected %.1f W', q, expected);
    results{end+1} = r;

    % Gray body: q = sigma*(T1^4-T2^4)*A / (1/eps1 + 1/eps2 - 1)
    % Incropera eq.13.24 for parallel plates
    r.name = 'lit: gray parallel plates eps=0.3 [Incropera eq.13.24]';
    q = heatTransferParallelPlanesRadiation(500, 300, 1.0, 0.3, 0.3);
    expected = sigma * (500^4 - 300^4) / (1/0.3 + 1/0.3 - 1);  % 1/(3.33+3.33-1)=1/5.67
    r.pass = assert_near(q, expected, 0.1, r.name);
    r.detail = sprintf('q=%.2f W, expected %.2f W', q, expected);
    results{end+1} = r;

    % =====================================================================
    % NUSSELT NUMBER — LAMINAR CHANNEL
    % Ref: Baehr & Stephan, "Warme- und Stoffubertragung"
    % Ref: Wikipedia "Nusselt number" — fully developed laminar in circular tube
    % Nu_D = 3.66 (const T BC), Nu_D = 4.36 (const heat flux BC)
    % =====================================================================

    % For a very long channel (L/dh*Re*Pr >> 1), Nu should approach 3.66
    r.name = 'lit: channel Nu -> 3.66 for long laminar tube [Baehr & Stephan]';
    fluid = air_properties(80);
    geom.width = 5e-3; geom.height = 5e-3; geom.length = 10;  % very long
    [~, Re, Nu, ~] = channel_rth(geom, 1e-5, fluid);  % very low flow -> laminar
    r.pass = Re < 2300 && assert_near(Nu, 3.66, 0.5, r.name);
    r.detail = sprintf('Nu=%.2f (expected ~3.66 for fully developed), Re=%.1f', Nu, Re);
    results{end+1} = r;

    % =====================================================================
    % NUSSELT — GNIELINSKI TURBULENT
    % Ref: Gnielinski (1976), VDI Heat Atlas
    % Nu = (f/8)(Re-1000)Pr / [1 + 12.7*sqrt(f/8)*(Pr^(2/3)-1)]
    % At Re=10000, Pr=0.71: Nu ~ 30 (Incropera Table 8.4 vicinity)
    % =====================================================================

    r.name = 'lit: Gnielinski Nu at Re=10000 Pr=0.71 [VDI Heat Atlas]';
    f = 1 / (8 * (0.79 * log(10000) - 1.64)^2);
    Nu_expected = (10000 - 1000) * 0.71 / (8 * (0.79 * log(10000) - 1.64)^2) / ...
                  (1 + 12.7 * sqrt(f) * (0.71^(2/3) - 1));
    % Our channel model should match at high Re
    geom2.width = 10e-3; geom2.height = 10e-3; geom2.length = 0.5;
    % Find flow rate that gives Re~10000
    dh = 4 * 0.01 * 0.01 / (2 * (0.01 + 0.01));  % = 0.01m
    Ac = 0.01 * 0.01;
    v_target = 10000 * fluid.cinematic_viscosity / dh;
    fr_target = v_target * Ac;
    [~, Re2, Nu2, ~] = channel_rth(geom2, fr_target, fluid);
    r.pass = Re2 > 2300 && abs(Nu2 - Nu_expected) / Nu_expected < 0.15;
    r.detail = sprintf('Nu=%.1f (expected %.1f), Re=%.0f', Nu2, Nu_expected, Re2);
    results{end+1} = r;

    % =====================================================================
    % NATURAL CONVECTION — VERTICAL PLATE
    % Ref: Incropera Ch.9, Churchill-Chu correlation
    % For Ra ~ 1e6 (laminar), typical h ~ 5-10 W/(m2K) for small plates in air
    % =====================================================================

    r.name = 'lit: natural conv vertical h in [3,30] for 50mm plate [Incropera Ch.9]';
    [h_nat, Ra] = h_natural_convection('vertical', 0.05, 25, 80);
    r.pass = h_nat > 3 && h_nat < 30 && Ra > 0;
    r.detail = sprintf('h=%.1f W/(m2K), Ra=%.2e', h_nat, Ra);
    results{end+1} = r;

    % Horizontal heated plate facing up has higher h than facing down
    % Ref: Incropera Table 9.1
    r.name = 'lit: h(horizontal_top) > h(horizontal_bottom) [Incropera Table 9.1]';
    [h_top, ~] = h_natural_convection('horizontal_top', 0.05, 25, 80);
    [h_bot, ~] = h_natural_convection('horizontal_bottom', 0.05, 25, 80);
    r.pass = h_top > h_bot;
    r.detail = sprintf('h_top=%.1f, h_bot=%.1f', h_top, h_bot);
    results{end+1} = r;

    % =====================================================================
    % FORCED CONVECTION — FLAT PLATE
    % Ref: Incropera eq.7.30: Nu_L = 0.664*Re^0.5*Pr^(1/3) (laminar)
    % For L=0.1m, U=2m/s, air at 50C: Re ~ 10000 (laminar)
    % =====================================================================

    r.name = 'lit: forced conv laminar flat plate [Incropera eq.7.30]';
    [h_fc, Re_fc] = h_forced_convection(0.1, 2, 25, 75);
    % At film temp ~50C: nu~1.8e-5, k~0.028
    % Re = rho*U*L/mu ~ 1.1*2*0.1/2e-5 ~ 11000 (still laminar < 5e5)
    % Nu = 0.664*11000^0.5*0.71^(1/3) = 0.664*105*0.89 = 62
    % h = Nu*k/L = 62*0.028/0.1 = 17.4
    r.pass = Re_fc < 5e5 && h_fc > 10 && h_fc < 30;
    r.detail = sprintf('h=%.1f W/(m2K), Re=%.0f', h_fc, Re_fc);
    results{end+1} = r;

    % =====================================================================
    % RADIATION — LINEARIZED h
    % Ref: Incropera eq.1.9: h_rad = eps*sigma*(Ts^2+Ta^2)*(Ts+Ta)
    % At Ts=100C(373K), Ta=25C(298K), eps=1:
    % h_rad = 5.67e-8*(373^2+298^2)*(373+298) = 5.67e-8*228058*671 = 8.67
    % =====================================================================

    r.name = 'lit: linearized h_rad at 100C/25C [Incropera eq.1.9]';
    h_r = h_radiation(1.0, 25, 100);
    expected_hr = sigma * (373.15^2 + 298.15^2) * (373.15 + 298.15);
    r.pass = assert_near(h_r, expected_hr, 0.01, r.name);
    r.detail = sprintf('h_rad=%.2f, expected %.2f W/(m2K)', h_r, expected_hr);
    results{end+1} = r;

    % =====================================================================
    % CSPI — DROFENIK MEASURED VALUES
    % Ref: Drofenik & Kolar, CIPS06 Fig.7
    % =====================================================================

    r.name = 'lit: CSPI Al prototype [Drofenik CIPS06 Fig.7a, measured]';
    cspi_al = cspi_calc(0.26, 0.22);  % measured Rth=0.26, Vol=0.22L
    r.pass = assert_near(cspi_al, 17.5, 0.5, r.name);
    r.detail = sprintf('CSPI=%.1f (paper: ~17.5)', cspi_al);
    results{end+1} = r;

    r.name = 'lit: CSPI Cu prototype [Drofenik CIPS06 Fig.7b, measured]';
    cspi_cu = cspi_calc(0.22, 0.22);  % measured Rth=0.22, Vol=0.22L
    r.pass = assert_near(cspi_cu, 20.7, 0.5, r.name);
    r.detail = sprintf('CSPI=%.1f (paper: ~20.7)', cspi_cu);
    results{end+1} = r;

    % =====================================================================
    % FAN SCALING LAWS
    % Ref: Drofenik CIPS06 eq.29-31, 65-fan survey ranges
    % k1 = [0.5..13.5]*1e-3, k2 = [3.9..8.85]*1e-4, k3 = [3.0..76.5]*1e-6
    % =====================================================================

    r.name = 'lit: fan scaling k1,k2,k3 in survey range [Drofenik CIPS06 eq.33-35]';
    [k1, k2, k3] = fan_scaling_fit(0.0068, 165, 5, 0.04, 15500);
    r.pass = k1 > 0.5e-3 && k1 < 13.5e-3 && ...
             k2 > 3.9e-4 && k2 < 8.85e-4 && ...
             k3 > 3.0e-6 && k3 < 76.5e-6;
    r.detail = sprintf('k1=%.2e, k2=%.2e, k3=%.2e', k1, k2, k3);
    results{end+1} = r;

    % =====================================================================
    % ZTH — FOSTER NETWORK STEADY STATE
    % Ref: Any thermal textbook: Zth(t->inf) = sum(Ri)
    % =====================================================================

    r.name = 'lit: Foster Zth(inf) = sum(R) [thermal network theory]';
    R = [0.1 0.2 0.3 0.4];
    tau = [1e-3 1e-2 1e-1 1];
    [Zth, ~] = zth_foster(R, tau, 100, 200);
    r.pass = assert_near(Zth(end), sum(R), 0.001, r.name);
    r.detail = sprintf('Zth(100s)=%.4f, sum(R)=%.1f', Zth(end), sum(R));
    results{end+1} = r;

    % =====================================================================
    % AIR PROPERTIES AT STANDARD CONDITIONS
    % Ref: Incropera Appendix A.4, air at 1atm
    % At 300K (27C): rho=1.177, mu=1.857e-5, k=0.0263, Cp=1007, Pr=0.707
    % =====================================================================

    r.name = 'lit: air density at 27C ~ 1.177 kg/m3 [Incropera App.A.4, 300K]';
    rho = rho_air(27);
    r.pass = assert_near(rho, 1.177, 0.03, r.name);
    r.detail = sprintf('rho=%.3f', rho);
    results{end+1} = r;

    r.name = 'lit: air Cp at 27C ~ 1007 J/(kg*K) [Incropera App.A.4, 300K]';
    cp = Cp_air(27);
    r.pass = assert_near(cp, 1007, 10, r.name);
    r.detail = sprintf('Cp=%.1f', cp);
    results{end+1} = r;

    r.name = 'lit: air viscosity at 27C ~ 1.857e-5 Pa*s [Incropera App.A.4, 300K]';
    mu = mu_air(27);
    r.pass = assert_near(mu, 1.857e-5, 2e-7, r.name);
    r.detail = sprintf('mu=%.4e', mu);
    results{end+1} = r;

    r.name = 'lit: air conductivity at 27C ~ 0.0263 W/(m*K) [Incropera App.A.4, 300K]';
    kt = Kt_air(27);
    r.pass = assert_near(kt, 0.0263, 0.002, r.name);
    r.detail = sprintf('k=%.4f', kt);
    results{end+1} = r;
end
