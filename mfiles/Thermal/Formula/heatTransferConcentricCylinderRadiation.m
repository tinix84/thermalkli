function [qRad12] = heatTransferConcentricCylinderRadiation(T1, T2, r1, r2, L, eps1, eps2)
    %heatTransferConcentricCylinderRadiation calculates the heattransfer
    %between long concentric cylinders due to radiation
    %   qRad12 heattransfer from surface 1 to 2
    %   T1     temperature of surface 1
    %   T2     temperature of surface 2
    %   r1     radius of cylinder 1
    %   r1     radius of cylinder 2
    %   L      length of cylinders
    %   eps1   emmissivity number of surface 1
    %   eps2   emmissivity number of surface 2
    % references: fundamentals of heat and mass transfer sixth edition (978-0-471-45728-2) p833
    
    sigmaBoltz = 5.670367*10^-8; % Stefan–Boltzmann constant [W/(m^2*K^4)]
    
    A1 = 2*pi*r1*L; % surface area of cylinder 1
    
    qRad12 = sigmaBoltz*A1*(T1^4-T2^4)/(1/eps1+(1-eps2)/eps2*(r1/r2));
    
end