classdef ThermalModelSemi < handle
    %ThermalModelSemi class
    %   Detailed explanation goes here
    
    properties (SetAccess = protected)
        input = ThermalModelSemiInput    % ThermalModelSemiInput object for storing the inputs
        output = ThermalModelSemiOutput   % ThermalModelSemiOutput object for storing the inputs
    end
    
    properties (Access = protected)
        pathCase % define which heat paths are to be considered
                 % 1: heat dissipation only through pcb to bottom, with vias
                 % 2: heat dissipation only through pcb to bottom, no vias
                 % 3: heat dissipation through pcb to bottom and through top of pcb, with vias
                 % 4: heat dissipation through pcb to bottom and through top of pcb, no vias
                 % 5: heat dissipation only through top of pcb
        pcb
        pcbNumVia
        sinkLayerStack
        
        rThCaseFluidBot
        
        rThCaseTopAmbient
        rThCasePcbTopAmbient
        
        tJunction
    end
    
    methods
        
        function obj = ThermalModelSemi(input)
            obj.updateModel(input);
        end
            
        function obj = updateModel(obj, input)
            obj.input = input;
            if ~(isa(obj.input,'ThermalModelSemiInput'))
                error(['input must be of class '...
                    'ThermalModelSemiInput'])
            end
            obj.pathCase = 0;
            obj.pcb = ThermalPcb();
            obj.sinkLayerStack = ThermalLayerStack();
            
            botPath = obj.input.includeBottom;
            topPath = obj.input.includeTop;
            if (obj.input.pcbNumVia > 0 ...
                    || obj.input.pcbEstimateNumVia == 1)
                viaPath = 1;
            else
                viaPath = 0;
            end
            if botPath==1 && viaPath==1 && topPath==0
                obj.pathCase = 1;
            elseif botPath==1 && viaPath==0 && topPath==0
                obj.pathCase = 2;
            elseif botPath==1 && viaPath==1 && topPath==1
                obj.pathCase = 3;
            elseif botPath==1 && viaPath==0 && topPath==1
                obj.pathCase = 4;
            elseif botPath==0 && viaPath==0 && topPath==1
                obj.pathCase = 5;
            else
                error('viaPath can only be considered if botPath is considered.')
            end
            
            obj.checkParameterConsistency();
            for i = 1:size(obj.input.pcbLayerStack,1)
                if length(obj.input.pcbLayerStack(i,:)) == 2
                    layer = ThermalLayer(...
                        obj.input.pcbLayerStack(i,1),...
                        obj.input.pcbLayerStack(i,2));
                elseif length(obj.input.pcbLayerStack(i,:)) == 3
                    layer = ThermalLayer(...
                        obj.input.pcbLayerStack(i,1),...
                        obj.input.pcbLayerStack(i,2),...
                        obj.input.pcbLayerStack(i,3));
                else
                    error('incorrect layer definition')
                end
                obj.pcb.addLayer(layer);
            end
            
            obj.pcb.nVia = obj.input.pcbNumVia;
            obj.pcb.kVia = obj.input.kVia;
            obj.pcb.viaSpacing = obj.input.pcbViaSpacing;
            obj.pcb.aSingleVia = obj.input.areaSingleVia;
            if obj.input.pcbEstimateNumVia == 1
                obj.pcb.estNumVia(obj.input.areaContact);
            end
            obj.pcbNumVia = obj.pcb.nVia;
            
            for i = 1:size(obj.input.sinkLayerStack,1)
