function run_tests()
    % run_tests - discovers and runs all test_*.m files in tests/
    % Each test file must be a function returning a cell array of structs
    % with fields: .name (string), .pass (bool)

    this_dir = fileparts(mfilename('fullpath'));
    root_dir = fullfile(this_dir, '..');
    addpath(fullfile(root_dir, 'lib'));
    addpath(genpath(fullfile(root_dir, 'mfiles')));
    addpath(this_dir);

    test_files = glob(fullfile(this_dir, 'test_*.m'));
    total_pass = 0;
    total_fail = 0;
    total_error = 0;

    for i = 1:length(test_files)
        [~, name, ~] = fileparts(test_files{i});
        fprintf('Running %s ...', name);
        try
            results = feval(name);
            pass = sum(cellfun(@(r) r.pass, results));
            fail = length(results) - pass;
            fprintf(' %d/%d PASS\n', pass, length(results));
            if fail > 0
                for j = 1:length(results)
                    if ~results{j}.pass
                        fprintf('  FAIL: %s\n', results{j}.name);
                        if isfield(results{j}, 'detail')
                            fprintf('    %s\n', results{j}.detail);
                        end
                    end
                end
            end
            total_pass = total_pass + pass;
            total_fail = total_fail + fail;
        catch e
            fprintf(' ERROR: %s\n', e.message);
            total_error = total_error + 1;
        end
    end

    fprintf('\n========================================\n');
    fprintf('TOTAL: %d pass, %d fail, %d error\n', total_pass, total_fail, total_error);
    if total_fail > 0 || total_error > 0
        exit(1);
    end
end
