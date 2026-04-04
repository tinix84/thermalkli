function [k1, k2, k3] = fan_scaling_fit(V_max, dp_max, P_fan, D, N)
    % fan_scaling_fit - fit fan scaling law constants from datasheet values
    % Drofenik eq. 29-31:
    %   V_MAX = k1 * N * D^3  =>  k1 = V_max / (N * D^3)
    %   dp_MAX = k2 * N^2 * D^2  =>  k2 = dp_max / (N^2 * D^2)
    %   P_FAN = k3 * N^3 * D^5  =>  k3 = P_fan / (N^3 * D^5)
    k1 = V_max / (N * D^3);
    k2 = dp_max / (N^2 * D^2);
    k3 = P_fan / (N^3 * D^5);
end
