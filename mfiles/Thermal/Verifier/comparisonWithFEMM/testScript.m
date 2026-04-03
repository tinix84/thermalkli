clear
clc
addpath('W:\Technology\Functions\ThermalModeling\Designer');

%% input definition

input = ThermalModelSemiInput;

input.includeBottom = true;    % Wheter or not to consider heat dissipation on bottom side of pcb [bool]
input.rThJCBottom = 0;       % Thermal resistance of Semi junction to case bottom [K/W]
input.areaContact = 80*10^-6;  % Area of Semi in contact with PCB or heat sink/spreader (Area of exposed pad if applicable) [m^2]
input.thInsContactPadPcb = 0;  % Thermal insulance of gap pad between Semi and PCB (or heat sink/spreader) [K*m^2/W]
input.pcbLayerStack = [[0.070*10^-3, 400];[0.463*10^-3, 0.3];[0.035*10^-3, 400];[0.463*10^-3, 0.3];[0.035*10^-3, 400];[0.463*10^-3, 0.3];[0.070*10^-3, 400]];      % Layer stack description of pcb in format [[thick_1, k_1];[thick_2, k_2];...;[thick_n, k_n]], thick in [m], k in [K*m/W]
input.areaSingleVia = 1.5795e-08;       % Crosssection area of single via [m^2]
input.kVia = 400;              % Thermal conductivity of via material [W/(m*K)]
input.pcbNumVia = 0;           % Number of thermal vias [int]
input.pcbEstimateNumVia = true;   % Estimate number of thermal vias based on areaContact instead of using pcbNumVia [bool]
input.pcbViaSpacing = 0.002;   % Spacing of vias, must be provided if pcbEstimateNumVia is true [m]
input.thInsContactPcbSink = 0; % Thermal insulance of gap pad between PCB and heat sink/spreader [K*m^2/W]
input.sinkLayerStack = [[0.003, 200]];     % Layer stack description of sink/spreader layers in format [[thick_1, k_1];[thick_2, k_2];...;[thick_n, k_n]], thick in [m], k in [K*m/W]
input.areaDissBottom = 1000*10^-6;      % Area available for dissipation of  heat to bottom fluid [m^2]
input.hFluidBottom = 500;      % Heat transfer coefficient from sink surface to fluid below [W/(m^2*K)]
input.tempFluidBottom = 70+273.15;    % Temperature of bottom fluid before Semi [K]

input.includeTop = false;      % Wheter or not to consider heat dissipation on top side of pcb [bool]
input.rThJCTop = 2;            % Thermal resistance of Semi junction to case top [K/W]
input.areaCaseTop = 80*10^-6;  % Area of Semi casetop in contact with air [m^2]
input.areaDissTop = 1000*10^-6;      % Area on top side of pcb (or heat sink/spreader) available for heat dissipation [m^2]
input.hFluidTop = 20;          % Heat transfer coefficient from top surface to fluid above [W/(m^2*K)]
input.tempFluidTop = 70+273.15;       % Temperature of top fluid before Semi [K]

input.pLossJunction = 0.9;       % Power loss of Semi [W]

input.tempJunctionMax = 98+273.15;    % Limit temperature of Semi [K]

%% model setup

model = ThermalModelSemi(input);

%% update model

% model.updateModel(input);
% model.updateTempJunctionMax(80);
% model.updatePLossJunction(3.2165);
% model.updateAreaDissBottom(1000*10^-6);
% model.updateAreaDissTop(1000*10^-6);
% model.updateTempFluidBottom(40);
% model.updateTempFluidTop(70);
% model.updateHFluidBottom(100);
% model.updateHFluidTop(10);

%% calculations

model.calcRthJunctionFluidBot();
% model.calcRthJunctionFluidTop();
model.calcTJunction();
model.calcPLossMax();
model.calcADissMin();
model.calcHFluidMin();

%% read outputs

output = model.output;
