function result = cmd_tim_lookup(parsed)
    % cmd_tim_lookup - look up thermal interface material from database
    % Usage: thermal_cli.m tim-lookup [--list] [--search <keyword>]

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m tim-lookup [--list] [--search <keyword>]\n');
        fprintf('Looks up TIM properties from db/Thermal_Interface_Materials.xlsx.\n');
        fprintf('  --list      List all available TIMs\n');
        fprintf('  --search    Filter by keyword in manufacturer/type/description\n');
        result = struct();
        return;
    end

    pkg load io;
    [~, ~, raw] = xlsread(fullfile(thermal_db_path(), 'Thermal_Interface_Materials.xlsx'));

    % Headers in row 1, data starts row 3
    headers = raw(1, :);
    n_rows = size(raw, 1);

    result.entries = {};
    count = 0;

    for i = 3:n_rows
        manufacturer = '';
        if ~isempty(raw{i, 2}) && ischar(raw{i, 2})
            manufacturer = raw{i, 2};
        end
        tim_type = '';
        if ~isempty(raw{i, 3}) && ischar(raw{i, 3})
            tim_type = raw{i, 3};
        end
        description = '';
        if ~isempty(raw{i, 4}) && ischar(raw{i, 4})
            description = raw{i, 4};
        end

        % Filter by search keyword
        if isfield(parsed, 'search')
            keyword = lower(parsed.search);
            combined = lower([manufacturer ' ' tim_type ' ' description]);
            if isempty(strfind(combined, keyword))
                continue;
            end
        end

        count = count + 1;

        % Extract thermal properties
        k_val = raw{i, 9};
        rth_area_no_press = raw{i, 10};
        rth_area_35N = raw{i, 11};
        thickness = raw{i, 6};

        if isfield(parsed, 'list') || isfield(parsed, 'search')
            fprintf('%-20s %-25s', manufacturer, tim_type);
            if isnumeric(k_val) && ~isempty(k_val)
                fprintf('  k=%.2f W/(m*K)', k_val);
            end
            if isnumeric(rth_area_no_press) && ~isempty(rth_area_no_press)
                fprintf('  Rth*A=%.1f mm2K/W', rth_area_no_press);
            end
            fprintf('\n');
        end

        entry.manufacturer = manufacturer;
        entry.type = tim_type;
        entry.description = description;
        entry.k = k_val;
        entry.rth_area_no_pressure = rth_area_no_press;
        entry.rth_area_35N = rth_area_35N;
        entry.thickness = thickness;
        result.entries{count} = entry;
    end

    fprintf('total=%d\n', count);
    result.count = count;
end
