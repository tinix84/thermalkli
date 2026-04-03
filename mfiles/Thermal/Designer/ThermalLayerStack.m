classdef ThermalLayerStack < handle
    %ThermalLayerStack class for stack of several thermal layers
    %   Detailed explanation goes here
    
    properties
        n             % number of layers
        layerArray    % array consisting of individual thermal layers
        thick         % total thickness of layer stack            [m]
        kOp           % thermal conductivity out of plane [K*m*W^-1]
        kIp           % averaged thermal conductivity in plane [K*m*W^-1]
    end
    
    methods
        function obj = ThermalLayerStack
            obj.layerArray = [];
            obj.thick = 0;
            obj.n = 0;
            obj.kOp = 0;
            obj.kIp = 0;
        end
        
        function obj = addLayer(obj, varargin)
            for i = 1:length(varargin)
                newLayer = varargin{i};
                if ~(isa(newLayer,'ThermalLayer'))
                    error('newLayer must be of class ThermalLayer')
                end
                obj.layerArray = [obj.layerArray, newLayer];
                obj.thick = obj.thick + newLayer.thick;
                obj.n = obj.n + 1;
                obj.kOpEquiv();
                obj.kIpEquiv();
            end
        end
        
        function [rTh, varargout] = thermalLayerResistance(obj, aIn, aOut, hEff )
            %THERMALLAYERRESISTANCE calculates the thermal resistance
            %   including thermal spreading effects
            %   RTH = THERMALLAYERRESISTANCE(OBJ,AIN,AOUT,HEFF) Calculates the
            %   thermal resistance, including thermal spreading effects
            %   Inputs:
            %   aIn [m^2] heat transfer area on hot side,
            %   aOut [m^2] heat transfer area on cold side,
            %   hEff [W/m^-2*K^1] heat transfer coefficient from aOut to ambient
            %   literature:
            %   Lee et al: "Constriction/Spreading Resistance Model for Electronic Packaging"
            %   Simons: "Simple Formulas for Estimating Thermal Spreading Resistance"
            %   Ying et al: "A HEAT SPREADING RESISTANCE MODEL FOR ANISOTROPIC THERMAL
            %   CONDUCTIVITY MATERIALS IN ELECTRONIC PACKAGING"

            switch(nargin)
                case 1
                    error('too few arguments')
                case 2
                    if ~(isscalar(aIn) && aIn>0)
                        error('aIn must be a positive scalar')
                    end
                    if obj.thick == 0
                        rTh = 0;
                    else
                        rTh = obj.thick/(obj.kOp*aIn);
                    end
                    rThThrough = rTh;
                    if obj.thick == 0
                        rTh = 0;
                    end
                    rThSpread = rTh - rThThrough;
                case 3
                    if aIn ~= aOut
                        error(['if aIn != aOut, hEff must be specified'...
                            ' in Order to calculate the thermal resistance'])
                    elseif ~(isscalar(aIn) && aIn>0)
                        error('aIn must be a positive scalar')
                    end
                    if obj.thick == 0
                        rTh = 0;
                    else
                        rTh = obj.thick/(obj.kOp*aIn);
                    end
                    rThThrough = rTh;
                    rThSpread = rTh - rThThrough;
                case 4
                    if ~(isscalar(aIn) && aIn>0)
                        error('aIn must be a positive scalar')
                    elseif ~(isscalar(aOut) && aOut>0)
                        error('aOut must be a positive scalar')
                    elseif ~(isscalar(hEff) && hEff>0)
                        error('hEff must be a positive scalar')
                    end
                    if aIn == aOut
                        if obj.thick == 0
                            rTh = 0;
                        else
                            rTh = obj.thick/(obj.kOp*aIn);
                        end
                        rThThrough = rTh;
                        rThSpread = rTh - rThThrough;
                    else
                        if obj.thick == 0
                            rTh = 1/(hEff*aIn)-1/(hEff*aOut);
                            rThThrough = 0;
                            rThSpread = rTh - rThThrough;
                        else
                            %   calculate equivalent radii of circular substitute area [m]
                            rIn = sqrt(aIn/pi);
                            rOut = sqrt(aOut/pi);
                            eps = rIn/rOut;
                            % choose which layer to use as spreader
                            % calculate the hEff after each layer if spreading only takes place
                            % beforehand
                            hEffArr = zeros(1,obj.n);                    
                            hEffArr(end) = hEff;
                            for i = 1:obj.n-1
                                k_i = obj.layerArray(end-i+1).kOp;
                                thick_i = obj.layerArray(end-i+1).thick;
                                hEffArr(end-i) = 1/(1/hEffArr(end-i+1)+thick_i/k_i);
                            end
                            % calculate the cumulative rTh from top to each layer if
                            % spreading only takes place subsequently
                            rThCum = zeros(1,obj.n);
                            for i = 2:obj.n
                                k_i = obj.layerArray(i-1).kOp;
                                thick_i = obj.layerArray(i-1).thick;
                                rThCum(i) = rThCum(i-1)+thick_i/(k_i*aIn);
                            end
                            % calculate rTh for spreading in different Layers
                            rThArr = zeros(1,obj.n);
                            for i = 1:obj.n
                                hEffL = hEffArr(i);
                                rThL = obj.layerArray(i).thermalLayerResistance(aIn, aOut, hEffL );
                                
                                rThAfter = (1/hEffArr(i)-1/hEff)/aOut;
                                rThBefore = rThCum(i);
                                rThArr(i) = rThBefore + rThL + rThAfter;
                            end
                            rTh = min(rThArr);
                            rThThrough = obj.thick/(obj.kOp*aOut);
                            rThSpread = rTh - rThThrough;
                        end
                    end
                otherwise
                    error('too many arguments')
            end

            if nargout > 3
                error('thermalLayerResistance gives a maximum of three outputs')
            end
            optOutput = [rThSpread, rThThrough];
            for i = 2:nargout
                varargout{i-1} = optOutput(i-1);
            end

        end
        
    end
    
    methods (Access = protected)
        
        function obj = kOpEquiv(obj)
        %kOpEquiv Calculates the equivalent out of plane thermal conductivity
        %   takes an object of class thermalLayerStack as input
        %   and returns the equivalent out of plane thermal conductivity 

            rLam = 0;
            for i = 1:obj.n
                rLam = rLam + obj.layerArray(i).thick /...
                    (obj.thick*obj.layerArray(i).kOp);
            end
            obj.kOp = 1/rLam;
        end
        
        function obj = kIpEquiv(obj)
        %kOpEquiv Calculates the equivalent in plane thermal conductivity
        %   takes an object of class thermalLayerStack as input
        %   and returns the equivalent in plane thermal conductivity 

            kSum = 0;
            for i = 1:obj.n
                kSum = kSum + obj.layerArray(i).thick*obj.layerArray(i).kIp;
            end
            obj.kIp = kSum/obj.thick;

        end
        
    end
    
end


