classdef LiquidProperty < handle
    %LiquidProperty Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        fluidRef
        raw
        fluidData
    end
    
    methods
        function obj = LiquidProperty(fluidRef)
            %FLUIDPROPERTY Construct an instance of this class
            %   Detailed explanation goes here
            obj.fluidRef = fluidRef;
            [~,~,obj.raw] = xlsread('W:\Technology\Functions\Thermal\db\FluidData.xlsx',...
                obj.fluidRef);
            for i = 4:length(obj.raw(:,1))
                j = i-3;
                obj.fluidData.temperature(j) = obj.raw{i,1};
                obj.fluidData.pressure(j) = obj.raw{i,2};
                obj.fluidData.specHeatCP(j) = obj.raw{i,3};
                obj.fluidData.dynVisc(j) = obj.raw{i,4};
                obj.fluidData.thermCond(j) = obj.raw{i,5};
                obj.fluidData.density(j) = obj.raw{i,6};
            end
            obj.fluidData.freezingPt = obj.raw{4,7};
            obj.fluidData.boilingPt = obj.raw{4,8};
        end
        
        function dynVisc = calcDynVisc(obj, temperature)
            %calcDynVisc calculates the dynamic viscosity for given
            %temperature (SI-units)
            % valid for sufficiently diluted gases (pressure below ~20 bar)
            dynVisc = interp1(...
                obj.fluidData.temperature,...
                obj.fluidData.dynVisc,...
                temperature,...
                'linear',...
                'extrap');
            if temperature < obj.fluidData.freezingPt
                warning('specified temperature below freezing point at 1 atm, result might be nonsensical')
            elseif temperature > obj.fluidData.boilingPt
                warning('specified temperature above boiling point at 1 atm, result might be nonsensical')
            end
        end

        function density = calcDensity(obj, temperature, ~)
            %calcDensity calculates the density for given temperature
            %(SI-units)
            density = interp1(...
                obj.fluidData.temperature,...
                obj.fluidData.density,...
                temperature,...
                'linear',...
                'extrap');
            if temperature < obj.fluidData.freezingPt
                warning('specified temperature below freezing point at 1 atm, result might be nonsensical')
            elseif temperature > obj.fluidData.boilingPt
                warning('specified temperature above boiling point at 1 atm, result might be nonsensical')
            end
        end
        
        function kinVisc = calcKinVisc(obj, temperature, ~)
            %calcKinVisc calculates the kinematic viscosity for given
            %temperature (SI-units)
            density = obj.calcDensity(temperature);
            dynVisc = obj.calcDynVisc(temperature);
            kinVisc = dynVisc/density;
            if temperature < obj.fluidData.freezingPt
                warning('specified temperature below freezing point at 1 atm, result might be nonsensical')
            elseif temperature > obj.fluidData.boilingPt
                warning('specified temperature above boiling point at 1 atm, result might be nonsensical')
            end
        end
        
        function specHeatCapCp = calcSpecHeatCapCp(obj, temperature, ~)
            %calcSpecHeatCapCp calculates the specific heat capctity cp for
            %given temperature (SI-units)
            specHeatCapCp = interp1(...
                obj.fluidData.temperature,...
                obj.fluidData.specHeatCP,...
                temperature,...
                'linear',...
                'extrap');
            if temperature < obj.fluidData.freezingPt
                warning('specified temperature below freezing point at 1 atm, result might be nonsensical')
            elseif temperature > obj.fluidData.boilingPt
                warning('specified temperature above boiling point at 1 atm, result might be nonsensical')
            end
        end
        
        function thermalConductivity = calcThermalConductivity(obj, temperature, ~)
            %calcThermalConductivity calculates the thermal conductivity for
            %given temperature (SI-units)
            thermalConductivity = interp1(...
                obj.fluidData.temperature,...
                obj.fluidData.thermCond,...
                temperature,...
                'linear',...
                'extrap');
            if temperature < obj.fluidData.freezingPt
                warning('specified temperature below freezing point at 1 atm, result might be nonsensical')
            elseif temperature > obj.fluidData.boilingPt
                warning('specified temperature above boiling point at 1 atm, result might be nonsensical')
            end
        end
        
    end
end