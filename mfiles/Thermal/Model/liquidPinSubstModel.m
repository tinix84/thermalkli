classdef liquidPinSubstModel < handle
    %liquidPinSubstModel Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        kMat
        diameter
        baseThickness
        spacing
        thickness
        pinDepth
        
        areaHot
        areaSink
        
        flowrate
        densityFluid
        specHeatCapFluid
%         dynViscosityFluid
        
        areaUnitCell
        areaHoleBottom
        areaCylinderWall
        areaUnitCellTop
        circumference
        numActivePins
        
        hFluid
        rThPinGround
        rThPinWall
        rThUnitCellTop
        baseLayer
        spreadLayer
        etaFin
        
        hInf
        rThSpread
        rThThrough
        rThTotal
    end
    
    methods
        function obj = liquidPinSubstModel(kMat, diameter, spacing, thickness, baseThickness)
            %liquidPinSubstModel Construct an instance of this class
            %   Detailed explanation goes here
            obj.kMat = kMat;
            obj.diameter = diameter;
            obj.spacing = spacing;
            obj.thickness = thickness;
            obj.baseThickness = baseThickness;
            obj.pinDepth = obj.thickness-obj.baseThickness;
        end
        
        function obj = defineFluidProperties(obj, flowrate, densityFluid, specHeatCapFluid)
            %METHOD1 Summary of this method goes here
            %   Detailed explanation goes here
            obj.flowrate = flowrate;
            obj.densityFluid = densityFluid;
            obj.specHeatCapFluid = specHeatCapFluid;
        end
        
%         function h = estimateHeatTransferCoeff(obj,Q,thick)
%             %METHOD1 Summary of this method goes here
%             %   Detailed explanation goes here
%             thickExp = 0.7;
%             spacing0 = 6;
%             diameter0 = 3;
%             h0 = 17000;
%             Q0 = 7;
%             thick0 = 10;
%             h = h0*(Q/Q0)^0.8*((obj.spacing^2+obj.diameter*pi*thick^thickExp)/(spacing0^2+diameter0*pi*thick0^thickExp));
%         end
        function obj = estimateFluidHeatTransferCoeff(obj)
            %METHOD1 Summary of this method goes here
            %   Detailed explanation goes here
            h0 = 7000;
            flowrate0 = 1.1667e-04; % 7 l/min == 1.1667e-04 m^3/s
            obj.hFluid = h0*(obj.flowrate/flowrate0)^0.8;
        end
        
        function [rTh, varargout] = thermalResistance( obj, areaHot, areaSink )
            %METHOD1 Summary of this method goes here
            %   Detailed explanation goes here
            obj.estimateFluidHeatTransferCoeff();
            
            obj.areaHot = areaHot;
            obj.areaSink = areaSink;
            obj.areaCylinderWall = obj.diameter*pi*obj.pinDepth;
            
            obj.areaUnitCell = obj.spacing^2;
            obj.numActivePins = obj.areaSink/obj.areaUnitCell;
            obj.areaHoleBottom = pi*(obj.diameter/2)^2;
            obj.areaUnitCellTop = obj.areaUnitCell-obj.areaHoleBottom;
            obj.circumference = pi*obj.diameter;
            obj.rThPinGround = 1/(obj.hFluid*obj.areaHoleBottom);
            obj.rThUnitCellTop = 1/(obj.hFluid*obj.areaUnitCellTop)+obj.pinDepth/(obj.kMat*obj.areaUnitCellTop);
            obj.baseLayer = ThermalLayer(obj.baseThickness, obj.kMat);
            hInfBaselayer = obj.baseLayer.thermalResistanceCalc(obj.areaSink);
            
            obj.etaFin = finEfficieny(obj.pinDepth, obj.hFluid, obj.areaCylinderWall, obj.kMat, obj.areaUnitCellTop);
            
            obj.rThPinWall = 1/(obj.hFluid*obj.areaCylinderWall)*1/obj.etaFin;
            
            rThUnitCell = 1/(1/obj.rThPinGround+1/obj.rThUnitCellTop+1/obj.rThPinWall);
            
%             hInfPin = 1/(rThUnitCell*obj.areaUnitCell+0.5/(obj.densityFluid*obj.specHeatCapFluid*obj.flowrate)*obj.areaSink);
            hInfPin = 1/(rThUnitCell*obj.areaUnitCell);

            obj.hInf = 1/(1/hInfBaselayer+1/hInfPin);
            obj.rThThrough = 1/(obj.hInf*areaSink);
            
            obj.spreadLayer = ThermalLayer(obj.baseThickness+obj.pinDepth^0.5,...
                (obj.baseThickness*obj.kMat+ obj.pinDepth*obj.kMat*obj.areaUnitCellTop/obj.areaUnitCell)/obj.thickness);
            [~,obj.rThSpread] = obj.baseLayer.thermalResistanceCalc(obj.areaHot, obj.areaSink, hInfPin);
            
            obj.rThTotal = 1/(obj.hInf*obj.areaSink)+obj.rThSpread;
            rTh = obj.rThTotal;
            if nargout > 3
                error('thermalLayerResistance gives a maximum of three outputs')
            end
            optOutput = [obj.rThSpread, obj.rThThrough];
            for i = 2:nargout
                varargout{i-1} = optOutput(i-1);
            end
        end
    end
end



