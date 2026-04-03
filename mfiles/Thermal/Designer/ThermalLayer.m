classdef ThermalLayer
    %THERMALLAYER Class for thermal layer objects
    %   obj = THERMALLAYER(thick,kOp,kIp) creates an object for a thermal
    %   layer with according properties for thickness and thermal
    %   conductivities
    
    properties
        thick     % thickness of layer                [m]
        kOp       % Thermal conductivity out of plane [K*m*W^-1]
        kIp       % Thermal conductivity in plane     [K*m*W^-1]
    end
    
    methods
        function obj = ThermalLayer(t, kOp, kIp)
            if ~(isscalar(t) && t>=0)
                error('t must be a positive scalar')
            end
            obj.thick = t;
            switch(nargin)
                case 1
                    error('too few arguments')
                case 2
                    if ~(isscalar(kOp) && kOp>=0)
                        error('kOp must be a positive scalar')
                    end
                    obj.kOp = kOp;
                    obj.kIp = kOp;
                case 3
                    if ~(isscalar(kOp) && kOp>=0)
                        error('kOp must be a positive scalar')
                    elseif ~(isscalar(kIp) && kIp>=0)
                        error('kIp must be a positive scalar')
                    end
                    obj.kOp = kOp;
                    obj.kIp = kIp;
            end
        end
        
        function [rTh, varargout] = thermalLayerResistance( obj, aIn, aOut, hEff )
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
                            % calculate equivalent radii of circular substitute area [m]
                            rIn = sqrt(aIn/pi);
                            rOut = sqrt(aOut/pi);
                            eps = rIn/rOut;
                            tau = obj.thick/rOut;
                            alpha = sqrt(obj.kOp/obj.kIp);
                            bi = hEff*rOut/obj.kOp;
                            lam = pi + 1/(eps*sqrt(pi));
                            phi = (tanh(lam*tau/alpha)+lam/(alpha*bi)) / ...
                                (1+lam/(alpha*bi)*tanh(lam*tau/alpha));
                            psiMax = eps*tau/sqrt(pi)...
                                + alpha*(1/sqrt(pi)*(1-eps)*phi);
                            rTh = psiMax/(obj.kOp*rIn*sqrt(pi));
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
        
        function [hInf, varargout] = thermalResistanceCalc( obj, aIn, aOut, hEff )
            hInf = obj.kOp/obj.thick;
            switch(nargin)
                case 1
                    rThSpread = NaN;
                    rTh = NaN;
                case 2
                    if ~(isscalar(aIn) && aIn>0)
                        error('aIn must be a positive scalar')
                    end
                    rTh = 1/(hInf*aIn);
                    rThSpread = 0;
                case 3
                    if aIn ~= aOut
                        error(['if aIn != aOut, hEff must be specified'...
                            ' in Order to calculate the thermal resistance'])
                    elseif ~(isscalar(aIn) && aIn>0)
                        error('aIn must be a positive scalar')
                    end
                    rTh = 1/(hInf*aIn);
                    rThSpread = 0;
                case 4
                    if ~(isscalar(aIn) && aIn>0)
                        error('aIn must be a positive scalar')
                    elseif ~(isscalar(aOut) && aOut>0)
                        error('aOut must be a positive scalar')
                    elseif ~(isscalar(hEff) && hEff>0)
                        error('hEff must be a positive scalar')
                    end
                    if aIn == aOut
                        rTh = 1/(hInf*aIn);
                        rThSpread = 0;
                    else
                        if obj.thick == 0
                            rThSpread = 1/(hEff*aIn)-1/(hEff*aOut);
                            rTh = rThSpread;
                        else
                            % calculate equivalent radii of circular substitute area [m]
                            rIn = sqrt(aIn/pi);
                            rOut = sqrt(aOut/pi);
                            eps = rIn/rOut;
                            tau = obj.thick/rOut;
                            alpha = sqrt(obj.kOp/obj.kIp);
                            bi = hEff*rOut/obj.kOp;
                            lam = pi + 1/(eps*sqrt(pi));
                            phi = (tanh(lam*tau/alpha)+lam/(alpha*bi)) / ...
                                (1+lam/(alpha*bi)*tanh(lam*tau/alpha));
                            psiMax = eps*tau/sqrt(pi)...
                                + alpha*(1/sqrt(pi)*(1-eps)*phi);
                            rTh = psiMax/(obj.kOp*rIn*sqrt(pi));
                            rThSpread = rTh - 1/(hInf*aOut);
                        end
                    end
                otherwise
                    error('too many arguments')
            end
            
            if nargout > 3
                error('thermalLayerResistance gives a maximum of three outputs')
            end
            optOutput = [rThSpread, rTh];
            for i = 2:nargout
                varargout{i-1} = optOutput(i-1);
            end
        end
    end
    
end
