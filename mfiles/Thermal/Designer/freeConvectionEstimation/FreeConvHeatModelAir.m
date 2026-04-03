classdef FreeConvHeatModelAir < handle
    %UNTITLED3 Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        faceArr
        heatDissipationTot
        temperatureAmbient
        
        temperatureSurface
        heatTransferCoeffArr
        heatDissipationArr
    end
    
    methods
        function obj = FreeConvHeatModelAir(faceArr)
            %UNTITLED3 Summary of this function goes here
            %   formula from https://www.electronics-cooling.com/2001/08/simplified-formula-for-estimating-natural-convection-heat-transfer-coefficient-on-a-flat-plate/
            obj.faceArr = faceArr;

        end
        function obj = calcSurfaceTemp(obj,temperatureAmbient,heatDissipationTot)
            obj.temperatureAmbient = temperatureAmbient;
            obj.heatDissipationTot = heatDissipationTot;
            
            fun = @(x) obj.heatDissipationCalc(x);
            x0 = obj.temperatureAmbient;
            ydata = obj.heatDissipationTot;
%             ydata = 0;
%             absTol = 1;
            opts = optiset('solver','nl2sol');
%             opts = optiset('solver','mkltrnls','tolafun',absTol);
            Opt = opti('fun',fun,'ydata',ydata,'x0',x0,'options',opts);
            [x1] = solve(Opt);
            obj.temperatureSurface = x1;
            obj.heatCoeffFreeConvPlateSimplAir(obj.temperatureSurface);
            for i = 1:length(obj.faceArr)
                obj.heatDissipationArr(i) = obj.heatTransferCoeffArr(i)*obj.faceArr(i).area*(obj.temperatureSurface-obj.temperatureAmbient);
            end
        end
    end
    
    methods (Access = protected)        
        function qTot = heatDissipationCalc(obj,temperatureSurface)
            obj.heatCoeffFreeConvPlateSimplAir(temperatureSurface);
            qTot = 0;
            for i = 1:length(obj.faceArr)
                qTot = qTot + obj.heatTransferCoeffArr(i)*obj.faceArr(i).area*(temperatureSurface-obj.temperatureAmbient);
            end
        end
        function obj = heatCoeffFreeConvPlateSimplAir(obj, temperatureSurface)
            %UNTITLED3 Summary of this function goes here
            %   formula from https://www.electronics-cooling.com/2001/08/simplified-formula-for-estimating-natural-convection-heat-transfer-coefficient-on-a-flat-plate/
            for i = 1:length(obj.faceArr)
                switch obj.faceArr(i).orientation
                    case 1 % vertical
                        C = 1.42;
                        n = 0.25;
                    case 2 % horizontal, heated side up
                        C = 1.32;
                        n = 0.25;
                    case 3 % horizontal, heated side down
                        C = 0.59;
                        n = 0.25;
                    otherwise
                        error('orientation not defined propertly')
                end
                deltaT = abs(temperatureSurface-obj.temperatureAmbient);
                obj.heatTransferCoeffArr(i) = C*(deltaT/obj.faceArr(i).charLength)^n;
            end
        end
    end

end

