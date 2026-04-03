clear all
close all
clc

%% thermal layer definition

thickSolder = 0.1*10^-3;
solderLayer = ThermalLayer(thickSolder, 65);
thickCopper1 = 0.3*10^-3;
copperLayer1 = ThermalLayer(thickCopper1, 385);
thickCeramic = 0.32*10^-3;
ceramicLayer = ThermalLayer(thickCeramic, 23);
thickCopper2 = 0.2*10^-3;
copperLayer2 = ThermalLayer(thickCopper2, 385);
thickTIM = 0.025*10^-3;
timLayer = ThermalLayer(thickTIM, 2.5);
stackCrCuTIM = ThermalLayerStack();
stackCrCuTIM.addLayer(ceramicLayer, copperLayer2, timLayer);
thickSinkSpreading = 0.0*10^-3;
sinkSpreadingLayer = ThermalLayer(thickSinkSpreading, 200);
stackCrCuTIMAl = ThermalLayerStack();
stackCrCuTIMAl.addLayer(ceramicLayer, copperLayer2, timLayer, sinkSpreadingLayer);

hSink = 20000;

%% thermal resistance calc no spreading

areaIGBT = 6.59*5.91*10^-6;
areaSolder = areaIGBT;
areaCopper1 = areaSolder;
areaCopper1_Eff = 7.9*7.9*10^-6;
areaMoldModul = 40*50*10^-6;
areaInterface = areaCopper1;
areaSink = areaInterface;
rThSinkFluid = 1/(hSink*areaSink);
rThTim = timLayer.thermalLayerResistance(areaInterface);
insTim = rThTim*areaInterface;
rThSinkSpreadingLayer = sinkSpreadingLayer.thermalLayerResistance(areaInterface, areaSink, hSink );
rThTIMFluid = rThSinkFluid+rThSinkSpreadingLayer;
hInterface = 1/(rThTIMFluid*areaInterface);

rThCu1Sink = stackCrCuTIMAl.thermalLayerResistance(areaCopper1, areaSink, hSink );
rThCu1Fluid = rThCu1Sink + rThSinkFluid;

hCu1 = 1/(rThCu1Fluid*areaCopper1);
rThCu1 = copperLayer1.thermalLayerResistance(areaSolder, areaCopper1, hCu1 );
rThSolderFluid = rThCu1 + rThCu1Fluid;
hSolder = 1/(rThSolderFluid*areaSolder);
rThSolder = solderLayer.thermalLayerResistance(areaIGBT, areaSolder, hSolder);
rThJF_NoSpreading = rThSolder + rThSolderFluid;
hJunction = 1/(rThJF_NoSpreading*areaIGBT);
insJF_NoSpread = 1/hJunction*10^6;
insJS_NoSpread = 1/hJunction*10^6 - 1/hInterface*10^6;

%% thermal resistance calc spreading in first copper layer

areaSolder = areaIGBT;
areaCopper1 = areaCopper1_Eff;
areaInterface = areaCopper1;
areaSink = areaInterface;
rThSinkFluid = 1/(hSink*areaSink);

rThCu1Sink = stackCrCuTIMAl.thermalLayerResistance(areaCopper1, areaSink, hSink );
rThCu1Fluid = rThCu1Sink + rThSinkFluid;

hCu1 = 1/(rThCu1Fluid*areaCopper1);
rThCu1 = copperLayer1.thermalLayerResistance(areaSolder, areaCopper1, hCu1 );
rThSolderFluid = rThCu1 + rThCu1Fluid;
hSolder = 1/(rThSolderFluid*areaSolder);
rThSolder = solderLayer.thermalLayerResistance(areaIGBT, areaSolder, hSolder);
rThJF_SpreadCopper1 = rThSolder + rThSolderFluid;

%% spreading in first copper layer

sinkAreaArr_SpreadCopper1 = zeros(1,100);
rThJFArr_SpreadCopper1 = zeros(1,100);

for i = 0:99
    areaCopper1 = areaIGBT+i*(areaCopper1_Eff-areaIGBT)/100;
    areaInterface = areaCopper1;
    areaSink = areaInterface;
    sinkAreaArr_SpreadCopper1(i+1) = areaSink;
    rThSinkFluid = 1/(hSink*areaSink);
    
    rThCu1Sink = stackCrCuTIMAl.thermalLayerResistance(areaCopper1, areaSink, hSink );
    rThCu1Fluid = rThCu1Sink + rThSinkFluid;
    
    hCu1 = 1/(rThCu1Fluid*areaCopper1);
    rThCu1 = copperLayer1.thermalLayerResistance(areaSolder, areaCopper1, hCu1 );
    rThSolderFluid = rThCu1 + rThCu1Fluid;
    hSolder = 1/(rThSolderFluid*areaSolder);
    rThSolder = solderLayer.thermalLayerResistance(areaIGBT, areaSolder, hSolder);
    rThJF_SpreadCopper1 = rThSolder + rThSolderFluid;
    rThJFArr_SpreadCopper1(i+1) = rThSolder + rThSolderFluid;
end

%% spreading in first and second copper layer

sinkAreaArr = zeros(1,100);
rThJFArr = zeros(1,100);

areaSolder = areaIGBT;
areaCopper1 = areaCopper1_Eff;

for i = 0:99
    areaInterface = areaCopper1+i*1*10^-6;
    areaSink = areaInterface;
    sinkAreaArr(i+1) = areaSink;
    rThSinkFluid = 1/(hSink*areaSink);
    rThCu1Sink = stackCrCuTIMAl.thermalLayerResistance(areaCopper1, areaSink, hSink );
    rThCu1Fluid = rThCu1Sink + rThSinkFluid;
    
    hCu1 = 1/(rThCu1Fluid*areaCopper1);
    rThCu1 = copperLayer1.thermalLayerResistance(areaSolder, areaCopper1, hCu1 );
    rThSolderFluid = rThCu1 + rThCu1Fluid;
    hSolder = 1/(rThSolderFluid*areaSolder);
    rThSolder = solderLayer.thermalLayerResistance(areaIGBT, areaSolder, hSolder);
    rThJF = rThSolder + rThSolderFluid;
    rThJFArr(i+1) = rThSolder + rThSolderFluid;
end


hold on

scatter(areaIGBT*10^6,rThJF_NoSpreading)
sinAreaArrTot = [sinkAreaArr_SpreadCopper1 sinkAreaArr];
rThJFArrTot = [rThJFArr_SpreadCopper1 rThJFArr];
plot(sinAreaArrTot*10^6, rThJFArrTot, '-')
plot([0 1000], [1.325 1.325], '-.')
line([areaCopper1_Eff*10^6 areaCopper1_Eff*10^6], [-10 10])
line([areaIGBT*10^6 areaIGBT*10^6], [-10 10])
legend('RthJF no spreading', 'RthJF with spreading', 'RthJF from simulation')

axis([0 100 0 2.6])

ylabel('Rth [K / W]')
xlabel('Area considered for spreading [mm^2]')

hold off

resultsArr = [sinAreaArrTot*10^6; rThJFArrTot];
