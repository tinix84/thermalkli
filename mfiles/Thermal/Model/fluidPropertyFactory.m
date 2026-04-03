function [fluidProperty] = fluidPropertyFactory(fluidRef)
    %fluidPropertyFactory factory function that returns a FluidProperty
    %Object of the appropriate type
    %   Detailed explanation goes here
    
    switch fluidRef
%         case 'air'
%             fluidProperty = GasProperty('air');
        case 'airDry'
            fluidProperty = GasProperty('airDry');
        case 'H2OGly50'
            fluidProperty = LiquidProperty('H2OGly50');
        case 'SAE30'
            fluidProperty = LiquidProperty('SAE30');
        otherwise
            error('undefined or unknown fluid')
    end

end
