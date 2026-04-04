classdef HeatsinkGenericClass < HeatsinkClass
    %HeatsinkGenericClass heatsink class for generic heatsinks
    %   Detailed explanation goes here
    
    properties
        heatsinkRef % reference to the used heatsink as defined in 'W:\Technology\Functions\Thermal\db\heatsinks.xlsx'
        hInfTot % heat transfer coefficient of profile with neglect of heatspreading [W/(m^2*K)]
        heatsinkType='generic' % type of used heatsink
    end
    
    methods
        function obj = HeatsinkGenericClass(heatsinkRef)
            obj.heatsinkRef = heatsinkRef;
            pkg load io;
            [~,~,raw] = xlsread(fullfile(thermal_db_path(), 'heatsinks.xlsx'),...
                'generic');
            heatsinkType = 'undefined';
            for i = 3:length(raw(:,1))
                if strcmp(raw{i,1},heatsinkRef)
                    heatsinkType = raw{i,2};
                    obj.hInfTot = raw{i,3};
                end
            end
            if ~strcmp(heatsinkType,obj.heatsinkType)
                error('specified heatsink is not of type generic')
            end
        end
    end
end

