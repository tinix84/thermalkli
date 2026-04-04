function cfg = test_hydraulic_config()
    % Test config for hydraulic-op command.
    % Heatsink I117: Hf=102mm, tf=1.7mm, bch=4.3mm
    % Fan EBMW2E200_axial_AC_50Hz, 2 fans in parallel, push ventilation.
    cfg.heatsink.profile  = 'I117';
    cfg.heatsink.length   = 0.33;    % [m]
    cfg.heatsink.width    = 0.65;    % [m]
    cfg.heatsink.material = 'all_aluminum';
    cfg.fan.model         = 'EBMW2E200_axial_AC_50Hz';
    cfg.fan.count         = 2;
    cfg.ventilation.type  = 'push';
    cfg.ventilation.impingeOpening = 0.22;  % [m] (used only for impinge type)
    cfg.ambient.tInlet    = 313.15;  % [K] = 40 °C
end
