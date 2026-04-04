function result = workflow_multi_sim(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m multi-sim --config <file>\n');
        fprintf('Sweeps heatsink geometry, checks temperature limits, auto-resizes.\n');
        result = struct(); return;
    end

    cfg = cli_load_config(parsed);
    fprintf('--- Multi-Configuration Simulation: %s ---\n', cfg.title);

    params.Tin = cfg.Tin;
    params.Niter = cfg.Niter;
    params.piastra = cfg.piastra;
    params.Dx = cfg.Dx;
    params.Dy = cfg.Dy;

    all_results = {};
    count = 0;

    for ns = 1:length(cfg.solutions)
        sol = cfg.solutions(ns);
        for k1 = 1:length(cfg.sweep.tf)
            for k2 = 1:length(cfg.sweep.Hf)
                for k3 = 1:length(cfg.sweep.Tp)
                    bch = cfg.sweep.Tp(k3) - cfg.sweep.tf(k1);
                    if bch < 2, continue; end
                    for k4 = 1:length(cfg.sweep.tb)
                        for k5 = 1:length(cfg.sweep.tr)
                            geom.a_init = sol.a_init;
                            geom.b_init = sol.b_init;
                            geom.a_max = sol.a_max;
                            geom.b_max = sol.b_max;
                            geom.tf = cfg.sweep.tf(k1);
                            geom.Hf = cfg.sweep.Hf(k2);
                            geom.bch = bch;
                            geom.tb = cfg.sweep.tb(k4);
                            geom.tr = cfg.sweep.tr(k5);

                            sources = cfg.sources;
                            sources.x_g = sol.x_g;
                            sources.y_g = sol.y_g;

                            count = count + 1;
                            fprintf('  [%d] %s tf=%.1f Hf=%.0f Tp=%.1f tb=%.0f ... ', ...
                                count, sol.hs_type, geom.tf, geom.Hf, cfg.sweep.Tp(k3), geom.tb);

                            res = multi_sim_core(sol, geom, sources, params);

                            if res.solved_therm
                                fprintf('OK (Tmax=%.0fC, a=%.0f, b=%.0f)\n', max(res.Ths), res.a, res.b);
                            else
                                fprintf('FAIL (Tmax=%.0fC, limit=%.0fC)\n', max(res.Ths), max(sources.Tmax));
                            end
                            all_results{count} = res;

                            if strcmp(cfg.piastra, 'no'), break; end
                        end
                    end
                end
            end
        end
    end

    % Summary
    fprintf('\n--- Results Summary (%d configurations) ---\n', count);
    fprintf('%-4s %-6s %-5s %-5s %-5s %-6s %-8s %-6s %-6s %-6s\n', ...
        '#', 'a[mm]', 'b[mm]', 'tf', 'Hf', 'tb', 'Rth', 'Tmax', 'Therm', 'Hydr');
    fprintf('%s\n', repmat('-', 1, 65));

    for i = 1:count
        r = all_results{i};
        if r.solved_therm, ts = 'OK'; else, ts = 'FAIL'; end
        if r.solved_hydr, hs = 'OK'; else, hs = 'FAIL'; end
        fprintf('%-4d %-6.0f %-5.0f %-5.1f %-5.0f %-5.0f %-8.4f %-6.0f %-6s %-6s\n', ...
            i, r.a, r.b, r.tf, r.Hf, r.tb, r.Rth_fin, max(r.Ths), ts, hs);
    end

    result.all_results = all_results;
    result.count = count;

    if isfield(parsed, 'save_csv')
        fid = fopen(parsed.save_csv, 'w');
        fprintf(fid, 'idx,a_mm,b_mm,tf_mm,Hf_mm,tb_mm,bch_mm,Rth_fin,Tmax_C,solved_therm,solved_hydr,Qv_f,Re_hydr\n');
        for i = 1:count
            r = all_results{i};
            fprintf(fid, '%d,%.0f,%.0f,%.1f,%.0f,%.0f,%.1f,%.6f,%.1f,%d,%d,%.6f,%.1f\n', ...
                i, r.a, r.b, r.tf, r.Hf, r.tb, r.bch, r.Rth_fin, max(r.Ths), r.solved_therm, r.solved_hydr, r.Qv_f, r.Re_hydr);
        end
        fclose(fid);
        fprintf('\nResults saved to: %s\n', parsed.save_csv);
    end

    fprintf('\n--- Complete ---\n');
end
