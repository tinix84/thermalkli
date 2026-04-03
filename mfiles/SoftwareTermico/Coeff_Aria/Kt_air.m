%% Kt_air (Tair) [W/(m*°C)]
function Kt_air=Kt_air(Tair)

Kt1=[0.0208, 0.0230, 0.0259, 0.0287]*4.1868*10^3/3600;
T1=[0, 38, 93, 149];

Kt2=spline(T1,Kt1);

Kt_air=ppval(Kt2, Tair);