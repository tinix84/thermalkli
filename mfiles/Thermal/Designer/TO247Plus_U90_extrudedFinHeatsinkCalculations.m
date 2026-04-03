clear all
close all
clc

depthChannel = 8*10^-3;
thickWall = 1*10^-3;
widthChannel = 1.05*10^-3;
thickFin = thickWall;
maxWidthHeatsink = 22*10^-3;
widthHeatsink = floor((maxWidthHeatsink-thickFin)/(widthChannel+thickFin))...
    *(thickFin+widthChannel)+thickFin+0.1*10^-3;
thickHeatsink = depthChannel+2*thickWall;
kProfile = 200;

flowrateLM = 1.5;
flowrate = flowrateLM/1000/60;
specHeatFluid = 3.6*10^3;
rhoFluid = 1000;
kFluid = 0.415;
kinViskM = 1*10^-6;

heatsink = extrudedFinModel(...
    widthHeatsink,...
    thickHeatsink,...
    thickWall,...
    thickFin,...
    widthChannel, ...
    kProfile,...
    specHeatFluid,...
    rhoFluid,...
    kFluid,...
    kinViskM);

numChannel = heatsink.numChannel;
crossAreaFluid = heatsink.crossAreaFluid;

areaContact = 190*10^-6;
widthDissipation = 20*10^-3;
lengthDissipation = 30*10^-3;

heatsink.thermalResistance(...
    areaContact,...
    lengthDissipation,...
    widthDissipation,...
    2,...
    flowrate);
rThSink = heatsink.rThTot;
hSink = heatsink.hInfTot;

thickTIM = 0.329*10^-3;
% thickTIM = 1.936*10^-3;
timLayer = ThermalLayer(thickTIM, 10);
rThTim = timLayer.thermalLayerResistance(areaContact);
insTim = rThTim*areaContact;

rThTot = rThTim + rThSink +0.2
% hCase = 1/(rThTot*areaContact);
% spreadLayerChip = ThermalLayer(0.3*10^-3, 385);
% areaChip = 40*10^-6;
% [rThJC, RspreadCase] = spreadLayerChip.thermalLayerResistance(...
%     areaChip,...
%     190,...
%     hCase);
% 
% pLoss = 50;
% TFluidIn = 72;
% pLossBothSide = 30+50;
% 
% TC = TFluidIn+pLoss*rThTot;
% 
% Tj = TC + pLoss*rThJC;
% 
% results = [depthChannel*10^3, thickWall*10^3, numChannel, rThSink, crossAreaFluid*10^6, widthHeatsink*10^3, thickHeatsink*10^3, hSink/1000]
