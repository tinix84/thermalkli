function results = test_thermal_model_semi()
    results = {};

    % Test 1: ThermalModelSemi pathCase 2 (bottom, no vias)
    r.name = 'ThermalModelSemi: pathCase 2 bottom no vias';
    input = ThermalModelSemiInput;
    input.includeBottom = true;
    input.rThJCBottom = [0.1];
    input.areaContact = 42e-6;
    input.thInsContactPadPcb = 0;
    input.pcbLayerStack = [[0.000635, 200]; [0.0003, 400]];
    input.areaSingleVia = 1.5795e-08;
    input.kVia = 400;
    input.pcbNumVia = 0;
    input.pcbEstimateNumVia = false;
    input.pcbViaSpacing = 0;
    input.thInsContactPcbSink = 7e-6;
    input.sinkLayerStack = [[0.0048, 200]];
    input.areaDissBottom = 4*42e-6;
    input.hFluidBottom = 17000;
    input.tempFluidBottom = 70;
    input.includeTop = false;
    input.rThJCTop = 2;
    input.areaCaseTop = 300e-6;
    input.areaDissTop = 900e-6;
    input.hFluidTop = 20;
    input.tempFluidTop = 70;
    input.pLossJunction = [67];
    input.tempJunctionMax = 150;

    try
        model = ThermalModelSemi(input);
        model.calcTJunction();
        output = model.output;
        r.pass = output.tJunction > input.tempFluidBottom && output.tJunction < input.tempJunctionMax;
        r.detail = sprintf('tJunction=%.2f K', output.tJunction);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 2: CSC128 module (complex PCB, 238 vias)
    r.name = 'ThermalModelSemi: CSC128 with vias';
    input2 = ThermalModelSemiInput;
    input2.includeBottom = true;
    input2.rThJCBottom = [1];
    input2.areaContact = 100e-6;
    input2.thInsContactPadPcb = 0;
    input2.pcbLayerStack = [
        [0.070e-3, 400];
        [0.214e-3, 0.3];
        [0.105e-3, 400];
        [0.3e-3, 0.3];
        [0.105e-3, 400];
        [0.26e-3, 0.3];
        [0.105e-3, 400];
        [0.3e-3, 0.3];
        [0.105e-3, 400];
        [0.26e-3, 0.3];
        [0.105e-3, 400];
        [0.3e-3, 0.3];
        [0.105e-3, 400];
        [0.214e-3, 0.3];
        [0.07e-3, 400]
    ];
    input2.areaSingleVia = pi*(0.15^2 - ((0.3-0.02)/2)^2)*1e-6;
    input2.kVia = 400;
    input2.pcbNumVia = 17*14;
    input2.pcbEstimateNumVia = false;
    input2.pcbViaSpacing = 0;
    input2.thInsContactPcbSink = 77.4e-6;
    input2.sinkLayerStack = [[0.005, 200]];
    input2.areaDissBottom = 100e-6;
    input2.hFluidBottom = 1000;
    input2.tempFluidBottom = 74;
    input2.includeTop = false;
    input2.rThJCTop = 2;
    input2.areaCaseTop = 100e-6;
    input2.areaDissTop = 100e-6;
    input2.hFluidTop = 20;
    input2.tempFluidTop = 74;
    input2.pLossJunction = [20];
    input2.tempJunctionMax = 150;

    try
        model2 = ThermalModelSemi(input2);
        model2.calcRthFluidBot();
        model2.calcTJunction();
        output2 = model2.output;
        r.pass = output2.tJunction > input2.tempFluidBottom && output2.rThCaseFluidBot > 0;
        r.detail = sprintf('tJunction=%.2f K, rThCaseFluidBot=%.4f K/W', output2.tJunction, output2.rThCaseFluidBot);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;

    % Test 3: Verify calcPLossMax returns positive value
    r.name = 'ThermalModelSemi: calcPLossMax positive';
    try
        model.calcPLossMax();
        output = model.output;
        r.pass = output.pLossMax > 0;
        r.detail = sprintf('pLossMax=%.2f W', output.pLossMax);
    catch e
        r.pass = false;
        r.detail = sprintf('ERROR: %s', e.message);
    end
    results{end+1} = r;
end
