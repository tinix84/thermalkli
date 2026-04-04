function result = cmd_heatsink_rth(parsed)
    % cmd_heatsink_rth - one-shot thermal resistance from DB reference + operating conditions
    % Usage: thermal_cli.m heatsink-rth --ref <db_ref> --fluid <type> --flowrate <m3/s>
    %   --t-inlet <K> --p-loss <W> --width-contact <m> --length-contact <m>
    %   [--num-heated-sides <1|2>] [--num-in-series <int>] [--spacing <m>]

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m heatsink-rth --ref <db_ref> --fluid <type> --flowrate <m3/s>\n');
        fprintf('  --t-inlet <K> --p-loss <W> --width-contact <m> --length-contact <m>\n');
        fprintf('  [--num-heated-sides <1|2>] [--num-in-series <int>] [--spacing <m>]\n');
        result = struct(); return;
    end

    pkg load io;

    hs = heatsinkFactory(parsed.ref);
    hs.defineFluid(parsed.fluid);
    hs.TFluidIn = str2double(parsed.t_inlet);
    hs.flowrate = str2double(parsed.flowrate);
    hs.pLossComponent = str2double(parsed.p_loss);

    nSides = 1;
    if isfield(parsed, 'num_heated_sides'), nSides = str2double(parsed.num_heated_sides); end
    nSeries = 1;
    if isfield(parsed, 'num_in_series'), nSeries = str2double(parsed.num_in_series); end
    spacing = 0;
    if isfield(parsed, 'spacing'), spacing = str2double(parsed.spacing); end

    wc = str2double(parsed.width_contact);
    lc = str2double(parsed.length_contact);

    % maxDissLength defaults to heightHeatsink if available
    if isa(hs, 'extrudedFinModel') && ~isempty(hs.heightHeatsink)
        maxDiss = hs.heightHeatsink;
    else
        maxDiss = wc;
    end

    hs.defineHeatingArrangement(wc, lc, nSides, maxDiss, nSeries, spacing);
    hs.thermalResistance();

    fprintf('rth_tot=%.6f\n', hs.rThTot);
    fprintf('reynolds=%.1f\n', hs.Re);
    fprintf('v_fluid=%.4f\n', hs.vFluid);

    for i = 1:length(hs.TContact)
        fprintf('t_contact_%d=%.2f\n', i, hs.TContact(i));
    end

    result.rThTot = hs.rThTot;
    result.Re = hs.Re;
    result.TContact = hs.TContact;
end
