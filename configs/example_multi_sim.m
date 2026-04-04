function cfg = example_multi_sim()
    cfg.title = 'example_multi_sim';
    cfg.Tin = 25;
    cfg.Niter = 10;
    cfg.piastra = 'no';
    cfg.Dx = 5;
    cfg.Dy = 5;

    cfg.sweep.tb = [10 15];
    cfg.sweep.Hf = [48 63];
    cfg.sweep.Tp = [4 5.5];
    cfg.sweep.tf = [1.5 2];
    cfg.sweep.tr = [10];

    cfg.sources.a_n = [110 110 110];
    cfg.sources.b_n = [80 80 80];
    cfg.sources.p_n = [710 710 710];
    cfg.sources.columns = [1 2 3];
    cfg.sources.rows = [1 1 1];
    cfg.sources.Tmax = [93 93 93];
    cfg.sources.scelta = 'centro';

    cfg.solutions(1).hs_type = 'all_aluminum';
    cfg.solutions(1).fan_model = 'EBMW1G180_axial_DC';
    cfg.solutions(1).n_fans = 2;
    cfg.solutions(1).vent_type = 'impinge';
    cfg.solutions(1).impinge_opening = 250;
    cfg.solutions(1).a_init = 400;
    cfg.solutions(1).b_init = 400;
    cfg.solutions(1).a_max = 550;
    cfg.solutions(1).b_max = 600;
    cfg.solutions(1).x_g = [65 200 335];
    cfg.solutions(1).y_g = [200 200 200];
end
