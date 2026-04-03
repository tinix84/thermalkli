function [etaFin] = finEfficieny(L, h, A, k, Ac)
    %finEfficieny calculates the fin efficiency of a fin with constant
    %crosssection
    %   L length of fin
    %   h pure-heat transfer coefficient fin-surface to fluid
    %   A fin surface area
    %   k thermal conductivity of fin
    %   Ac cross-sectional area of fin
    
    mL = (h*A/(k*Ac*L))^0.5*L;
    etaFin = tanh(mL)/mL;
end

