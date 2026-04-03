function result = workflow_extruded_fin(parsed)
    % workflow_extruded_fin - extruded fin heatsink thermal analysis
    %
    % Usage: thermal_cli.m extruded-fin --config <file>
    % Config fields (SI units - meters, Kelvin, Watts):
    %   cfg.heatsink.rhoSink       - density [kg/m^3]
    %   cfg.heatsink.kSink         - thermal conductivity [W/(m*K)]
    %   cfg.heatsink.specHeat      - specific heat [J/(kg*K)]
    %   cfg.heatsink.thickHeatsink - heatsink base thickness [m]
    %   cfg.heatsink.thickWall     - wall/fin thickness [m]
    %   cfg.heatsink.widthChannel  - channel width [m]
    %   cfg.heatsink.numBridge     - number of bridges (0 = none)
    %   cfg.heatsink.heightTotal   - total heatsink height [m]
    %   cfg.fluid.type             - fluid reference string (e.g. 'H2OGly50')
    %   cfg.fluid.flowrate         - volumetric flow rate [m^3/s]
    %   cfg.fluid.tInlet           - inlet temperature [K]
    %   cfg.heating.widthContact   - contact width in flow direction [m]
    %   cfg.heating.lengthContact  - contact length perpendicular to flow [m]
    %   cfg.heating.numHeatedSides - number of heated sides (1 or 2)
    %   cfg.heating.maxDissLength  - max dissipation length per component [m]
    %   cfg.heating.numInSeries    - number of components in series
    %   cfg.heating.spacing        - component spacing center-to-center [m]
    %   cfg.heating.pLoss          - power loss per component [W]

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m extruded-fin --config <file>\n');
        fprintf('Runs extruded fin heatsink thermal analysis.\n');
        result = struct();
        return;
    end

    pkg load io;
    cfg = cli_load_config(parsed);

    fprintf('--- Extruded Fin Heatsink Analysis ---\n');

    % Derive number of channels from total height
    numChannel = ceil((cfg.heatsink.heightTotal - cfg.heatsink.thickWall) / ...
        (cfg.heatsink.widthChannel + cfg.heatsink.thickWall));

    heatsink = extrudedFinModel(...
        cfg.heatsink.rhoSink, ...
        cfg.heatsink.kSink, ...
        cfg.heatsink.specHeat, ...
        numChannel, ...
        cfg.heatsink.thickHeatsink, ...
        cfg.heatsink.thickWall, ...
        cfg.heatsink.widthChannel, ...
        cfg.heatsink.numBridge);

    fprintf('num_channels=%d\n', numChannel);

    heatsink.defineFluid(cfg.fluid.type);
    heatsink.TFluidIn = cfg.fluid.tInlet;
    heatsink.flowrate = cfg.fluid.flowrate;

    heatsink.defineHeatingArrangement(...
        cfg.heating.widthContact, ...
        cfg.heating.lengthContact, ...
        cfg.heating.numHeatedSides, ...
        cfg.heating.maxDissLength, ...
        cfg.heating.numInSeries, ...
        cfg.heating.spacing);

    heatsink.pLossComponent = cfg.heating.pLoss;

    heatsink.thermalResistance();

    fprintf('rth_tot=%.6f\n', heatsink.rThTot);
    fprintf('rth_fluid_flow=%.6f\n', heatsink.rThFluidFlow);
    fprintf('reynolds=%.1f\n', heatsink.Re);
    fprintf('v_fluid=%.4f\n', heatsink.vFluid);

    for i = 1:length(heatsink.TContact)
        fprintf('t_contact_%d=%.2f\n', i, heatsink.TContact(i));
        fprintf('t_wall_%d=%.2f\n', i, heatsink.TWall(i));
        fprintf('t_fluid_mean_%d=%.2f\n', i, heatsink.TFluidLocMean(i));
    end

    result.rThTot = heatsink.rThTot;
    result.rThFluidFlow = heatsink.rThFluidFlow;
    result.Re = heatsink.Re;
    result.vFluid = heatsink.vFluid;
    result.TContact = heatsink.TContact;

    if isfield(parsed, 'save_csv')
        fid = fopen(parsed.save_csv, 'w');
        fprintf(fid, 'point,value,unit\n');
        fprintf(fid, 'rth_tot,%.6f,K/W\n', heatsink.rThTot);
        fprintf(fid, 'rth_fluid_flow,%.6f,K/W\n', heatsink.rThFluidFlow);
        fprintf(fid, 'reynolds,%.1f,-\n', heatsink.Re);
        for i = 1:length(heatsink.TContact)
            fprintf(fid, 't_contact_%d,%.2f,K\n', i, heatsink.TContact(i));
        end
        fclose(fid);
        fprintf('Results saved to: %s\n', parsed.save_csv);
    end

    fprintf('--- Complete ---\n');
end
