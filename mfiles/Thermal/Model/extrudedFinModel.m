classdef extrudedFinModel < HeatsinkClass
    %extrudedFinModel Class that describes the thermal behaviour of a
    %extruded profile heat sink
    
    properties
        
        % geometric properties of heatsink
        
        heightHeatsink           % [m]         height of heatsink
        thickHeatsink            % [m]         thickness of heatsink
        thickWall                % [m]         thickness of heatsink wall
        thickFin                 % [m]         thickness of heatsink fin
        widthChannel             % [m]         width of single flowchannel
        depthChannel             % [m]         depth of dlowchannel
        numChannel               % [-]         number of flowchannel in profile
        crossAreaFluid           % [m^2]       crosssectional area of fluid in profile
        
        numBridge
        depthSingleChannel
        
        % geometric properties of object to be cooled (eg TO247)
        
        numHeatedSides           % [-]         number of heated sides (1 or 2)
        widthHotContact          % [m]         dimension of heated contact area in flow direction
        lengthHotContact         % [m]         dimension of heated contact area perpendicular to flow direction
        areaHot                  % [m^2]       heated area
        lengthDiss               % [m]         length of heat dissipation for one component
        widthDiss                % [m]         width of heat dissipation for one component
        areaDiss                 % [m^2]       area of heat dissipation for one component
        lengthDissTot            % [m]         overall length of dissipation for all components
        maxDissipationLength     % [m]         maximum length available for heat dissipation for one component (for example if limited by neighbouring components)
        numComponentsInSeries    % [-]         number of components cooled in series on the same profile
        componentSpacing         % [m]         spacing of components in series (from center to center)
        
        % properties of fluid at operating point
        
        vFluid                   % [m/s]       average velocity of fluid
        Re                       % [-]         Reynolds number
        dHydro                   % [m]         equivalent diameter of rectangular flow channel
        
        % thermal characteristics
        
        TFluidLocMean
        TContact
        TWall
        
        rThFluidLocToIn
        rThContactFluidLoc
        hContactLoc
    end
    
    methods
        function obj = extrudedFinModel(varargin)
            if nargin == 1
                obj.heatsinkRef = varargin;
                pkg load io;
                [~,~,raw] = xlsread(fullfile(thermal_db_path(), 'heatsinks.xlsx'),...
                    'extruded');
                heatsinkType = 'undefined';
                for i = 3:length(raw(:,1))
                    if strcmp(raw{i,1},obj.heatsinkRef)
                        heatsinkType = raw{i,2};
                        obj.materialSink = raw{i,3};
                        obj.rhoSink = raw{i,4};
                        obj.kSink = raw{i,5};
                        obj.specHeatMatSink = raw{i,6};
                        obj.numChannel = raw{i,7};
                        obj.thickHeatsink = raw{i,9};
                        obj.thickWall = raw{i,10};
                        obj.widthChannel = raw{i,12};
                    end
                end
                if ~strcmp(heatsinkType,'extruded')
                    error('specified heatsink is not of type extruded, use appropriate class instead')
                else
                    obj.heatsinkType = 'extruded';
                end
            else
                obj.materialSink = 'generic';
                obj.rhoSink = varargin{1};
                obj.kSink = varargin{2};
                obj.specHeatMatSink = varargin{3};
                obj.numChannel = varargin{4};
                obj.thickHeatsink = varargin{5};
                obj.thickWall = varargin{6};
                obj.widthChannel = varargin{7};
                obj.numBridge = varargin{8};
            end
            obj.heightHeatsink = obj.numChannel*(obj.thickWall+obj.widthChannel)+obj.thickWall;
            obj.thickFin = obj.thickWall;
            obj.depthChannel = obj.thickHeatsink-2*obj.thickWall;
            obj.depthSingleChannel = (obj.depthChannel-obj.numBridge*obj.thickFin)/(obj.numBridge+1);