%                 layer = ThermalLayer(obj.input.sinkLayerStack(i,1),...
%                     obj.input.sinkLayerStack(i,2));
                if length(obj.input.sinkLayerStack(i,:)) == 2
                    layer = ThermalLayer(...
                        obj.input.sinkLayerStack(i,1),...
                        obj.input.sinkLayerStack(i,2));
                elseif length(obj.input.sinkLayerStack(i,:)) == 3
                    layer = ThermalLayer(...
                        obj.input.sinkLayerStack(i,1),...
                        obj.input.sinkLayerStack(i,2),...
                        obj.input.sinkLayerStack(i,3));
                else
                    error('incorrect layer definition')
                end
                obj.sinkLayerStack.addLayer(layer);
            end
            
            obj.output = ThermalModelSemiOutput();
            obj.output.pcbNumVia = obj.pcbNumVia;
        end
        
        function obj = updateTempJunctionMax(obj, tempJunctionMax)
            obj.input.tempJunctionMax = tempJunctionMax;
            obj.output = ThermalModelSemiOutput();
            obj.output.pcbNumVia = obj.pcbNumVia;
        end
        function obj = updatePLossJunction(obj, pLossJunction)
            obj.input.pLossJunction = pLossJunction;
            obj.output = ThermalModelSemiOutput();
            obj.output.pcbNumVia = obj.pcbNumVia;
        end
        function obj = updateAreaDissBottom(obj, areaDissBottom)
            obj.input.areaDissBottom = areaDissBottom;
            obj.output = ThermalModelSemiOutput();
            obj.output.pcbNumVia = obj.pcbNumVia;
        end
        function obj = updateAreaDissTop(obj, areaDissTop)
            obj.input.areaDissTop = areaDissTop;
            obj.output = ThermalModelSemiOutput();
            obj.output.pcbNumVia = obj.pcbNumVia;
        end
        function obj = updateTempFluidBottom(obj, tempFluidBottom)
            obj.input.tempFluidBottom = tempFluidBottom;
            obj.output = ThermalModelSemiOutput();
            obj.output.pcbNumVia = obj.pcbNumVia;
        end
        function obj = updateTempFluidTop(obj, tempFluidTop)
            obj.input.tempFluidTop = tempFluidTop;
            obj.output = ThermalModelSemiOutput();
            obj.output.pcbNumVia = obj.pcbNumVia;
        end
        function obj = updateHFluidBottom(obj, hFluidBottom)
            obj.input.hFluidBottom = hFluidBottom;
            obj.output = ThermalModelSemiOutput();
            obj.output.pcbNumVia = obj.pcbNumVia;
        end
        function obj = updateHFluidTop(obj, hFluidTop)
            obj.input.hFluidTop = hFluidTop;
            obj.output = ThermalModelSemiOutput();
            obj.output.pcbNumVia = obj.pcbNumVia;
        end
        
        function obj = checkParameterConsistency(obj)
        end
        
%         function obj = calcRthJunctionFluidBot(obj)
%             if ~ismember(obj.pathCase, [1,2,3,4])
%                 error('model is set to not calculate heat dissipation through pcb')
%             end
%             [~ , rThSinkSpread, rThSinkThrough] = thermalLayerResistance(...
%                 obj.sinkLayerStack, obj.input.areaContact,...
%                 obj.input.areaDissBottom, obj.input.hFluidBottom);
%             hEffAtPcb = 1/(...
%                 1/obj.input.hFluidBottom...
%                 + rThSinkThrough*obj.input.areaDissBottom...
%                 + obj.input.thInsContactPcbSink);
%             obj.pcb.pcbThermalResistance(...
%                 obj.input.areaContact,...
%                 obj.input.areaDissBottom,...
%                 hEffAtPcb,...
%                 rThSinkSpread);
%             pcbCache = obj.pcb;
%             
%             rThSpreadInPcb = rThSinkThrough ...
%                 + obj.input.thInsContactPcbSink/obj.input.areaDissBottom...
%                 + obj.pcb.rThPcbTot;
%             obj.pcb.pcbThermalResistance(...
%                 obj.input.areaContact,...
%                 obj.input.areaContact,...
%                 hEffAtPcb,...
%                 rThSinkSpread);
%             rThSpreadInSink = rThSinkThrough + rThSinkSpread ...
%                 + obj.input.thInsContactPcbSink/obj.input.areaContact ...
%                 + obj.pcb.rThPcbTot;
%             rThPcbAndSink = min(rThSpreadInPcb,rThSpreadInSink);
%             if rThSpreadInPcb<rThSpreadInSink
%                 obj.pcb = pcbCache;
%             end
%             obj.rThJunctionFluidBot = ...
%                 1/(obj.input.hFluidBottom * obj.input.areaDissBottom)...
%                 + rThPcbAndSink...
%                 + obj.input.thInsContactPadPcb/obj.input.areaContact...
%                 + obj.input.rThJCBottom;
%             obj.output.rThJunctionFluidBot = obj.rThJunctionFluidBot;
%         end

        function obj = calcRthFluidBot(obj)
            if ~ismember(obj.pathCase, [1,2,3,4])
                error('model is set to not calculate heat dissipation through pcb')
            end
            [~ , rThSinkSpread, rThSinkThrough] = obj.sinkLayerStack.thermalLayerResistance(...
                obj.input.areaContact,...
                obj.input.areaDissBottom, obj.input.hFluidBottom);
            hEffAtPcb = 1/(...
                1/obj.input.hFluidBottom...
                + rThSinkThrough*obj.input.areaDissBottom...
                + obj.input.thInsContactPcbSink);
            obj.pcb.pcbThermalResistance(...
                obj.input.areaContact,...
                obj.input.areaDissBottom,...
                hEffAtPcb,...
                rThSinkSpread);
            pcbCache = obj.pcb;
            
            rThSpreadInPcb = rThSinkThrough ...
                + obj.input.thInsContactPcbSink/obj.input.areaDissBottom...
                + obj.pcb.rThPcbTot;
            obj.pcb.pcbThermalResistance(...
                obj.input.areaContact,...
                obj.input.areaContact,...
                hEffAtPcb,...
                rThSinkSpread);
            rThSpreadInSink = rThSinkThrough + rThSinkSpread ...
                + obj.input.thInsContactPcbSink/obj.input.areaContact ...
                + obj.pcb.rThPcbTot;
            rThPcbAndSink = min(rThSpreadInPcb,rThSpreadInSink);
            if rThSpreadInPcb<rThSpreadInSink
                obj.pcb = pcbCache;
            end
            obj.rThCaseFluidBot = ...
                1/(obj.input.hFluidBottom * obj.input.areaDissBottom)...
                + rThPcbAndSink...
                + obj.input.thInsContactPadPcb/obj.input.areaContact;
            
            obj.output.rThCaseFluidBot =  obj.rThCaseFluidBot;
        end
        
