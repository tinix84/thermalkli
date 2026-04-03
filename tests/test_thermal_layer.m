function results = test_thermal_layer()
    results = {};

    r.name = 'ThermalLayer: create isotropic';
    layer = ThermalLayer(0.001, 200);
    r.pass = layer.thick == 0.001 && layer.kOp == 200 && layer.kIp == 200;
    r.detail = sprintf('thick=%.4f kOp=%.1f kIp=%.1f', layer.thick, layer.kOp, layer.kIp);
    results{end+1} = r;

    r.name = 'ThermalLayer: create anisotropic';
    layer = ThermalLayer(0.001, 0.3, 200);
    r.pass = layer.thick == 0.001 && layer.kOp == 0.3 && layer.kIp == 200;
    r.detail = sprintf('kOp=%.1f kIp=%.1f', layer.kOp, layer.kIp);
    results{end+1} = r;

    r.name = 'ThermalLayer: resistance no spreading';
    layer = ThermalLayer(0.001, 200);
    rTh = layer.thermalLayerResistance(1e-4);
    expected = 0.001 / (200 * 1e-4);
    r.pass = assert_near(rTh, expected, 1e-6, r.name);
    r.detail = sprintf('got %.6f, expected %.6f', rTh, expected);
    results{end+1} = r;

    r.name = 'ThermalLayer: spreading resistance (Lee model)';
    layer = ThermalLayer(0.001, 200);
    aIn = 1e-4; aOut = 4e-4; hEff = 500;
    [rTh, rThSpread, rThThrough] = layer.thermalLayerResistance(aIn, aOut, hEff);
    r.pass = rTh > rThThrough && rThSpread > 0 && rTh > 0;
    r.detail = sprintf('rTh=%.4f rThSpread=%.4f rThThrough=%.4f', rTh, rThSpread, rThThrough);
    results{end+1} = r;

    r.name = 'ThermalLayerStack: single layer matches ThermalLayer';
    stack = ThermalLayerStack();
    stack.addLayer(ThermalLayer(0.001, 200));
    rThStack = stack.thermalLayerResistance(1e-4);
    rThSingle = ThermalLayer(0.001, 200).thermalLayerResistance(1e-4);
    r.pass = assert_near(rThStack, rThSingle, 1e-10, r.name);
    r.detail = sprintf('stack=%.6f single=%.6f', rThStack, rThSingle);
    results{end+1} = r;

    r.name = 'ThermalLayerStack: two-layer series resistance';
    stack = ThermalLayerStack();
    stack.addLayer(ThermalLayer(0.001, 200));
    stack.addLayer(ThermalLayer(0.0005, 0.3));
    A = 1e-4;
    rThStack = stack.thermalLayerResistance(A);
    expected = 0.001/(200*1e-4) + 0.0005/(0.3*1e-4);
    r.pass = assert_near(rThStack, expected, 0.01, r.name);
    r.detail = sprintf('got %.4f, expected %.4f', rThStack, expected);
    results{end+1} = r;

    r.name = 'ThermalLayerStack: multi-layer with spreading';
    stack = ThermalLayerStack();
    stack.addLayer(ThermalLayer(0.001, 200));
    stack.addLayer(ThermalLayer(0.0005, 0.3));
    aIn = 1e-4; aOut = 4e-4; hEff = 500;
    [rTh, rThSpread, rThThrough] = stack.thermalLayerResistance(aIn, aOut, hEff);
    r.pass = rTh > 0 && rThSpread >= 0;
    r.detail = sprintf('rTh=%.4f rThSpread=%.4f rThThrough=%.4f', rTh, rThSpread, rThThrough);
    results{end+1} = r;
end
