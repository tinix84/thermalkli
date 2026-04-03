clear all
close all
clc

%useful setting for debugging, comment it in normal mode
dbstop if error;
debugmode=1; %debug mode uses dummy instruments

addpath('W:\Technology\Functions\Thermal\Model');
addpath('W:\Technology\Functions\Thermal\Formula');
addpath('W:\Technology\Functions\Thermal\Designer');

results = zeros(51,8,10);

for i = 1:51
    for j = 1:8
        %% define heatsink (either from database or directly defined)
        
        % create heatsink object for heatsink specified by heatsinkRef as defined
        %in database 'W:\Technology\Functions\Thermal\db\heatsinks.xlsx'
        % heatsink = heatsinkFactory('HS_EX_001');
        
        % create heatsink object directly
        rhoSink = 2698.9;
        kSink = 180;
        specHeatMatSink = 880;
        thickHeatsink = (3.0+(i-1)*0.2)*10^-3;
        thickWall = (0.5+(j-1)*0.1)*10^-3;
        widthChannel = 1.05E-3;
        numChannel = ceil((21E-3-thickWall)/(widthChannel+thickWall));
        numBridge = 0;
        results(i,j,1) = numChannel;
        
        heatsink = extrudedFinModel(...
            rhoSink,...
            kSink,...
            specHeatMatSink,...
            numChannel,...
            thickHeatsink, ...
            thickWall,...
            widthChannel,...
            numBridge);
        
        %% define fluid and flow properties
        
        % set up fluid with properties as defined in database
        %'W:\Technology\Functions\Thermal\db\FluidData.xlsx'
        heatsink.defineFluid('H2OGly50');
        
        heatsink.TFluidIn = 273.15+70;
        
        flowrateLM = 1.0;
        flowrate = flowrateLM/1000/60;
        
        heatsink.flowrate = flowrate;
        
        %% define heating arrangement
        
        widthHotContact = 16.9*10^-3;
        lengthHotContact = 13.7*10^-3;
        numHeatedSides = 2;
        maxDissipationLength = 30*10^-3;
        numComponentsInSeries = 9;
        componentSpacing = 16.5E-3;
        
        heatsink.defineHeatingArrangement(...
            widthHotContact,...
            lengthHotContact,...
            numHeatedSides,...
            maxDissipationLength,...
            numComponentsInSeries,...
            componentSpacing);
        
        % areaHole = pi*(3.5E-3)^2;
        % areaHotContactTIM = widthHotContact*lengthHotContact-areaHole;
        
        %% calculate thermal resistance of heatsink
        
        heatsink.pLossComponent = 40;
        
        heatsink.thermalResistance();
        rThHF = heatsink.rThTot;
        
        results(i,j,2:10) = rThHF;
    end
end

