clear all
close all
clc

addpath('W:\Technology\Functions\Thermal\Model');
addpath('W:\Technology\Functions\Thermal\Formula');
addpath('W:\Technology\Functions\Thermal\Designer');


%% define heatsink (either from database or directly defined)

% create heatsink object for heatsink specified by heatsinkRef as defined
%in database 'W:\Technology\Functions\Thermal\db\heatsinks.xlsx'
% heatsink = heatsinkFactory('HS_EX_001');

% create heatsink object directly
rhoSink = 2698.9;
kSink = 180;
specHeatMatSink = 880;
thickHeatsink = 3.5E-3;
thickWall = 1.2E-3;
widthChannel = 1.05E-3;
numChannel = ceil((21E-3-thickWall)/(widthChannel+thickWall))
numBridge = 0

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

flowrateLM = 1.5;
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
rThFluidLocToIn = heatsink.rThFluidLocToIn
rThContactFluidLoc = heatsink.rThContactFluidLoc
rThHF = heatsink.rThTot
TFluidLocMean = heatsink.TFluidLocMean
TWall = heatsink.TWall
TContact = heatsink.TContact
        
