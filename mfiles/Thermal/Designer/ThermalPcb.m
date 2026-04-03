classdef ThermalPcb < handle
    %THERMALPCB class for calculating and storing the thermal properties
    %and structure of a pcb, including thermal vias
    %   Detailed explanation goes here
    
    properties
        pcbLayerStack = ThermalLayerStack;
        thick         % total thickness of layer stack                  [m]
%         aHeat=0       % area of heat source in contact with pcb     [m^2]
%         aCool=0       % area over which heat is dissipated          [m^2]
        nVia          % number of thermal vias                        [m^2]
        viaSpacing
        aSingleVia    % cross section of sinlge via                   [m^2]
        kVia          % thermal conductivity of via material     [K*m*W^-1]
        aAllVia       % combined cross section of all via             [m^2]
        rThAllVia     % thermal resistance of all vias             [W*K^-1]
        rThWithoutVia % thermal resistance of pcb with no via      [W*K^-1]
        rThViaSection    %                                         [W*K^-1]
        rThBypassVia  % thermal resistance through pcb around via  [W*K^-1]
        rThLastLayerSpread % spreading resistance of last layer    [W*K^-1]
        rThPcbTot     % estimated total thermal resistance of pcb  [W*K^-1]
    end
    
    methods
      function obj = ThermalPcb
          obj.pcbLayerStack = ThermalLayerStack();
          obj.thick = 0;
          obj.nVia = 0;
          obj.viaSpacing = 0;
          obj.aSingleVia = 0;
          obj.kVia = 0;
          obj.aAllVia = 0;
          obj.rThAllVia = 0;
          obj.rThWithoutVia = 0;
          obj.rThBypassVia = 0;
          obj.rThViaSection = 0;
          obj.rThLastLayerSpread = 0;
          obj.rThPcbTot = 0;
      end  
      function obj = addLayer(obj, varargin)
          for i = 1:length(varargin)
              obj.pcbLayerStack.addLayer(varargin{i});
          end
          obj.thick = obj.pcbLayerStack.thick;
      end
      function obj = defineVia(obj, rOuter, tPlating, viaSpacing)
          obj.aSingleVia = pi*(rOuter.^2 - (rOuter-tPlating).^2);
          obj.viaSpacing = viaSpacing;
      end
      function obj = estNumVia(obj, aHeat)
          obj.nVia = floor(...
              aHeat/(obj.viaSpacing*(obj.viaSpacing/2*sqrt(3))));
      end
      function obj = rThViaCalc(obj)
          if obj.aSingleVia <= 0
              error('Via cross section must first be defined')
          elseif obj.nVia <= 0
              error('Number of vias must first be defined')
          elseif obj.kVia <= 0
              error('Conductivity of via material must first be defined')
          end
          viaLayer = ThermalLayer(obj.thick, obj.kVia);
          obj.aAllVia = obj.nVia*obj.aSingleVia;
          obj.rThAllVia = thermalLayerResistance(viaLayer,...
              obj.aAllVia);
      end
      function obj = pcbThermalResistance(obj,aHeat,aCool,hEff,rThSpreadAfter)
          if obj.nVia == 0
              obj.rThWithoutVia = thermalLayerResistance(...
              obj.pcbLayerStack, aHeat, aCool, hEff);
              obj.rThPcbTot = obj.rThWithoutVia;
          else
              if aCool < aHeat
                  error('If vias are defined, aCool can not be smaller than aHeat')
              end
              rThAHeatWithoutVia = thermalLayerResistance(...
                  obj.pcbLayerStack, aHeat);
              obj.rThViaCalc();
              rThAHeatViaCutout = thermalLayerResistance(...
                  obj.pcbLayerStack, aHeat-obj.aAllVia);
              obj.rThViaSection = 1/(1/obj.rThAllVia + 1/(rThAHeatViaCutout));
              if aCool > aHeat
                  obj.rThWithoutVia = thermalLayerResistance(...
                      obj.pcbLayerStack, aHeat, aCool, hEff);
                  obj.rThBypassVia = 1/...
                      (1/obj.rThWithoutVia-1/rThAHeatWithoutVia);
                  [~, obj.rThLastLayerSpread] = ...
                      thermalLayerResistance(...
                      obj.pcbLayerStack.layerArray(end), aHeat, aCool, hEff);
                  if nargin > 4
                      rThViaSpread = min(rThSpreadAfter, obj.rThLastLayerSpread);
                  else
                      rThViaSpread =  obj.rThLastLayerSpread;
                  end
                  obj.rThPcbTot = 1/(...
                        1/obj.rThBypassVia...
                        + 1/(obj.rThViaSection+rThViaSpread));
              else
                  obj.rThPcbTot = obj.rThViaSection;
              end
          end
          
      end
    end
end
