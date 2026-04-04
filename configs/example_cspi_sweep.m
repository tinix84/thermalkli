function cfg = example_cspi_sweep()
    cfg.a_chip = 32e-4;
    cfg.p_fan_max = 20;
    cfg.lambda = [210 380];
    cfg.c = [0.02 0.04 0.06 0.08 0.12];
    cfg.t_min = 0.5e-3;
end
