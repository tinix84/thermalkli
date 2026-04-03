classdef HeatsinkClass < handle
    %HeatsinkClass generic class for heatsinks
    %   Detailed explanation goes here
    
    properties
        heatsinkRef              % [string]    reference to the used heatsink as defined in 'W:\Technology\Functions\Thermal\db\heatsinks.xlsx'
        heatsinkType             % [string]    type of used heatsink
        
        materialSink             % [string]    name of heatsink material
        rhoSink                  % [kg/m^3]    density of sink material
        kSink                    % [W/(m*K)]   thermal conductivity of sink material
        specHeatMatSink          % [J/(m^3*K)] specific heat capacity of sink material
        
        g = 9.81                 % [m/s^2]     gravitational acceleration
        
        fluid                    %             object of type FluidProperty to define the cooling fluid
        
        flowrate                 % [m^3/s]     forced flowrate
        TFluidIn                 % [K]         inlet temperature of fluid
        pLossComponent           % [W]         power loss per component
        
        hInfTot                  % [W/(m^2*K)] heat transfer coefficient of heatsink with regards to contact surface, neglecting heatspreading
        rThTot                   % [K/W]       absolut thermal resistance from specified contact surface to fluid with regards to inlet temperature
        rThFluidFlow             % [K/W]       absolut thermal resistance due to limited heat capacity and flow rate of fluid
    end
    
    methods
        function obj = HeatsinkClass()
        end
        
        function defineFluid(obj, FluidRef)
            obj.fluid = fluidPropertyFactory(FluidRef);
        end
        
        function set.flowrate(obj, flowrate)
            obj.flowrate = flowrate;
        end
        
        function set.pLossComponent(obj, pLossComponent)
            %setPLossComponent sets the power loss per component [W]
            obj.pLossComponent = pLossComponent;
        end
        
        function rThFluidFlow = calcRthFluidFlow(obj, temperature)
            % calculates the Rth due to limited heat capacity of fluid
            % (increase of fluid temperature, averaged over heated section)
            
            rhoFluid = obj.fluid.calcDensity(temperature);
            specHeatFluid = obj.fluid.calcSpecHeatCapCp(temperature);
            
            rThFluidFlow = 1/(rhoFluid*specHeatFluid*obj.flowrate);
            obj.rThFluidFlow = rThFluidFlow;
        end
        
    end
end

