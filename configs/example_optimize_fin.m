function cfg = example_optimize_fin()
    cfg.heatsink.rhoSink = 2698.9;
    cfg.heatsink.kSink = 180;
    cfg.heatsink.specHeat = 880;
    cfg.heatsink.heightTotal = 21e-3;
    cfg.heatsink.numBridge = 0;
    cfg.heatsink.widthChannel = 1.05e-3;

    cfg.fluid.type = 'H2OGly50';
    cfg.fluid.flowrate = 1.0 / 1000 / 60;  % 1 L/min
    cfg.fluid.tInlet = 343.15;              % 70C

    cfg.heating.widthContact = 16.9e-3;
    cfg.heating.lengthContact = 13.7e-3;
    cfg.heating.numHeatedSides = 1;
    cfg.heating.maxDissLength = 21e-3;
    cfg.heating.numInSeries = 1;
    cfg.heating.spacing = 0;
    cfg.heating.pLoss = 100;

    % Sweep ranges
    cfg.sweep.thickHeatsink = linspace(3e-3, 13e-3, 6);
    cfg.sweep.thickWall = linspace(0.5e-3, 1.2e-3, 4);
end
