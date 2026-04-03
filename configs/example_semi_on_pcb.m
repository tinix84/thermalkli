function cfg = example_semi_on_pcb()
    % Example: semiconductor on PCB (from Designer/testScript.m)
    cfg.includeBottom = true;
    cfg.rThJCBottom = [0.1];
    cfg.areaContact = 42e-6;
    cfg.thInsContactPadPcb = 0;
    cfg.pcbLayerStack = [[0.000635, 200]; [0.0003, 400]];
    cfg.areaSingleVia = 1.5795e-08;
    cfg.kVia = 400;
    cfg.pcbNumVia = 0;
    cfg.pcbEstimateNumVia = false;
    cfg.pcbViaSpacing = 0;
    cfg.thInsContactPcbSink = 7e-6;
    cfg.sinkLayerStack = [[0.0048, 200]];
    cfg.areaDissBottom = 4*42e-6;
    cfg.hFluidBottom = 17000;
    cfg.tempFluidBottom = 70;

    cfg.includeTop = false;
    cfg.rThJCTop = 2;
    cfg.areaCaseTop = 300e-6;
    cfg.areaDissTop = 900e-6;
    cfg.hFluidTop = 20;
    cfg.tempFluidTop = 70;

    cfg.pLossJunction = [67];
    cfg.tempJunctionMax = 150;
end
