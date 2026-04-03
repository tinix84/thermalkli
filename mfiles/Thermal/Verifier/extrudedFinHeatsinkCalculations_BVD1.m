clear all
close all
clc

addpath('W:\Technology\Functions\Thermal\Model');
addpath('W:\Technology\Functions\Thermal\Formula');

%% define heatsink (either from database or directly defined)

% create heatsink object for heatsink specified by heatsinkRef as defined
%in database 'W:\Technology\Functions\Thermal\db\heatsinks.xlsx'
% heatsink = heatsinkFactory('HS_EX_001');

% create heatsink object directly
rhoSink = 2698.9;
kSink = 180;
specHeatMatSink = 880;
numChannel = 10;
thickHeatsink = 10E-3;
thickWall = 1E-3;
widthChannel = 1.05E-3;

heatsink = extrudedFinModel(...
    rhoSink,...
    kSink,...
    specHeatMatSink,...
    numChannel,...
    thickHeatsink, ...
    thickWall,...
    widthChannel);

%% define fluid and flow properties

% set up fluid with properties as defined in database
%'W:\Technology\Functions\Thermal\db\FluidData.xlsx'
heatsink.defineFluid('H2OGly50');

heatsink.TFluidIn = 273.15+72;

flowrateLM = 3.5;
flowrate = flowrateLM/1000/60;

heatsink.flowrate = flowrate;

%% define heating arrangement

% widthHotContact = 13.75*10^-3;
widthHotContact = 16.5*10^-3;
% lengthHotContact = 13.5*10^-3;
% lengthHotContact = 14.5*10^-3;
lengthHotContact = 13*10^-3;
% areaHotContact = widthHotContact*lengthHotContact;
areaHotContact = 200E-6;
numHeatedSides = 2;
maxDissipationLength = 30*10^-3;
numComponentsInSeries = 1;
componentSpacing = 0;

heatsink.defineHeatingArrangement(...
    widthHotContact,...
    lengthHotContact,...
    numHeatedSides,...
    maxDissipationLength,...
    numComponentsInSeries,...
    componentSpacing);

%% calculate thermal resistance of heatsink

heatsink.pLossComponent = 50;

heatsink.thermalResistance();
rThHF = heatsink.rThTot;

%% calculate thermal resistances of rest of thermal stack

% insTim = 32.9*10^-6;
insTim = 2*10^-4;
rThCH = insTim/areaHotContact;

rThCF = rThCH + rThHF;

rThJC = 0.35;

rThJF = rThJC + rThCF;

%% calculate temperatures for given power loss and fluid inlet temperature

pLoss = 30;
TFluidIn = 72;

TH = TFluidIn + pLoss*rThHF;

TC = TFluidIn + pLoss*rThCF;

TJ = TFluidIn + pLoss*rThJF;

% NuLoc = heatsink.NuLocal

