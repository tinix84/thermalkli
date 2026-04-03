classdef AreaPowerLossParOpt < handle
    %UNTITLED9 Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        componentList
        nComp
        areaArr
        minAreaArr
        maxAreaArr
        areaTot
        areaFree
        pLossArr
        pLossTot
        tJMaxArr
        tJMax
    end
    
    methods
        function obj = AreaPowerLossParOpt(varargin)
            %UNTITLED9 Construct an instance of this class
            %   Detailed explanation goes here
            obj.componentList = varargin;
            obj.nComp = length(obj.componentList);
%             for i = 1:obj.nComp
%                 obj.componentList{i} = varargin{i};
%             end
        end
        
        function obj = pLossAreaDistrOpt(obj, areaTot)
            % find how the available area has to be distributed between the
            % individual components to minimize power loss
            obj.areaTot = areaTot;
            fun = @(x) obj.pLossAreaDistribution(x);
            areaWeightingEst = ones(obj.nComp,1)./obj.nComp;
            x0 = areaWeightingEst;
            for i = 1:obj.nComp
                obj.minAreaArr(i) = obj.componentList{i}.thermalModel.input.areaContact;
            end
            for i = 1:obj.nComp
                obj.maxAreaArr(i) = obj.areaTot - sum(obj.minAreaArr) + obj.minAreaArr(i);
            end
            obj.areaFree = obj.areaTot-sum(obj.minAreaArr);
            lb = zeros(obj.nComp,1);
            ub = ones(obj.nComp,1);
%             opts = optiset('solver','ipopt');
            opts = optiset('solver','nlopt','solverOpts',nloptset('algorithm','LN_SBPLX'));
            Opt = opti('fun',fun,'bounds',lb,ub,'x0',x0,'options',opts);
            [x1] = solve(Opt);
            obj.areaArr = obj.minAreaArr+x1'./sum(x1).*obj.areaFree;
            for i = 1:obj.nComp
                obj.componentList{i}.changeAreaDissBottom(obj.areaArr(i));
                obj.pLossArr(i) = obj.componentList{i}.pLossMeanComp;
            end
            obj.pLossTot = sum(obj.pLossArr);
        end
        
        function pLossTot = pLossAreaDistribution(obj,areaWeighting)
            %METHOD1 Summary of this method goes here
            %   Detailed explanation goes here
            obj.areaArr = obj.minAreaArr+areaWeighting'./sum(areaWeighting).*obj.areaFree;
            for i = 1:obj.nComp
                obj.componentList{i}.changeAreaDissBottom(obj.areaArr(i));
                obj.pLossArr(i) = obj.componentList{i}.pLossMeanComp;
            end
            pLossTot = sum(obj.pLossArr);
            obj.pLossTot = pLossTot;
        end
        
        
        function obj = tJMaxAreaDistrOpt(obj, areaTot)
            % find how the available area has to be distributed between the
            % individual components to minimize power loss
            obj.areaTot = areaTot;
            fun = @(x) obj.tJMaxAreaDistribution(x);
            areaWeightingEst = ones(obj.nComp,1)./obj.nComp;
            x0 = areaWeightingEst;
            for i = 1:obj.nComp
                obj.minAreaArr(i) = obj.componentList{i}.thermalModel.input.areaContact;
            end
            for i = 1:obj.nComp
                obj.maxAreaArr(i) = obj.areaTot - sum(obj.minAreaArr) + obj.minAreaArr(i);
            end
            obj.areaFree = obj.areaTot-sum(obj.minAreaArr);
            lb = zeros(obj.nComp,1);
            ub = ones(obj.nComp,1);
%             opts = optiset('solver','ipopt');
            opts = optiset('solver','nlopt','solverOpts',nloptset('algorithm','LN_SBPLX'));
            Opt = opti('fun',fun,'bounds',lb,ub,'x0',x0,'options',opts);
            [x1] = solve(Opt);
            obj.areaArr = obj.minAreaArr+x1'./sum(x1).*obj.areaFree;
            for i = 1:obj.nComp
                obj.componentList{i}.changeAreaDissBottom(obj.areaArr(i));
                obj.tJMaxArr(i) = max(obj.componentList{i}.TjArr);
            end
            obj.tJMax = max(obj.tJMaxArr(:));
        end
        
        function tJMax = tJMaxAreaDistribution(obj,areaWeighting)
            %METHOD1 Summary of this method goes here
            %   Detailed explanation goes here
            obj.areaArr = obj.minAreaArr+areaWeighting'./sum(areaWeighting).*obj.areaFree;
            for i = 1:obj.nComp
                obj.componentList{i}.changeAreaDissBottom(obj.areaArr(i));
                obj.tJMaxArr(i) = max(obj.componentList{i}.TjArr);
            end
            tJMax = max(obj.tJMaxArr(:));
            obj.tJMax = tJMax;
        end
        
%         function [areaTot,pLossTot] = areaPlossParetoOpt(obj, wArea,wPloss)
%             areaWeighting = [1,1];
%             fun = @(x) obj.areaPlossObjective(x, areaWeighting, wArea,wPloss);
%         end
%         
%         function objVal = areaPlossObjective(obj, area, areaWeighting, wArea,wPloss)
%             pLoss = 0;
%             for i = 1:obj.nComp
%                 obj.componentList{i}.changeAreaDissBottom(area/obj.nComp); % adjust for areaArr
%                 pLoss = pLoss + obj.componentList{i}.pLossMeanComp;
%             end
%             obj.areaDistribution(areaWeighting);
%             objVal = area*wArea + pLoss*wPloss;
%         end
        
    end
end

