clear
clc

%% input definition

% temperature calculation for multiple junctions is currently only implemented for dissipation solely through bottom

input = ThermalModelSemiInput;

input.includeBottom = true;    % Wheter or not to consider heat dissipation on bottom side of pcb [bool]
input.rThJCBottom = [1];       % Thermal resistance of Semi junction to case bottom [K/W]
input.areaContact = 100*10^-6;  % Area of Semi in contact with PCB or heat sink/spreader (Area of exposed pad if applicable) [m^2]
input.pcbLayerStack = ...
    [[0.070*10^-3, 400];...
    [0.214*10^-3, 0.3];...
    [0.105*10^-3, 400];...
    [0.3*10^-3, 0.3];...
    [0.105*10^-3, 400];...
    [0.26*10^-3, 0.3];...
    [0.105*10^-3, 400];...
    [0.3*10^-3, 0.3];...
    [0.105*10^-3, 400];...
    [0.26*10^-3, 0.3];...
    [0.105*10^-3, 400];...
    [0.3*10^-3, 0.3];...
    [0.105*10^-3, 400];...
    [0.214*10^-3, 0.3];...
    [0.07*10^-3, 400]];      % Layer stack description of pcb in format [[thick_1, k_1];[thick_2, k_2];...;[thick_n, k_n]], thick in [m], k in [K*m/W]

input.areaSingleVia = pi*(0.15^2-((0.3-0.02)/2)^2)*10^-6;       % material crosssection area of single via [m^2]
input.kVia = 400;              % Thermal conductivity of via material [W/(m*K)]
input.pcbNumVia = 17*14;           % Number of thermal vias [int]
input.pcbEstimateNumVia = false;   % Estimate number of thermal vias based on areaContact instead of using pcbNumVia [bool]
% input.pcbViaSpacing = 0.0006;   % Spacing of vias, must be provided if pcbEstimateNumVia is true [m]
input.thInsContactPcbSink = 77.4*10^-6; % Thermal insulance of gap pad between PCB and heat sink/spreader [K*m^2/W]
input.sinkLayerStack = [[0.005, 200]];     % Layer stack description of sink/spreader layers in format [[thick_1, k_1];[thick_2, k_2];...;[thick_n, k_n]], thick in [m], k in [K*m/W]
input.areaDissBottom = 100*10^-6;      % Area available for dissipation of  heat to bottom fluid [m^2]% input.hFluidBottom = 17000;      % Heat transfer coefficient from sink surface to fluid below [W/(m^2*K)]
input.hFluidBottom = 1000;      % Heat transfer coefficient from sink surface to fluid below [W/(m^2*K)]
input.tempFluidBottom = 74;    % Temperature of bottom fluid before Semi [K]

input.includeTop = false;      % Wheter or not to consider heat dissipation on top side of pcb [bool]

input.pLossJunction = [20];       % Power loss of Semi [W]


%% model setup

model = ThermalModelSemi(input);

%% update model

% model.updateModel(input);

%% calculations

model.calcRthFluidBot();
model.calcTJunction();

%% read outputs

output = model.output;
