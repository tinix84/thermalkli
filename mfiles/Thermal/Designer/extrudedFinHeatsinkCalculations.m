clear all
close all
clc

%% define heatsink

% create heatsink object for heatsink specified by heatsinkRef as defined
% in database 'W:\Technology\Functions\Thermal\db\heatsinks.xlsx'
addpath('W:\Technology\Functions\Thermal\Model');

heatsink = heatsinkFactory('HS_EX_001');

% heightHeatsink = 22*10^-3;
% thickHeatsink = 10*10^-3;
% thickWall = 0.8*10^-3;
% thickFin = thickWall;
% widthChannel = 1.05*10^-3;
% kProfile = 190;
% 
% heatsink = extrudedFinModel(...
%     heightHeatsink,...
%     thickHeatsink,...
%     thickWall,...
%     thickFin,...
%     widthChannel, ...
%     kProfile);

%% define fluid properties

specHeatFluid = 3.6*10^3;
rhoFluid = 1000;
kFluid = 0.415;
kinViskM = 1*10^-6;

heatsink.defineFluidProperties(...
    specHeatFluid,...
    rhoFluid,...
    kFluid,...
    kinViskM);

flowrateLM = 3.5;
flowrate = flowrateLM/1000/60;

heatsink.setFlowrate(flowrate);

%% define heating arrangement

widthHotContact = 16*10^-3;
lengthHotContact = 12.5*10^-3;
areaHotContact = widthHotContact*lengthHotContact;
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

rThHF = heatsink.thermalResistance();

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
