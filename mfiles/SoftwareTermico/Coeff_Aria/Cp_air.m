%% Cp_air (Tair) [J/(kg*°C)]
function Cp_air=Cp_air(Tair)

Cp1=[0.24, 0.240, 0.241, 0.243]*4.1868*10^3;
T1=[0, 38, 93, 149];

Cp2=spline(T1,Cp1);

Cp_air=ppval(Cp2, Tair);