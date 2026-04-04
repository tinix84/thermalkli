function parsed = cli_parse_args(args)
    % cli_parse_args - parse CLI arguments into a struct
    % Input: cell array of strings, e.g. {'--power', '50', '--help'}
    % Output: struct with fields
    %   --key value  -> parsed.key = 'value' (string)
    %   --key.sub v  -> parsed.key_sub = 'value' (dots to underscores)
    %   --flag       -> parsed.flag = true (if next arg starts with -- or is last)

    parsed = struct();
    i = 1;
    while i <= length(args)
        arg = args{i};
        if length(arg) > 2 && strcmp(arg(1:2), '--')
            key = strrep(arg(3:end), '.', '_');
            key = strrep(key, '-', '_');
            if i + 1 <= length(args) && ~strncmp(args{i+1}, '--', 2)
                parsed.(key) = args{i+1};
                i = i + 2;
            else
                parsed.(key) = true;
                i = i + 1;
            end
        else
            i = i + 1;
        end
    end
end
