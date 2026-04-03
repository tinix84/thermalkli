function [heatsink] = heatsinkFactory(heatsinkRef)
    %heatsinkFactory factory function that returns a heatsink Object of the
    %appropriate type
    %   Detailed explanation goes here

    pkg load io;
    [~,~,raw] = xlsread(fullfile(thermal_db_path(), 'heatsinks.xlsx'),...
        'listOfHeatsinks');
    heatsinkType = 'undefined';
    for i = 3:length(raw(:,1))
        if strcmp(raw{i,1},heatsinkRef)
            heatsinkType = raw{i,2};
        end
    end

    switch heatsinkType
        case 'generic'
            heatsink = HeatsinkGenericClass(heatsinkRef);
        case 'extruded'
            heatsink = extrudedFinModel(heatsinkRef);
        otherwise
            error('undefined heatsink or unknown heatsink type')
    end

end

