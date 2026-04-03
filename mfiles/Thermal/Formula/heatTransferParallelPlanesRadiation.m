function [qRad12] = heatTransferParallelPlanesRadiation(T1, T2, A, eps1, eps2)
    %heatTransferParallelPlanesRadiation calculates the heattransfer
    %between large parallel planes due to radiation
    %   qRad12 heattransfer from surface 1 to 2
    %   T1     temperature of surface 1
    %   T2     temperature of surface 2
    %   eps1   emmissivity number of surface 1
    %   eps2   emmissivity number of surface 2
    %   A      area of surface
    % references: fundamentals of heat and mass transfer sixth edition (978-0-471-45728-2) p833
    
    sigmaBoltz = 5.670367*10^-8; % Stefan–Boltzmann constant [W/(m^2*K^4)]
    
    qRad12 = A*sigmaBoltz*(T1^4-T2^4)/(1/eps1+1/eps2-1);
    
end