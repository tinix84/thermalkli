function result = cmd_heatsink_create(parsed)
    % cmd_heatsink_create - create heatsink from database reference
    % Usage: thermal_cli.m heatsink-create --ref <db_reference>

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m heatsink-create --ref <db_reference>\n');
        fprintf('Creates heatsink from database reference in db/heatsinks.xlsx.\n');
        result = struct(); return;
    end

    pkg load io;
    ref = parsed.ref;
    hs = heatsinkFactory(ref);

    fprintf('ref=%s\n', ref);
    fprintf('type=%s\n', hs.heatsinkType);
    fprintf('material=%s\n', hs.materialSink);
    fprintf('k_sink=%.1f\n', hs.kSink);

    if isa(hs, 'extrudedFinModel')
        fprintf('height=%.6f\n', hs.heightHeatsink);
        fprintf('thick=%.6f\n', hs.thickHeatsink);
        fprintf('thick_wall=%.6f\n', hs.thickWall);
        fprintf('thick_fin=%.6f\n', hs.thickFin);
        fprintf('width_channel=%.6f\n', hs.widthChannel);
        fprintf('num_channel=%d\n', hs.numChannel);
    end

    result.heatsink = hs;
    result.ref = ref;
end
