function result = cmd_compare_femm(parsed)
    % cmd_compare_femm - compare analytical CSV results against FEMM CSV results
    % Usage: thermal_cli.m compare-femm --analytical <csv> --femm <csv>
    %
    % Analytical CSV format: point,value,unit
    % FEMM CSV format:       point,x,y,temperature

    if isfield(parsed, 'help') && parsed.help
        fprintf('Usage: thermal_cli.m compare-femm --analytical <csv> --femm <csv>\n');
        fprintf('Compares analytical CSV (point,value,unit) with FEMM CSV (point,x,y,temperature).\n');
        result = struct();
        return;
    end

    if ~isfield(parsed, 'analytical')
        fprintf(2, 'Error: --analytical <csv> is required\n');
        result = struct();
        return;
    end

    if ~isfield(parsed, 'femm')
        fprintf(2, 'Error: --femm <csv> is required\n');
        result = struct();
        return;
    end

    % Read analytical CSV (format: point,value,unit)
    fid_a = fopen(parsed.analytical, 'r');
    if fid_a < 0
        fprintf(2, 'Error: cannot open analytical CSV: %s\n', parsed.analytical);
        result = struct();
        return;
    end
    fgetl(fid_a);  % skip header
    analytical = struct();
    while ~feof(fid_a)
        line = fgetl(fid_a);
        if ischar(line) && ~isempty(strtrim(line))
            parts = strsplit(line, ',');
            name = strtrim(parts{1});
            val = str2double(parts{2});
            key = strrep(strrep(name, ' ', '_'), '-', '_');
            analytical.(key) = val;
        end
    end
    fclose(fid_a);

    % Read FEMM CSV (format: point,x,y,temperature)
    fid_f = fopen(parsed.femm, 'r');
    if fid_f < 0
        fprintf(2, 'Error: cannot open FEMM CSV: %s\n', parsed.femm);
        result = struct();
        return;
    end
    fgetl(fid_f);  % skip header
    femm_data = struct();
    while ~feof(fid_f)
        line = fgetl(fid_f);
        if ischar(line) && ~isempty(strtrim(line))
            parts = strsplit(line, ',');
            name = strtrim(parts{1});
            temp = str2double(parts{end});
            key = strrep(strrep(name, ' ', '_'), '-', '_');
            femm_data.(key) = temp;
        end
    end
    fclose(fid_f);

    % Print comparison table
    fprintf('%-25s %15s %15s %12s\n', 'Point', 'Analytical', 'FEMM', 'Deviation');
    fprintf('%s\n', repmat('-', 1, 70));

    result.comparisons = {};
    f_fields = fieldnames(femm_data);
    a_fields = fieldnames(analytical);

    for i = 1:length(f_fields)
        fname = f_fields{i};
        femm_val = femm_data.(fname);
        matched = false;
        for j = 1:length(a_fields)
            if ~isempty(strfind(a_fields{j}, fname)) || ~isempty(strfind(fname, a_fields{j}))
                ana_val = analytical.(a_fields{j});
                if ana_val ~= 0
                    dev = abs(femm_val - ana_val) / abs(ana_val) * 100;
                else
                    dev = abs(femm_val - ana_val);
                end
                fprintf('%-25s %15.4f %15.4f %11.2f%%\n', fname, ana_val, femm_val, dev);
                c.point = fname;
                c.analytical = ana_val;
                c.femm = femm_val;
                c.deviation_pct = dev;
                result.comparisons{end+1} = c;
                matched = true;
                break;
            end
        end
        if ~matched
            fprintf('%-25s %15s %15.4f %12s\n', fname, 'N/A', femm_val, '-');
        end
    end
end