%             obj.crossAreaFluid = obj.widthChannel*obj.depthChannel*obj.numChannel;
            obj.crossAreaFluid = obj.widthChannel*(obj.depthChannel-obj.numBridge*obj.thickFin)*obj.numChannel;
            obj.dHydro = 2*obj.widthChannel*obj.depthSingleChannel/(obj.widthChannel+obj.depthSingleChannel);
        end
        
        function obj = defineHeatingArrangement(obj,...
                widthHotContact,...
                lengthHotContact,...
                numHeatedSides,...
                maxDissipationLength,...
                numComponentsInSeries,...
                componentSpacing)
            % define the arrangement of the heatsources on the heatsink
            
            obj.maxDissipationLength = maxDissipationLength;
            obj.widthHotContact = widthHotContact;
            obj.lengthHotContact = lengthHotContact;
            obj.areaHot = obj.widthHotContact*obj.lengthHotContact;
            obj.lengthDiss = min(obj.maxDissipationLength, obj.lengthHotContact*1.3);
            if obj.numComponentsInSeries > 1
                obj.lengthDiss = min(obj.lengthDiss, obj.componentSpacing);
            end
            obj.widthDiss = min(obj.heightHeatsink, obj.widthHotContact*1.3);
            
            obj.areaDiss = obj.lengthDiss*obj.widthDiss;
            obj.numHeatedSides = numHeatedSides;
            obj.numComponentsInSeries = numComponentsInSeries;
            obj.componentSpacing = componentSpacing;
            
            obj.lengthDissTot = (obj.numComponentsInSeries-1)*obj.componentSpacing + obj.lengthDiss;
        end
        
        function hFluidLoc = calcHeatTransferFluid(obj, lengthHeatedBefore, TFluidMean, TWallEst)
            %calcHeatTransferFluid calculate the average heat transfer from
            %channel surface to fluid for specified arrangement
            %   literature and source of formulae: VDI-W�rmeatlas, 11.
            %   Auflage, S. 785ff and Fundamentals of Heat and Mass
            %   Transfer, 6. edition, p518ff
            obj.vFluid = obj.flowrate/obj.crossAreaFluid;
            
            kinViskM = obj.fluid.calcKinVisc(TFluidMean);
            kinViskTWall = obj.fluid.calcKinVisc(TWallEst);
            
            obj.Re = obj.vFluid*obj.dHydro/kinViskM;
            
            rhoFluid = obj.fluid.calcDensity(TFluidMean);
            specHeatFluid = obj.fluid.calcSpecHeatCapCp(TFluidMean);
            kFluid = obj.fluid.calcThermalConductivity(TFluidMean);
            
            a = kFluid/(rhoFluid*specHeatFluid);
            PrM = kinViskM/a;
            PrWall = kinViskTWall/a;
            % Pe = obj.vFluid*obj.dHydro/a;
            K = (PrM/PrWall)^0.11;
            % Zeta = (0.79*log(obj.Re)-1.64)^-2;
            
            if obj.Re <= 2300 % laminar flow
                ratioDimDef = [1, 1.43, 2, 3, 4, 8, 100000000];
                valuesNu1 = [3.61, 3.73, 4.12, 4.79, 5.33, 6.49, 8.23];
                ratioSide = max(obj.depthSingleChannel, obj.widthChannel)/min(obj.depthSingleChannel, obj.widthChannel);
                Nu_x_q_1 = interp1(ratioDimDef,valuesNu1,ratioSide,'makima');
                fak2 = 1.302+(Nu_x_q_1-4.364)/(8.23-4.364)*(1.841-1.302);
                Nu_x_q_2 = fak2*(obj.Re*PrM*obj.dHydro/lengthHeatedBefore)^(1/3);
                NuLoc = (Nu_x_q_1^3 + 1 + (Nu_x_q_2-1)^3)^(1/3)*K;
            else % turbulent flow
                f = (0.79*log(obj.Re)-1.64)^-2;
                NuLoc = f/8*(obj.Re-1000)*PrM/(1+12.7*(f/8)^0.5*(PrM^(2/3)-1))*(1+1/3*(obj.dHydro/lengthHeatedBefore)^(2/3));
%                 error('turbulent flow not yet implemented')
                % obj.Nu = (obj.Zeta./8.*(obj.Re-1000).*obj.PrM)./(1+12.7.*(obj.PrM.^(2/3)-1).*sqrt(obj.Zeta./8)).*(1+(obj.dHydro./obj.lengthHeated).^(2/3)).*K;
            end
            hFluidLoc = NuLoc*kFluid/obj.dHydro;
        end
        
        function thermalResistance(obj)
            %calculates the absolut thermal resistance in [K/W] from
            %specified contact surface to fluid with regards to inlet temperature
            
            switch obj.numHeatedSides
                case 1
                    effFinLength = obj.depthChannel+0.5*obj.widthChannel; % regard opposite wall as extension of fin
                case 2
                    effFinLength = obj.depthChannel/2; % regard only half of fin for double sided heatsource
                otherwise
                    error('numHeatedSides must be 1 or 2')
            end
%             if obj.numBridge > 1
%                 effFinLength = effFinLength + 0.5*obj.widthChannel; % correction for bridge
%             end
            areaChannelBaseFluid = obj.widthChannel*obj.lengthDiss;