%         function obj = calcRthJunctionFluidTop(obj)
%             if ~ismember(obj.pathCase, [3,4,5])
%                 error('model is set to not calculate heat dissipation to top')
%             end
%             rThJunctionCaseTopAmbient = ...
%                 obj.input.rThJCTop ...
%                 + 1/(obj.input.hFluidTop*obj.input.areaCaseTop);
%             if ~isempty(obj.pcb.pcbLayerStack.layerArray)
%                 topSpreadLayer = obj.pcb.pcbLayerStack.layerArray(1);
%             elseif ~isempty(obj.sinkLayerStack.layerArray)
%                 topSpreadLayer = obj.sinkLayerStack.layerArray(1);
%             else
%                 error('no layer defined for heat spreading at top')
%             end
%             % calculate spreading resistance in top layer from contact area
%             % of semiconductor to top dissipation area. Input area is taken
%             % as half the contact area to account for longer thermal paths
%             % in the middle of the contact area.
%             [~, rThJunctionPcbTopSpread] = thermalLayerResistance(...
%                 topSpreadLayer,...
%                 obj.input.areaContact/2,... 
%                 obj.input.areaDissTop,...
%                 obj.input.hFluidTop);
%             rThJunctionPcbTopAmbient = ...
%                 obj.input.rThJCBottom ...
%                 + obj.input.thInsContactPadPcb/obj.input.areaContact ...
%                 + rThJunctionPcbTopSpread ...
%                 + 1/(obj.input.hFluidTop*(obj.input.areaDissTop-obj.input.areaCaseTop));
%             obj.rThJunctionFluidTop = 1/...
%                 (1/rThJunctionCaseTopAmbient...
%                 + 1/rThJunctionPcbTopAmbient);
%             obj.output.rThJunctionFluidTop = obj.rThJunctionFluidTop;
%         end
        
        function obj = calcRthFluidTop(obj)
            if ~ismember(obj.pathCase, [3,4,5])
                error('model is set to not calculate heat dissipation to top')
            end
            
            obj.rThCaseTopAmbient = ...
                1/(obj.input.hFluidTop*obj.input.areaCaseTop);
            
            if ~isempty(obj.pcb.pcbLayerStack.layerArray)
                topSpreadLayer = obj.pcb.pcbLayerStack.layerArray(1);
            elseif ~isempty(obj.sinkLayerStack.layerArray)
                topSpreadLayer = obj.sinkLayerStack.layerArray(1);
            else
                error('no layer defined for heat spreading at top')
            end
            % calculate spreading resistance in top layer from contact area
            % of semiconductor to top dissipation area. Input area is taken
            % as half the contact area to account for longer thermal paths
            % in the middle of the contact area.
            [~, rThPcbTopSpread] = topSpreadLayer.thermalLayerResistance(...
                obj.input.areaContact/2,... 
                obj.input.areaDissTop,...
                obj.input.hFluidTop);
            obj.rThCasePcbTopAmbient = ...
                rThPcbTopSpread ...
                + obj.input.thInsContactPadPcb/obj.input.areaContact ...
                + 1/(obj.input.hFluidTop*(obj.input.areaDissTop-obj.input.areaCaseTop));
            
            obj.output.rThCaseTopAmbient = obj.rThCaseTopAmbient;
            obj.output.rThCasePcbTopAmbient = obj.rThCasePcbTopAmbient;
        end
        
        function obj = calcTJunction(obj)
            switch obj.pathCase
                case {1, 2}
                    obj.calcRthFluidBot();
                    obj.tJunction = ...
                        obj.input.tempFluidBottom...
                        + obj.rThCaseFluidBot.*sum(obj.input.pLossJunction)...
                        + obj.input.rThJCBottom.*obj.input.pLossJunction;
                case {3, 4}
                    if length(obj.input.pLossJunction)~=1 ...
                        || length(obj.input.rThJCBottom)~=1 ...
                        || length(obj.input.rThJCTop)~=1
                        error('temperature calculation for multiple junctions is not currently implemented for dissipation both on top and bottom')
                    end
                    obj.calcRthFluidBot();
                    obj.calcRthFluidTop();
                    P = obj.input.pLossJunction;
                    Rb = obj.input.rThJCBottom;
                    Rct = obj.rThCaseTopAmbient;
                    Rcbt = obj.rThCasePcbTopAmbient;
                    Rt = obj.input.rThJCTop;
                    Rcb = obj.rThCaseFluidBot;
                    Tft = obj.input.tempFluidTop;
                    Tfb = obj.input.tempFluidBottom;
                    
                    if Rct==Inf
                        Rct = 10^30;
                    end
                    if Rcbt==Inf
                        Rcbt = 10^30;
                    end
                    if Rb==Inf
                        Rb = 10^30;
                    end
                    
                    obj.tJunction = (...
                        P*(Rb*Rt*(Rcb + Rcbt) + Rb*Rct*(Rcb + Rcbt) + Rt*Rcb*Rcbt + Rcb*Rcbt*Rct)...
                        + Tft*(Rb*(Rcb + Rcbt) + Rcb*Rcbt)...
                        + (Rt + Rct)*(Rcb*Tft + Rcbt*Tfb))/(Rb*(Rcb + Rcbt) + Rt*Rcb + Rt*Rcbt + Rcb*Rcbt + Rcb*Rct + Rcbt*Rct);
                case 5
                    if length(obj.input.pLossJunction)~=1 ...
                        || length(obj.input.rThJCBottom)~=1 ...
                        || length(obj.input.rThJCTop)~=1
                        error('temperature calculation for multiple junctions is not currently implemented for dissipation both on top and bottom')
                    end
                    obj.calcRthFluidTop();
                    obj.tJunction = ...
                        obj.input.tempFluidTop...
                        + 1/(1/(obj.rThCaseTopAmbient+obj.input.rThJCTop)+1/(obj.rThCasePcbTopAmbient+obj.input.rThJCBottom))*obj.input.pLossJunction;
                otherwise
                    error('pathCase value out of range')
            end
            obj.output.tJunction = obj.tJunction;
        end
        
        function obj = calcPLossMax(obj)
            outputStored = obj.output;
            pLossJunction = obj.input.pLossJunction;
            
            fun = @(x) obj.pLossOptiFun(x);
            x0L = 00;
            x0U = 10;
            lb = 0;
            ub = 100000;
            maxIter = 1000;
            tolX = 1;
            
            [x1, ~] = minBySQA(fun,x0L,x0U,lb,ub,maxIter,tolX);
            pLossMax = x1;
            
            
