function cfg = example_free_conv()
    % Example: bridge rectifier component natural convection cooling
    % Based on bridgeTemperatureCalc.m: 4x7.5x9.1x14.3mm bridge, 0.8W at 75C ambient
    cfg.t_ambient = 75;    % [C]
    cfg.p_total = 0.8;     % [W]

    % 6 faces of a rectangular bridge component
    thick = 4e-3; width = 7.5e-3; height = 9.1e-3; len = 14.3e-3;

    cfg.faces.area = [
        width * (height + thick/2) * 2, ...   % sides outside (2x)
        len * (height + thick/2) * 2, ...     % sides front/back (2x)
        width * len, ...                       % top
        width * len                            % bottom
    ];
    cfg.faces.char_length = [height, height, width/4, width/4];
    cfg.faces.orientation = {'vertical', 'vertical', 'horizontal_top', 'horizontal_bottom'};
    cfg.faces.emissivity = [0.9, 0.9, 0.9, 0.9];
end
