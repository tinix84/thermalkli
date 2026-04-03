function [qRad12] = heatTransferEnclosureRadiation(T1, T2, eps1, eps2, A1, A2, F12)
    %heatTransferEnclosureRadiation calculates the heattransfer due to
    %radiation between two surfaces that form an enclosure (radiation only
    %between each other)
    %   qRad12 heattransfer from surface 1 to 2
    %   T1     temperature of surface 1
    %   T2     temperature of surface 2
    %   eps1   emmissivity number of surface 1
    %   eps2   emmissivity number of surface 2
    %   A1     area of surface 1
    %   A2     area of surface 2
    %   F12    view factor from surface 1 to 2
    % references: fundamentals of heat and mass transfer sixth edition (978-0-471-45728-2) p832
    
    sigmaBoltz = 5.670367*10^-8; % Stefan–Boltzmann constant [W/(m^2*K^4)]
    
    qRad12 = sigmaBoltz*(T1^4-T2^4)/((1-eps1)/(eps1*A1)+1/(A1*F12)+(1-eps2)/(eps2*A2));
    
end

