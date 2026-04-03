classdef SemiconductorLossModel < handle
    %SemiconductorLossModel Loss model for semiconductors
    %   Detailed explanation goes here
    
    properties
        % inputs
        scData   % data for semiconductor in use
        t                   % 
        i                   % current [A]
        Tj                  % junction temperature [K]
    end
    
    % outputs
    properties (SetAccess = protected)
        conductionLoss
        meanConductionLoss
        switchingLoss
        meanSwitchingLoss
        meanLoss
    end
    
    methods
        function obj = SemiconductorLossModel(scData)
            %SemiconductorLossModel Construct an instance of this class
            %   Detailed explanation goes here
            obj.scData = scData;
        end
        
%         function obj = updateOperatingParameters(obj, Tj, t, i)
%             %updateOperatingParameters set parameters for operation
%             %   Detailed explanation goes here
%             obj.t = t;
%             obj.i = i;
%             obj.Tj = Tj;
%             obj.conductionLoss = [];
%             obj.switchingLoss = [];
%             obj.meanConductionLoss = [];
%             obj.meanSwitchingLoss = [];
%             obj.meanLoss = [];
%         end
        
        function obj = calculateLoss(obj, Tj, t, i)
            %calculateLoss function to calculate losses
            %losses
            %   Detailed explanation goes here
            
            obj.t = t;
            obj.i = i;
            obj.Tj = Tj;
            
            obj.calculateConductionLoss();
            obj.calculateSwitchingLoss();
            obj.calculateMeanLoss();
            
        end
        
    end
    
    methods (Access = protected)

        function obj = calculateConductionLoss(obj)
            %calculateConductionLoss function to calculate conduction
            %losses
            %   Detailed explanation goes here
            
            % here be calculation formulas
            % obj.conductionLoss = ...;
            obj.conductionLoss = ...
                obj.i .* ...
                interp2(obj.scData.table1_Tj,...
                        obj.scData.table1_I,...
                        obj.scData.table1_V,...
                        obj.Tj,...
                        obj.i,...
                        'linear',...
                        0)';

%             obj.conductionLoss = ...
%                 obj.i .* ...
%                 interp2(obj.scData.table1_Tj,...
%                         obj.scData.table1_I,...
%                         obj.scData.table1_V,...
%                         obj.Tj,...
%                         obj.i,...
%                         'makima')';
%             obj.conductionLoss = ...
%                 obj.i .* ...
%                 interp2(obj.scData.table1_Tj,...
%                         obj.scData.table1_I,...
%                         obj.scData.table1_V,...
%                         obj.Tj,...
%                         obj.i,...
%                         'spline')';
%             obj.conductionLoss = ...
%                 obj.i .* ...
%                 interp2(obj.scData.table1_Tj,...
%                         obj.scData.table1_I,...
%                         obj.scData.table1_V,...
%                         obj.Tj,...
%                         obj.i,...
%                         'linear',...
%                         max(obj.scData.table1_V(:)))';
            obj.meanConductionLoss = 3 * sum(obj.conductionLoss)/length(obj.t);
        end
        
        function obj = calculateSwitchingLoss(obj)
            %calculateSwitchingLoss function to calculate switching
            %losses
            %   Detailed explanation goes here
            
            % here be calculation formulas
            % obj.switchingLoss = ...;
            % 
            % switch obj.scData.Type
            %     case 'diode'
            %         obj.switchingLoss = ...;
            %     case 'IGBT'
            %         obj.switchingLoss = ...;
            % end
            
            obj.switchingLoss = 0;
            obj.meanSwitchingLoss = 3 * sum(obj.switchingLoss)/obj.t(end);
        end
        
        function obj = calculateMeanLoss(obj)
            %calculateMeanLoss function to calculate meanLoss
            %losses from conductin losses and switching losses
            %   Detailed explanation goes here
            
            obj.meanLoss = obj.meanConductionLoss + obj.meanSwitchingLoss;
        end
        
    end
    
end

