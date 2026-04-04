function [T_surface, h_arr, q_arr] = free_conv_surface_temp(faces, T_ambient, P_total)
    % free_conv_surface_temp - find surface temperature from natural convection + radiation
    % Uses bisection on the heat balance equation.
    %
    % faces: struct array with fields:
    %   .area            [m2] surface area
    %   .char_length     [m] characteristic length
    %   .orientation     'vertical', 'horizontal_top', or 'horizontal_bottom'
    %   .emissivity      [-] surface emissivity (0-1), default 0.9
    %
    % T_ambient: ambient temperature [C]
    % P_total: total heat dissipation [W]
    %
    % Returns:
    %   T_surface: surface temperature [C]
    %   h_arr: heat transfer coefficient per face [W/(m2*K)]
    %   q_arr: heat dissipation per face [W]

    % Bisection: T_surface is between T_ambient and T_ambient + 500
    T_low = T_ambient + 0.1;
    T_high = T_ambient + 500;
    tol = 0.01;  % 0.01 C tolerance

    for iter = 1:100
        T_mid = (T_low + T_high) / 2;
        r = heat_balance(T_mid, faces, T_ambient, P_total);
        if abs(r) < tol * P_total * 0.001
            break;
        end
        if r > 0
            T_high = T_mid;
        else
            T_low = T_mid;
        end
    end

    T_surface = T_mid;

    % Compute per-face breakdown
    h_arr = zeros(1, length(faces));
    q_arr = zeros(1, length(faces));
    for k = 1:length(faces)
        [h_nat, ~] = h_natural_convection(faces(k).orientation, faces(k).char_length, T_ambient, T_surface);
        if isfield(faces(k), 'emissivity')
            h_rad = h_radiation(faces(k).emissivity, T_ambient, T_surface);
        else
            h_rad = h_radiation(0.9, T_ambient, T_surface);
        end
        h_arr(k) = h_nat + h_rad;
        q_arr(k) = h_arr(k) * faces(k).area * (T_surface - T_ambient);
    end
end

function residual = heat_balance(Ts, faces, T_ambient, P_total)
    residual = 0;
    for k = 1:length(faces)
        [h_nat, ~] = h_natural_convection(faces(k).orientation, faces(k).char_length, T_ambient, Ts);
        if isfield(faces(k), 'emissivity')
            h_rad = h_radiation(faces(k).emissivity, T_ambient, Ts);
        else
            h_rad = h_radiation(0.9, T_ambient, Ts);
        end
        residual = residual + (h_nat + h_rad) * faces(k).area * (Ts - T_ambient);
    end
    residual = residual - P_total;
end
