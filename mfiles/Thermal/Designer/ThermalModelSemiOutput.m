classdef ThermalModelSemiOutput
    %ThermalModelSemiOutput Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
               
        rThCaseFluidBot
        
        rThCaseTopAmbient
        rThCasePcbTopAmbient
        
        tJunction % array of temperatures if copacked semi, scalar otherwise
        
        pcbNumVia
        
        pLossMax
        % if Dissipation occurs on top and bottom of pcb, the available
        % areas are assumed to be equal on both sides
        aDissipationMin
        % if Dissipation occurs on top and bottom of pcb, the heat exchange
        % coefficient is assumed to be equal on both sides
        hFluidMin
        
    end
    
    methods
    end
    
end
