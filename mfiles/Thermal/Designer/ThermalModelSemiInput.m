classdef ThermalModelSemiInput
    %ThermalModelSemiInput Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        
        % if no pcb or no sink/spreader is present, leave corresponding fields empty
        % temperature calculation for multiple junctions is currently only implemented for dissipation solely through bottom
        
        includeBottom = 0       % Wheter or not to consider heat dissipation on bottom side of pcb [bool]
        rThJCBottom = []        % Thermal resistance of Semi junction to case bottom [K/W] (as array if multiple junctions in one packaging)
        areaContact = 0         % Area of Semi in contact with PCB or heat sink/spreader (Area of exposed pad if applicable) [m^2]
        thInsContactPadPcb = 0  % Thermal insulance of gap pad between Semi and PCB (or heat sink/spreader) [K*m^2/W]
        pcbLayerStack = []      % Layer stack description of pcb in format [[thick_1, k_1];[thick_2, k_2];...;[thick_n, k_n]], thick in [m], k in [K*m/W]
        areaSingleVia = 0       % Crosssection area of single via [m^2]
        kVia = 0                % Thermal conductivity of via material [W/(m*K)]
        pcbNumVia = 0           % Number of thermal vias [int]
        pcbEstimateNumVia = 0   % Estimate number of thermal vias based on areaContact instead of using pcbNumVia [bool]
        pcbViaSpacing = 0       % Spacing of vias, must be provided if pcbEstimateNumVia is true [m]
        thInsContactPcbSink = 0 % Thermal insulance of gap pad between PCB and heat sink/spreader [K*m^2/W]
        sinkLayerStack = []     % Layer stack description of sink/spreader layers in format [[thick_1, k_1];[thick_2, k_2];...;[thick_n, k_n]], thick in [m], k in [K*m/W]
        areaDissBottom = 0      % Area available for dissipation of  heat to bottom fluid [m^2]
        hFluidBottom = 0        % Heat transfer coefficient from sink surface to fluid below [W/(m^2*K)]
        tempFluidBottom = 0     % Temperature of bottom fluid before Semi [K]
        
        includeTop = 0          % Wheter or not to consider heat dissipation on top side of pcb [bool]
        rThJCTop = []           % Thermal resistance of Semi junction to case top [K/W] (as array if multiple junctions in one packaging)
        areaCaseTop = 0         % Area of Semi casetop in contact with air [m^2]
        areaDissTop = 0         % Area on top side of pcb (or heat sink/spreader) available for heat dissipation (including areaCaseTop) [m^2]
        hFluidTop = 0           % Heat transfer coefficient from  top surface to fluid above [W/(m^2*K)]
        tempFluidTop = 0        % Temperature of top fluid before Semi [K]
        
        pLossJunction = []      % Power loss of Semi [W] (as array if multiple junctions in one packaging)
        
        tempJunctionMax = []    % Limit temperature of Semi [K] (as array if multiple junctions in one packaging)
                
        % tempJunctionMax must be set to calculate the maximum possible power loss, the minimal dissipation area
        % pLossJunction must be set to calculate the junction temperature, the minimal dissipation area
        % areaDissBottom must be set to calculate the thermal resistance from junction to fluid, the junction temperature, the maximum possible power loss
        % tempFluidBottom must be set to calculate the junction temperature, the minimal dissipation area, the maximum possible power loss
        
    end
    
    methods
    end
    
end
