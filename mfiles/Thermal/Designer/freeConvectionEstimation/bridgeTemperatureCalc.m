clear all
close all
clc

thick = 4*10^-3;
width = 7.5*10^-3;
height = 9.1*10^-3;
length = 14.3*10^-3;
temperatureAmbient = 75;
heatDissipation = 0.8;

faceArr(1).description = 'sides outside (twice)';
faceArr(1).area = width*(height+thick/2)*2;
faceArr(1).charLength = height;
faceArr(1).orientation = 1;
faceArr(2).description = 'top outside';
faceArr(2).area = width*(length+thick/2);
faceArr(2).charLength = width;
faceArr(2).orientation = 2;
faceArr(3).description = 'sides inside (twice)';
faceArr(3).area = width*(height-thick/2)*2;
faceArr(3).charLength = width;
faceArr(3).orientation = 3; % assume constants for horizontal downfacing, because convection flow is partially blocked by roof of bridge
faceArr(4).description = 'top inside';
faceArr(4).area = width*(length-thick/2);
faceArr(4).charLength = width;
faceArr(4).orientation = 3;
faceArr(5).description = 'thin side of bridge, vertical part(four times)';
faceArr(5).area = thick*height*4;
faceArr(5).charLength = height;
faceArr(5).orientation = 1;
faceArr(6).description = 'thin side of bridge, horizontal part(two times)';
faceArr(6).area = thick*length*2;
faceArr(6).charLength = thick;
faceArr(6).orientation = 1;

bridgeThermModel = FreeConvHeatModelAir(faceArr);
bridgeThermModel.calcSurfaceTemp(temperatureAmbient,heatDissipation);

temperatureSurface = bridgeThermModel.temperatureSurface;
heatTransferCoeffArr = bridgeThermModel.heatTransferCoeffArr;
heatDissipationArr = bridgeThermModel.heatDissipationArr;
