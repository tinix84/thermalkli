function result = cmd_h_coeff(parsed)
    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m h-coeff --mode <type> [options]\n\n');
        fprintf('Modes:\n');
        fprintf('  forced     --length <m> --velocity <m/s> --t-ambient <C> --t-surface <C>\n');
        fprintf('  natural    --orientation <vertical|horizontal_top|horizontal_bottom> --length <m> --t-ambient <C> --t-surface <C>\n');
        fprintf('  radiation  --epsilon <-> --t-ambient <C> --t-surface <C>\n');
        result = struct(); return;
    end
    if ~isfield(parsed, 'mode')
        fprintf(2, 'Error: --mode is required (forced|natural|radiation)\n');
        result = struct(); return;
    end
    switch parsed.mode
        case 'forced'
            L = str2double(parsed.length); U = str2double(parsed.velocity);
            Ta = str2double(parsed.t_ambient); Ts = str2double(parsed.t_surface);
            [h, Re] = h_forced_convection(L, U, Ta, Ts);
            result.h = h; result.Re = Re;
            fprintf('h=%.4f\n', h); fprintf('Re=%.1f\n', Re);
        case 'natural'
            orient = parsed.orientation; L = str2double(parsed.length);
            Ta = str2double(parsed.t_ambient); Ts = str2double(parsed.t_surface);
            [h, Ra] = h_natural_convection(orient, L, Ta, Ts);
            result.h = h; result.Ra = Ra;
            fprintf('h=%.4f\n', h); fprintf('Ra=%.2e\n', Ra);
        case 'radiation'
            eps_val = str2double(parsed.epsilon);
            Ta = str2double(parsed.t_ambient); Ts = str2double(parsed.t_surface);
            h = h_radiation(eps_val, Ta, Ts);
            result.h = h;
            fprintf('h=%.4f\n', h);
        otherwise
            fprintf(2, 'Error: unknown mode "%s"\n', parsed.mode);
            result = struct();
    end
end
