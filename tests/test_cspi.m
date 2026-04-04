function results = test_cspi()
    % test_cspi - unit tests for cspi_calc and cspi_optimize
    results = {};

    % --- cspi_calc basic ---
    r.name = 'cspi_calc: 1/(0.5*0.2)=10';
    cspi = cspi_calc(0.5, 0.2);
    r.pass = assert_near(cspi, 10, 0.001, r.name);
    r.detail = sprintf('CSPI=%.4f', cspi);
    results{end+1} = r;

    r.name = 'cspi_calc: 1/(0.1*1.0)=10';
    cspi = cspi_calc(0.1, 1.0);
    r.pass = assert_near(cspi, 10, 0.001, r.name);
    r.detail = sprintf('CSPI=%.4f', cspi);
    results{end+1} = r;

    r.name = 'cspi_calc: rth=0.26, vol=0.22 => ~17.5';
    cspi = cspi_calc(0.26, 0.22);
    r.pass = assert_near(cspi, 17.5, 1.0, r.name);
    r.detail = sprintf('CSPI=%.2f (expected ~17.5)', cspi);
    results{end+1} = r;

    % --- cspi_optimize basic ---
    r.name = 'cspi_optimize: aluminum produces valid geometry';
    res = cspi_optimize(210, 32e-4, 0.04, 20);
    r.pass = res.cspi > 0 && isfinite(res.cspi) && res.n >= 2 && res.s > 0 && res.t > 0;
    r.detail = sprintf('CSPI=%.2f, n=%d, s=%.2fmm, t=%.2fmm', ...
        res.cspi, res.n, res.s*1000, res.t*1000);
    results{end+1} = r;

    r.name = 'cspi_optimize: CSPI > 0 (physically meaningful)';
    res = cspi_optimize(210, 32e-4, 0.04, 20);
    r.pass = res.cspi > 0;
    r.detail = sprintf('CSPI=%.2f', res.cspi);
    results{end+1} = r;

    % --- material comparison ---
    r.name = 'cspi_optimize: copper >= aluminum CSPI';
    res_al = cspi_optimize(210, 32e-4, 0.04, 20);
    res_cu = cspi_optimize(380, 32e-4, 0.04, 20);
    r.pass = res_cu.cspi >= res_al.cspi * 0.95;   % 5% tolerance for numerical noise
    r.detail = sprintf('Al CSPI=%.2f, Cu CSPI=%.2f', res_al.cspi, res_cu.cspi);
    results{end+1} = r;

    % --- t_min constraint ---
    r.name = 'cspi_optimize: t_min constraint gives t >= t_min';
    t_min_val = 1.5e-3;
    res = cspi_optimize(210, 32e-4, 0.04, 20, 't_min', t_min_val);
    r.pass = res.t >= t_min_val * 0.999;   % floating point tolerance
    r.detail = sprintf('t=%.3fmm (min=%.3fmm)', res.t*1000, t_min_val*1000);
    results{end+1} = r;

    r.name = 'cspi_optimize: t_min constraint reduces or equals unconstrained CSPI';
    res_free  = cspi_optimize(210, 32e-4, 0.04, 20);
    res_const = cspi_optimize(210, 32e-4, 0.04, 20, 't_min', 1.5e-3);
    r.pass = res_const.cspi <= res_free.cspi * 1.05;   % constrained <= unconstrained (5% tol)
    r.detail = sprintf('free=%.2f, t_min=%.2f', res_free.cspi, res_const.cspi);
    results{end+1} = r;

    % --- Re reported ---
    r.name = 'cspi_optimize: Re > 0 and finite';
    res = cspi_optimize(210, 32e-4, 0.04, 20);
    r.pass = res.Re > 0 && isfinite(res.Re);
    r.detail = sprintf('Re=%.0f', res.Re);
    results{end+1} = r;

    % --- higher fan power gives better CSPI ---
    r.name = 'cspi_optimize: higher fan power gives >= CSPI';
    res_low  = cspi_optimize(210, 32e-4, 0.04, 5);
    res_high = cspi_optimize(210, 32e-4, 0.04, 50);
    r.pass = res_high.cspi >= res_low.cspi * 0.95;
    r.detail = sprintf('5W=%.2f, 50W=%.2f', res_low.cspi, res_high.cspi);
    results{end+1} = r;

    % --- output fields complete ---
    r.name = 'cspi_optimize: all output fields present';
    res = cspi_optimize(210, 32e-4, 0.04, 20);
    required = {'cspi','rth','vol','n','s','t','Re','N_fan','L','V_MAX','dp_MAX','feasible'};
    ok = true;
    for i = 1:length(required)
        if ~isfield(res, required{i})
            ok = false;
            fprintf('  FAIL: missing field %s\n', required{i});
        end
    end
    r.pass = ok;
    r.detail = sprintf('checked %d fields', length(required));
    results{end+1} = r;
end
