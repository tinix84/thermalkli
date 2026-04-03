clear all
close all
clc

addpath('W:\Technology\Functions\ThermalModeling\Designer');
addpath('W:\Technology\Functions\Inverter\Designer');

%% SYSTEM SPECIFICATIONS

% Load specifications
V_ref = 200;                        % load reference voltage peak value [V]
I = 50;                              % load current peak value [A]
phi = 30;                           % load power factor angle [°]
f = 1000;                           % load fundamental frequency [Hz]

% Inverter specifications
V_dc = 400;                         % inverter DC-bus (or battery) voltage [V]
fsw = 30*f;                         % inverter switching frequency [Hz]

V_max = V_dc/sqrt(3);               % SVM maximum output peak voltage (in linearity)
if V_ref > V_max
    V = V_max;
else
    V = V_ref;
end

m = V/V_max;                        % modulation index

theta_0 = 0;                        % voltage vector starting angle [°]

q = 1;                              % number of fundamental periods

[t,v] = SVM_7(f,fsw,m,V_dc,theta_0,q,1);
theta_ref = theta_0 + 360 * f * t;              % reference voltage vector angle [°]
theta = theta_ref - 0.5 * f / fsw * 360;        % real voltage vector angle (actuation delay) [°]
v = v{1};                                       % a-leg voltage
i = I * cos(pi/180*(theta-phi));                % a-phase current

% thermal model inputs common to all components
thermModelInput_Common = ThermalModelSemiInput;
thermModelInput_Common.includeBottom = true;
thermModelInput_Common.thInsContactPcbSink = 90*10^-6;
thermModelInput_Common.sinkLayerStack = [[0.003, 200]];
thermModelInput_Common.hFluidBottom = 15000;
thermModelInput_Common.tempFluidBottom = 70;


%% calculate current for each component

% optifun = @(PLoss) comp1

%% set up components

thermalModelInput_comp1 = thermModelInput_Common;
thermalModelInput_comp1.areaDissBottom = 500*10^-6;
component1 = SCComponentModel(thermalModelInput_comp1, 'Model_IGBT.mat', 'Model_Diode.mat');
% component1 = SCComponentModel(thermalModelInput_comp1, 'Model_Diode.mat');

% define component operating parameters
iArrComp1 = [(v>0).*i.*(i>0); (v>0).*i.*(i<0)];

% calculate component operating point
component1.updateOperatingParameters(t,iArrComp1);

% second component
thermalModelInput_comp2 = thermModelInput_Common;
thermalModelInput_comp2.areaDissBottom = 500*10^-6;

iArrComp2 = [(v==0).*i.*(i>0); (v==0).*i.*(i<0)];

component2 = SCComponentModel(thermalModelInput_comp2, 'Model_IGBT.mat', 'Model_Diode.mat');
component2.updateOperatingParameters(t,iArrComp2);

component1
component2


% areaOpt = AreaPowerLossParOpt(component1, component2);


% pLossTot = component1.pLossMeanComp+component2.pLossMeanComp;
% areaOpt.pLossAreaDistrOpt(2000*10^-6);
% optAreaArr = areaOpt.areaArr;
% pLossTotOpt = component1.pLossMeanComp+component2.pLossMeanComp;

% tJMax = max(max(component1.TjArr), max(component2.TjArr));
% areaOpt.tJMaxAreaDistrOpt(1000*10^-6);
% optAreaArr = areaOpt.areaArr;
% tJMaxOpt = areaOpt.tJMax;


% areaList = [];
% pLossList = [];
% for i = 1:20
%     area = (2000+i*200)*10^-6;
%     areaList(i) = area;
%     areaOpt.areaDistrOpt(area);
%     pLossList(i) = areaOpt.pLossTot;
% end


% areaList = [];
% pLossList = [];
% for i = 1:20
%     area = (2000+i*200)*10^-6;
%     areaList(i) = area;
%     component1.changeAreaDissBottom(area/2)
%     component2.changeAreaDissBottom(area/2)
%     pLossTot = component1.pLossMeanComp + component2.pLossMeanComp;
%     pLossList(i) = pLossTot;
% end