%             areaFinFluid = effFinLength*obj.lengthDiss*2; % both sides of fin
            switch obj.numHeatedSides
                case 1
                    areaFinFluid = ((obj.depthChannel-obj.numBridge*obj.thickFin)*2+(obj.numBridge+0.5)*2*obj.widthChannel)*obj.lengthDiss;
                case 2
                    areaFinFluid = ((obj.depthChannel-obj.numBridge*obj.thickFin)*2+(obj.numBridge)*2*obj.widthChannel)*obj.lengthDiss/2;
                otherwise
                    error('numHeatedSides must be 1 or 2')
            end
            
            
            crossAreaFin = obj.thickFin*obj.lengthDiss;
            numEvalPoints = floor(obj.lengthDiss*1000*2);
            
            baseLayer = ThermalLayer(obj.thickWall, obj.kSink);
            
            obj.TFluidLocMean = zeros(obj.numComponentsInSeries,1);
            TFluidLocEnd = zeros(obj.numComponentsInSeries,1);
            
            obj.TWall = zeros(obj.numComponentsInSeries,1);
            
            obj.TContact = zeros(obj.numComponentsInSeries,1);
            
            % fluid thermal resistance at local position
            rThFluidFlowLoc = zeros(obj.numComponentsInSeries,1);
            hFluidMeanComp = zeros(obj.numComponentsInSeries,1);
            obj.hContactLoc = zeros(obj.numComponentsInSeries,1);
            obj.rThContactFluidLoc = zeros(obj.numComponentsInSeries,1);
            
            obj.TFluidLocMean(1) = obj.TFluidIn; % inlet temperature as initial guess for fluid temperature
            TFluidLocEnd(1) = obj.TFluidIn; % inlet temperature as initial guess for fluid temperature
            obj.TWall(1) = obj.TFluidIn; % inlet temperature as initial guess for wall temperature
            
            for i = 1:obj.numComponentsInSeries
                rThFluidFlowLoc(i) = obj.calcRthFluidFlow(obj.TFluidLocMean(max(i-1,1)));
                obj.TFluidLocMean(i) = TFluidLocEnd(max(i-1,1)) + rThFluidFlowLoc(i)/2*obj.numHeatedSides*obj.pLossComponent;
                TFluidLocEnd(i) = TFluidLocEnd(max(i-1,1)) + rThFluidFlowLoc(i)*obj.numHeatedSides*obj.pLossComponent;
                obj.TWall(i) = obj.TWall(max(i-1,1)); % previous wall temperature as initial guess for wall temperature
                for k = 1:2
                    hFluidLoc = zeros(numEvalPoints,1);
                    startPos = (i-1)*obj.componentSpacing;
                    for j = 1:numEvalPoints
                        localPos = startPos+j*obj.lengthDiss/numEvalPoints;
                        hFluidLoc(j) = obj.calcHeatTransferFluid(localPos, obj.TFluidLocMean(i), obj.TWall(i));
                    end
                    hFluidMeanComp(i) = mean(hFluidLoc);
%                     rThBaseFluid = 1/(hFluidMeanComp(i)*0.5*areaChannelBaseFluid);
                    rThBaseFluid = 1/(hFluidMeanComp(i)*1*areaChannelBaseFluid);
                    etaFin = finEfficieny(effFinLength, hFluidMeanComp(i), areaFinFluid, obj.kSink, crossAreaFin);
                    rThFinWall = 1/(hFluidMeanComp(i)*areaFinFluid*etaFin);
                    rThChannel = 1/(1/rThBaseFluid +1/rThFinWall);
                    hBase = abs(1/(rThChannel*(areaChannelBaseFluid+crossAreaFin)));
                    rThBaseFluid = 1/(hBase*obj.areaDiss);
                    obj.TWall(i) = obj.TFluidLocMean(i) + rThBaseFluid*obj.pLossComponent;
                end
                [rThContactBase, ~, rThContactBaseThrough] = baseLayer.thermalLayerResistance(obj.areaHot, obj.areaDiss, hBase );
                obj.hContactLoc(i) = 1/(1/(1/(rThContactBaseThrough*obj.areaDiss))+1/(hBase));
                obj.rThContactFluidLoc(i) = rThBaseFluid + rThContactBase;
                obj.TContact(i) = obj.TFluidLocMean(i) + obj.rThContactFluidLoc(i)*obj.pLossComponent;
            end
            
            obj.rThFluidLocToIn = (obj.TFluidLocMean-obj.TFluidIn)./(obj.pLossComponent);
            obj.rThTot = obj.rThFluidLocToIn+obj.rThContactFluidLoc;
        end
    end
end
