function results = test_natural_conv_hs()
    results = {};

    % Test using CLI function directly via parsed struct
    r.name = 'natural_conv_hs: basic calculation';
    parsed.n_fins = '10';
    parsed.fin_height = '0.05';
    parsed.fin_length = '0.1';
    parsed.fin_thickness = '0.002';
    parsed.channel_width = '0.008';
    parsed.base_thickness = '0.005';
    parsed.k = '200';
    parsed.t_ambient = '25';
    parsed.p_loss = '10';
    parsed.emissivity = '0.9';
    res = cmd_natural_conv_hs(parsed);
    r.pass = res.Rth > 0 && res.Ts > 25 && res.eta_fin > 0.5 && res.eta_fin <= 1;
    r.detail = sprintf('Rth=%.2f K/W, Ts=%.1fC, eta=%.3f', res.Rth, res.Ts, res.eta_fin);
    results{end+1} = r;

    % More power -> higher Ts
    r.name = 'natural_conv_hs: more power -> higher Ts';
    parsed2 = parsed;
    parsed2.p_loss = '20';
    res2 = cmd_natural_conv_hs(parsed2);
    r.pass = res2.Ts > res.Ts;
    r.detail = sprintf('10W: %.1fC, 20W: %.1fC', res.Ts, res2.Ts);
    results{end+1} = r;

    % More fins -> lower Rth
    r.name = 'natural_conv_hs: more fins -> lower Rth';
    parsed3 = parsed;
    parsed3.n_fins = '20';
    res3 = cmd_natural_conv_hs(parsed3);
    r.pass = res3.Rth < res.Rth;
    r.detail = sprintf('10 fins: %.2f K/W, 20 fins: %.2f K/W', res.Rth, res3.Rth);
    results{end+1} = r;
end
