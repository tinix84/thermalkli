classdef GasProperty < handle
    %GasProperty Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        fluidRef
        raw
        fluidData
    end
    
    methods
        function obj = GasProperty(fluidRef)
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
                obj.fluidData.specHeatCV(j) = obj.raw{i,4};
                obj.fluidData.dynVisc(j) = obj.raw{i,5};
                obj.fluidData.thermCond(j) = obj.raw{i,6};
                obj.fluidData.Pr(j) = obj.raw{i,7};
                obj.fluidData.density(j) = obj.raw{i,8};
            end
            obj.fluidData.sutherlandConst = obj.raw{4,9};
            
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
        end

        function density = calcDensity(obj, temperature, pressure)
            %calcDensity calculates the density for given temperature and
            %pressure (SI-units)
            % valid for sufficiently diluted gases (pressure below ~20 bar)
            T1 = temperature;
            p1 = interp1(...
                obj.fluidData.temperature,...
                obj.fluidData.pressure,...
                T1,...
                'linear',...
                'extrap');
            rho1 = interp1(...
                obj.fluidData.temperature,...
                obj.fluidData.density,...
                T1,...
                'linear',...
                'extrap');
            p2 = pressure;
            T2 = T1;
            rho2 = rho1*(p2*T1)/(p1*T2); % ideal gas law
            density = rho2;
        end
        
        function kinVisc = calcKinVisc(obj, temperature, pressure)
            %calcKinVisc calculates the kinematic viscosity for given
            %temperature and pressure (SI-units)
            % valid for sufficiently diluted gases (pressure below ~20 bar)
            density = obj.calcDensity(temperature, pressure);
            dynVisc = obj.calcDynVisc(temperature);
            kinVisc = dynVisc/density;
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
        end
        
    end
end

