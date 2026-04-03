function db_dir = thermal_db_path()
    % thermal_db_path - returns absolute path to the db/ directory
    this_dir = fileparts(mfilename('fullpath'));
    candidate = fullfile(this_dir, '..', 'db');
    if exist(fullfile(candidate, 'FluidData.xlsx'), 'file')
        db_dir = candidate;
        return;
    end
    candidate = fullfile(pwd, 'db');
    if exist(fullfile(candidate, 'FluidData.xlsx'), 'file')
        db_dir = candidate;
        return;
    end
    error('thermal_db_path: cannot find db/ directory with FluidData.xlsx');
end
