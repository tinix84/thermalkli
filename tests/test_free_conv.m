function results = test_free_conv()
    results = {};

    % Test 1: surface temp > ambient
    r.name = 'free_conv: surface temp above ambient';
    faces(1).area = 0.01;
    faces(1).char_length = 0.05;
    faces(1).orientation = 'vertical';
    faces(1).emissivity = 0.9;
    [Ts, ~, ~] = free_conv_surface_temp(faces, 25, 1);
    r.pass = Ts > 25;
    r.detail = sprintf('Ts=%.1fC, Tamb=25C', Ts);
    results{end+1} = r;

    % Test 2: more power -> higher temperature
    r.name = 'free_conv: more power -> higher temp';
    [Ts1, ~, ~] = free_conv_surface_temp(faces, 25, 1);
    [Ts2, ~, ~] = free_conv_surface_temp(faces, 25, 5);
    r.pass = Ts2 > Ts1;
    r.detail = sprintf('1W: %.1fC, 5W: %.1fC', Ts1, Ts2);
    results{end+1} = r;

    % Test 3: heat balance closes
    r.name = 'free_conv: heat balance closes within 1%';
    [~, ~, q_arr] = free_conv_surface_temp(faces, 25, 1);
    r.pass = abs(sum(q_arr) - 1) < 0.01;
    r.detail = sprintf('q_total=%.4f, expected 1.0', sum(q_arr));
    results{end+1} = r;

    % Test 4: bridge component from existing script
    r.name = 'free_conv: bridge 0.8W at 75C';
    thick = 4e-3; width = 7.5e-3; height = 9.1e-3; len = 14.3e-3;
    clear faces2;
    faces2(1).area = width*(height+thick/2)*2;
    faces2(1).char_length = height;
    faces2(1).orientation = 'vertical';
    faces2(1).emissivity = 0.9;
    faces2(2).area = len*(height+thick/2)*2;
    faces2(2).char_length = height;
    faces2(2).orientation = 'vertical';
    faces2(2).emissivity = 0.9;
    faces2(3).area = width*len;
    faces2(3).char_length = width/4;
    faces2(3).orientation = 'horizontal_top';
    faces2(3).emissivity = 0.9;
    faces2(4).area = width*len;
    faces2(4).char_length = width/4;
    faces2(4).orientation = 'horizontal_bottom';
    faces2(4).emissivity = 0.9;
    [Ts, ~, ~] = free_conv_surface_temp(faces2, 75, 0.8);
    r.pass = Ts > 80 && Ts < 200;
    r.detail = sprintf('Ts=%.1fC (bridge at 75C ambient, 0.8W)', Ts);
    results{end+1} = r;
end
