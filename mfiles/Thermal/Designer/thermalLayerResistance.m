function [rTh, varargout] = thermalLayerResistance( layer, aIn, aOut, hEff )
%THERMALLAYERRESISTANCE calculates the thermal resistance of a thermalLayer
%or thermalLayerStack object, including thermal spreading effects
%   RTH = THERMALLAYERRESISTANCE(LAYER,AIN,AOUT,HEFF) Calculates the
%   thermal resistance through an object of type thermalLayer or
%   thermalLayerStack, including thermal spreading effects
%   Inputs:
%   layer object of class ThermalLayer or ThermalLayerStack,
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
            if ~(isa(layer,'ThermalLayer')...
                    || isa(layer,'ThermalLayerStack'))
                error(['layer must be of class '...
                    'ThermalLayer or ThermalLayerStack'])
            elseif ~(isscalar(aIn) && aIn>0)
                error('aIn must be a positive scalar')
            end
            thick = layer.thick;
            if thick == 0;
                rTh = 0;
            else
                kOp = layer.kOp;
                rTh = thick/(kOp*aIn);
            end
            rThThrough = rTh;
            if thick == 0;
                rTh = 0;
            end
            rThSpread = rTh - rThThrough;
        case 3
            if aIn ~= aOut
                error(['if aIn != aOut, hEff must be specified'...
                    ' in Order to calculate the thermal resistance'])
            elseif ~(isa(layer,'ThermalLayer')...
                    || isa(layer,'ThermalLayerStack'))
                error(['layer must be of class '...
                    'ThermalLayer or ThermalLayerStack'])
            elseif ~(isscalar(aIn) && aIn>0)
                error('aIn must be a positive scalar')
            end
            thick = layer.thick;
            if thick == 0;
                rTh = 0;
            else
                kOp = layer.kOp;
                rTh = thick/(kOp*aIn);
            end
            rThThrough = rTh;
            rThSpread = rTh - rThThrough;
        case 4
            if ~(isa(layer,'ThermalLayer')...
                    || isa(layer,'ThermalLayerStack'))
                error(['layer must be of class '...
                    'ThermalLayer or ThermalLayerStack'])
            elseif ~(isscalar(aIn) && aIn>0)
                error('aIn must be a positive scalar')
            elseif ~(isscalar(aOut) && aOut>0)
                error('aOut must be a positive scalar')
            elseif ~(isscalar(hEff) && hEff>0)
                error('hEff must be a positive scalar')
            end
            if aIn == aOut
                thick = layer.thick;
                if thick == 0;
                    rTh = 0;
                else
                    kOp = layer.kOp;
                    rTh = thick/(kOp*aIn);
                end
                rThThrough = rTh;
                rThSpread = rTh - rThThrough;
            else
                thick = layer.thick;
                if thick == 0;
                    rTh = 1/(hEff*aIn)-1/(hEff*aOut);
                    rThThrough = 0;
                    rThSpread = rTh - rThThrough;
                else
                    kOp = layer.kOp;
                    kIp = layer.kIp;
                    %   calculate equivalent radii of circular substitute area [m]
                    rIn = sqrt(aIn/pi);
                    rOut = sqrt(aOut/pi);
                    eps = rIn/rOut;
                    % if a layer stack is passed as input, choose which layer to
                    % use as spreader
                    if isa(layer,'ThermalLayerStack')
        %             if 1==0
                        % calculate the hEff after each layer if spreading only takes place
                        % beforehand
                        n = layer.n;
                        hEffArr = zeros(1,n);                    
                        hEffArr(end) = hEff;
                        for i = 1:n-1
                            k_i = layer.layerArray(end-i+1).kOp;
                            thick_i = layer.layerArray(end-i+1).thick;
                            hEffArr(end-i) = 1/(1/hEffArr(end-i+1)+thick_i/k_i);
                        end
                        % calculate the cumulative rTh from top to each layer if
                        % spreading only takes place subsequently
                        rThCum = zeros(1,n);
                        for i = 2:n
                            k_i = layer.layerArray(i-1).kOp;
                            thick_i = layer.layerArray(i-1).thick;
                            rThCum(i) = rThCum(i-1)+thick_i/(k_i*aIn);
                        end
                        % calculate rTh for spreading in different Layers
                        rThArr = zeros(1,n);
                        for i = 1:n
                            thickL = layer.layerArray(i).thick;
                            hEffL = hEffArr(i);
                            kOpL = layer.layerArray(i).kOp;
                            kIpL = layer.layerArray(i).kIp;
                            %   calculate equivalent radii of circular substitute area [m]
                            tau = thickL/rOut;
                            alpha = sqrt(kOpL/kIpL);
                            bi = hEffL*rOut/kOpL;
                            lam = pi + 1/(eps*sqrt(pi));
                            phi = (tanh(lam*tau/alpha)+lam/(alpha*bi)) / ...
                                (1+lam/(alpha*bi)*tanh(lam*tau/alpha));
                            psiMax = eps*tau/sqrt(pi)...
                                + alpha*(1/sqrt(pi)*(1-eps)*phi);
                            rThL = psiMax/(kOpL*rIn*sqrt(pi));
                            rThAfter = (1/hEffArr(i)-1/hEff)/aOut;
                            rThBefore = rThCum(i);
                            rThArr(i) = rThBefore + rThL + rThAfter;
                        end
                        rTh = min(rThArr);
                    else
                        tau = thick/rOut;
                        alpha = sqrt(kOp/kIp);
                        bi = hEff*rOut/kOp;
                        lam = pi + 1/(eps*sqrt(pi));
                        phi = (tanh(lam*tau/alpha)+lam/(alpha*bi)) / ...
                            (1+lam/(alpha*bi)*tanh(lam*tau/alpha));
                        psiMax = eps*tau/sqrt(pi)...
                            + alpha*(1/sqrt(pi)*(1-eps)*phi);
                        rTh = psiMax/(kOp*rIn*sqrt(pi));
                    end
                    rThThrough = thick/(kOp*aOut);
                    rThSpread = rTh - rThThrough;
                end
            end
    end
    
    if nargout > 3
        error('thermalLayerResistance gives a maximum of three outputs')
    end
    optOutput = [rThSpread, rThThrough];
    for i = 2:nargout
        varargout{i-1} = optOutput(i-1);
    end

end


