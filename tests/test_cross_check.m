function results = test_cross_check()
    results = {};

    % Cross-check: SoftwareTermico Rth_fin vs Drofenik channel_rth
    % Same geometry: I117 heatsink, 650x330mm, push, 0.05 m3/s, air at 45C
    r.name = 'cross_check: SoftwareTermico vs Drofenik within 20%';
    a_mm = 650; b_mm = 330; tf_mm = 1.7; bch_mm = 4.3; Hf_mm = 48;
    Nf = round(a_mm / (bch_mm + tf_mm));

    % SoftwareTermico
    [~, ~, ~, Rth_sw, ~] = Rth_fin(0.05, a_mm, b_mm, a_mm, tf_mm, bch_mm, Hf_mm, 45, 'push', 200, Nf);

    % Drofenik single channel
    fluid = air_properties(45);
    geom.width = bch_mm * 1e-3;
    geom.height = Hf_mm * 1e-3;
    geom.length = b_mm * 1e-3;
    [rth_ch, ~, ~, ~] = channel_rth(geom, 0.05 / Nf, fluid);
    Rth_drof = rth_ch / Nf;

    ratio = Rth_sw / Rth_drof;
    r.pass = ratio > 0.8 && ratio < 1.2;
    r.detail = sprintf('SW=%.6f, Drof=%.6f, ratio=%.2f', Rth_sw, Rth_drof, ratio);
    results{end+1} = r;
end
