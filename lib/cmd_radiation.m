function result = cmd_radiation(parsed)
    % cmd_radiation - radiation heat transfer calculations
    % Usage: thermal_cli.m radiation --mode <type> [options]
    % Modes: parallel, cylinder, sphere, enclosure, convex

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m radiation --mode <type> [options]\n\n');
        fprintf('Modes:\n');
        fprintf('  parallel   --t1 <K> --t2 <K> --area <m2> --eps1 <-> --eps2 <->\n');
        fprintf('  cylinder   --t1 <K> --t2 <K> --r1 <m> --r2 <m> --length <m> --eps1 <-> --eps2 <->\n');
        fprintf('  sphere     --t1 <K> --t2 <K> --r1 <m> --r2 <m> --eps1 <-> --eps2 <->\n');
        fprintf('  enclosure  --t1 <K> --t2 <K> --eps1 <-> --eps2 <-> --a1 <m2> --a2 <m2> --f12 <->\n');
        fprintf('  convex     --t1 <K> --t2 <K> --a1 <m2> --eps1 <->\n');
        result = struct();
        return;
    end

    if ~isfield(parsed, 'mode')
        fprintf(2, 'Error: --mode is required (parallel|cylinder|sphere|enclosure|convex)\n');
        result = struct();
        return;
    end

    T1 = str2double(parsed.t1);
    T2 = str2double(parsed.t2);

    switch parsed.mode
        case 'parallel'
            A = str2double(parsed.area);
            eps1 = str2double(parsed.eps1);
            eps2 = str2double(parsed.eps2);
            q = heatTransferParallelPlanesRadiation(T1, T2, A, eps1, eps2);

        case 'cylinder'
            r1 = str2double(parsed.r1);
            r2 = str2double(parsed.r2);
            L = str2double(parsed.length);
            eps1 = str2double(parsed.eps1);
            eps2 = str2double(parsed.eps2);
            q = heatTransferConcentricCylinderRadiation(T1, T2, r1, r2, L, eps1, eps2);

        case 'sphere'
            r1 = str2double(parsed.r1);
            r2 = str2double(parsed.r2);
            eps1 = str2double(parsed.eps1);
            eps2 = str2double(parsed.eps2);
            q = heatTransferConcentricSphereRadiation(T1, T2, r1, r2, eps1, eps2);

        case 'enclosure'
            eps1 = str2double(parsed.eps1);
            eps2 = str2double(parsed.eps2);
            A1 = str2double(parsed.a1);
            A2 = str2double(parsed.a2);
            F12 = str2double(parsed.f12);
            q = heatTransferEnclosureRadiation(T1, T2, eps1, eps2, A1, A2, F12);

        case 'convex'
            A1 = str2double(parsed.a1);
            eps1 = str2double(parsed.eps1);
            q = heatTransferSmallConvexRadiation(T1, T2, A1, eps1);

        otherwise
            fprintf(2, 'Error: unknown mode "%s"\n', parsed.mode);
            result = struct();
            return;
    end

    result.q = q;
    result.mode = parsed.mode;
    fprintf('q=%.6f\n', q);
end
