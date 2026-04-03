classdef SCComponentModel < handle
    %SCComponentModel Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        
        scData = {} % struct array for data of semiconductors
        
        scLossmodel = {} % struct array with Lossmodels for all semiconductors within component
        
        thermalModel % thermal model for component
        
        % electricalModelComponent % electrical model of the component (maybe...)
        % electricalModelSC % electrical model of the individual elements of the component (maybe...)
        
        % some of these inputs might be calculated by property
        % electricalModelComponent 
        t     % [s] time vector
        iArr  % [A] array of current vectors corresponding to t for each element of the component
        
        pLossMeanComp % mean power loss of the component
        pLossMeanArr % array of mean power loss of the individual elements
        TjArr % array of juncton temperature of the individual elements
        
    end
    
    methods
        function obj = SCComponentModel(thermalInputSink, varargin)
            % thermalInputSink : ThermalModelSemiInput for part of thermal that is outside the semiconductor (pcb, heatsink, fluid, ...
            % varagin : references for all copacked semiconductors (semi1_ref, semi1_ref, ...)
            
            % parse semiconductor data (in future read directly from
            % database with function parseSemiData(semiRef)
            % for semiRef = varargin
            %     opj.parseSemiData(semiRef)
            % end
            semi1data = load(varargin{1});      % IGBT model
            obj.scData(1).Type = 'IGBT';
            obj.scData(1).table1_I = semi1data.Id2Vce25C(1:end,1);
            obj.scData(1).table1_Tj = [25; 125; 150];
            obj.scData(1).table1_V = [semi1data.Id2Vce25C(1:end,2),semi1data.Id2Vce125C(1:end,2),semi1data.Id2Vce150C(1:end,2)];
            obj.scData(1).rThJC = 0.31;
            obj.scData(1).ThermalContactArea = 300*10^-6;
            semi2Data = load(varargin{2});    % diode model
            obj.scData(2).Type = 'diode';
            obj.scData(2).table1_I = semi2Data.If2Vd25C(1:end,1);
            obj.scData(2).table1_Tj = [25; 125; 150];
            obj.scData(2).table1_V = [semi2Data.If2Vd25C(1:end,2),semi2Data.If2Vd125C(1:end,2),semi2Data.If2Vd150C(1:end,2)];
            obj.scData(2).rThJC = 1.11;
            obj.scData(2).ThermalContactArea = 300*10^-6;
            % setting up loss models for semiconductors
            for n = 1:length(obj.scData)
                obj.scLossmodel{n} = SemiconductorLossModel(obj.scData(n));
            end
            
            thermalModelInput = thermalInputSink;
            thermalModelInput.areaContact = obj.scData(1).ThermalContactArea;
            for n = 1:length(obj.scData)
                thermalModelInput.rThJCBottom(n) = obj.scData(n).rThJC;
            end
            obj.thermalModel = ThermalModelSemi(thermalModelInput);
            
        end
        
        function obj = updateOperatingParameters(obj, t, iArr)
            %updateOperatingParameters set parameters for operation
            %   Detailed explanation goes here
            obj.t = t;
            obj.iArr = iArr;
            fun = @(x) obj.operatingPointObjective(x);
%             PLossMeanEstArr = zeros(1,length(obj.scLossmodel));
%             TjEst = ones(1,length(obj.scLossmodel)).*100;
%             for n = 1:length(obj.scLossmodel)
%                 obj.scLossmodel{n}.updateOperatingParameters(TjEst(n), obj.t, obj.iArr(n,:));
%                 obj.scLossmodel{n}.calculateLoss();
%                 PLossMeanEstArr(1,n) = obj.scLossmodel{n}.meanLoss;
%             end
            TjEstArr = ones(length(obj.scLossmodel),1).*obj.thermalModel.input.tempFluidBottom;
            x0 = TjEstArr;
            ydata = zeros(length(obj.scLossmodel),1);
            lb = x0;
            ub = ones(length(obj.scLossmodel),1).*140;
            absTol = 1;
%             opts = optiset('solver','nlopt','solverOpts',nloptset('algorithm','LN_SBPLX'),'tolafun',absTol);
%             opts = optiset('solver','nl2sol','tolafun',absTol);
            opts = optiset('solver','mkltrnls','tolafun',absTol);
            Opt = opti('fun',fun,'ydata',ydata,'bounds',lb,ub,'x0',x0,'options',opts);
            [x1] = solve(Opt);
            TjArrEst = x1';
%             for n = 1:length(obj.scLossmodel)
%                 obj.pLossMeanArr(n) = obj.scLossmodel{n}.meanLoss;
%             end
            for n = 1:length(obj.scLossmodel)
%                 obj.scLossmodel{n}.updateOperatingParameters(TjArrEst(n), obj.t, obj.iArr(n,:));
%                 obj.scLossmodel{n}.calculateLoss();
                obj.scLossmodel{n}.calculateLoss(TjArrEst(n), obj.t, obj.iArr(n,:));
                obj.pLossMeanArr(n) = obj.scLossmodel{n}.meanLoss;
            end
            obj.thermalModel.updatePLossJunction(obj.pLossMeanArr);
            obj.thermalModel.calcTJunction();
            obj.TjArr = obj.thermalModel.output.tJunction;
            obj.pLossMeanComp = sum(obj.pLossMeanArr);
        end
        
        function obj = changeAreaDissBottom(obj, areaDissBottom)
            obj.thermalModel.updateAreaDissBottom(areaDissBottom);
            if isnumeric(obj.pLossMeanComp)
                obj.updateOperatingParameters(obj.t, obj.iArr)
            end
        end
        
    end
    
    methods (Access = protected)
        
        function optival = operatingPointObjective(obj, TjEstArr)
%             PLossMeanEstArr = PLossMeanEstArr'
%             obj.thermalModel.updatePLossJunction(PLossMeanEstArr);
%             obj.thermalModel.calcTJunction();
%             Tj = obj.thermalModel.output.tJunction
%             PLossMeanArr = zeros(1,length(obj.scLossmodel));
%             for n = 1:length(obj.scLossmodel)
%                 obj.scLossmodel{n}.updateOperatingParameters(Tj(n), obj.t, obj.iArr(n));
%                 obj.scLossmodel{n}.calculateLoss();
%                 PLossMeanArr(n) = obj.scLossmodel{n}.meanLoss;
%             end
%             
%             optival = sum((PLossMeanEstArr-PLossMeanArr).^2);
            
            

            TjEstArr = TjEstArr';
%             iArr = obj.iArr
            for n = 1:length(obj.scLossmodel)
%                 obj.scLossmodel{n}.updateOperatingParameters(TjEstArr(n), obj.t, obj.iArr(n,:));
%                 obj.scLossmodel{n}.calculateLoss();
                obj.scLossmodel{n}.calculateLoss(TjEstArr(n), obj.t, obj.iArr(n,:));
                pLossMeanArrEst(n) = obj.scLossmodel{n}.meanLoss;
            end
            obj.thermalModel.updatePLossJunction(pLossMeanArrEst);
            obj.thermalModel.calcTJunction();
            Tj = obj.thermalModel.output.tJunction;
            
%             optival = (TjEstArr-Tj)'.^2
            optival = (TjEstArr-Tj)';
        end
        
        function obj = parseSemiData(obj,semiRef)
            pass
        end
        
    end
    
end