%             obj.updatePLossJunction(0);
%             obj.calcTJunction();
%             temp0 = obj.tJunction;
%             obj.updatePLossJunction(1);
%             obj.calcTJunction();
%             temp1 = obj.tJunction;
%             pLossMax = (obj.input.tempJunctionMax-temp0)./(temp1-temp0);

            obj.updatePLossJunction(pLossJunction);
            obj.output = outputStored;
            obj.output.pLossMax = pLossMax;
        end
        
        function obj = calcADissMin(obj)
            % if both top and bottom dissipation are set,
            % the areaDissTop assumed equal to areaDissBottom
            outputStored = obj.output;
            areaDissTop = obj.input.areaDissTop;
            areaDissBottom = obj.input.areaDissBottom;
            
            fun = @(x) obj.areaDissOptiFun(x);
            x0L = obj.input.areaContact;
            x0U = obj.input.areaContact*5;
            lb = obj.input.areaContact;
            ub = 1;
            maxIter = 1000;
            tolX = 1*10^-6;
            
            [x1, ~] = minBySQA(fun,x0L,x0U,lb,ub,maxIter,tolX);
            
%             fun = @(x) obj.areaDissOptiFun(x);
%             lb = obj.input.areaContact;
%             ub = 1;
%             x0 = obj.input.areaContact;
%             % Options
%             opts = optiset('solver','nlopt','solverOpts',nloptset('algorithm','LN_BOBYQA'));
%             
%             Opt = opti('fun',fun,'bounds',lb,ub,'x0',x0,'options',opts);
%             [x1] = solve(Opt);
            
            areaDissipationMin = x1;
            
            tolTemp = 1;
            if obj.tJunction > obj.input.tempJunctionMax+tolTemp
                areaDissipationMin = Inf;
            end
            
            obj.updateAreaDissBottom(areaDissBottom);
            obj.updateAreaDissTop(areaDissTop);
            obj.output = outputStored;
            obj.output.aDissipationMin = areaDissipationMin;
            
        end
        
        function obj = calcHFluidMin(obj)
            % if both top and bottom dissipation are set, hFluidBottom is
            % assumed to be equal hFluidTop
            outputStored = obj.output;
            hFluidBottom = obj.input.hFluidBottom;
            hFluidTop = obj.input.hFluidTop;
            
            fun = @(x) obj.hFluidOptiFun(x);
            x0L = 10;
            x0U = 1000;
            lb = 10^-7;
            ub = 100000;
            maxIter = 1000;
            tolX = 1;
            
            [x1, ~] = minBySQA(fun,x0L,x0U,lb,ub,maxIter,tolX);

            hFluidMin = x1;
            
            tolTemp = 1;
            if obj.tJunction > obj.input.tempJunctionMax+tolTemp
                hFluidMin = Inf;
            end
            
            obj.updateHFluidBottom(hFluidBottom);
            obj.updateHFluidTop(hFluidTop);
            obj.output = outputStored;
            obj.output.hFluidMin = hFluidMin;
            
        end
        
    end
    
    methods  (Access = protected)
        
        function optival = areaDissOptiFun(obj, areaDissipation)
            switch obj.pathCase
                case {1, 2}
                    obj.updateAreaDissBottom(areaDissipation);
                case {3, 4}
                    obj.updateAreaDissBottom(areaDissipation);
                    obj.updateAreaDissTop(areaDissipation);
                case {5}
                    obj.updateAreaDissTop(areaDissipation);
                otherwise
                    error('pathCase value out of range')
            end
            obj.calcTJunction();
            deltaTSquare = max((obj.tJunction - obj.input.tempJunctionMax).^2);
            % preconditioning
            optival = deltaTSquare*areaDissipation^2;
        end
        
        function optival = pLossOptiFun(obj, pLoss)
            obj.updatePLossJunction(pLoss);
            obj.calcTJunction();
            deltaTSquare = max((obj.tJunction - obj.input.tempJunctionMax).^2);
            % preconditioning
            optival = deltaTSquare;
        end
        
        function optival = hFluidOptiFun(obj, hFluid)
            switch obj.pathCase
                case {1, 2}
                    obj.updateHFluidBottom(hFluid);
                case {3, 4}
                    obj.updateHFluidBottom(hFluid);
                    obj.updateHFluidTop(hFluid);
                case {5}
                    obj.updateHFluidTop(hFluid);
                otherwise
                    error('pathCase value out of range')
            end
            obj.calcTJunction();
            deltaTSquare = max((obj.tJunction - obj.input.tempJunctionMax).^2);
            % preconditioning
            optival = deltaTSquare*hFluid^2;
        end
        
    end
    
end

