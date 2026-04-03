function [qRad12] = heatTransferSmallConvexRadiation(T1, T2, A1, eps1)
    %heatTransferSmallConvexRadiation calculates the heattransfer
    %between a small convex object in a large cavity (A1<<A2)
    %(eg heattransfer from small object to ambient)
    %   qRad12 heattransfer from surface 1 to 2
    %   T1     temperature of surface 1
    %   T2     temperature of surface 2
    %   A1     surface of small object
    %   eps1   emmissivity number of surface 1
    % references: fundamentals of heat and mass transfer sixth edition (978-0-471-45728-2) p833
    
    sigmaBoltz = 5.670367*10^-8; % Stefan–Boltzmann constant [W/(m^2*K^4)]
    
    qRad12 = sigmaBoltz*A1*eps1(T1^4-T2^4);
    
end