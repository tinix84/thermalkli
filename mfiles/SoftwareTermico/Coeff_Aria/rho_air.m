%% mu_air (Tair) [kg/m^3]
function rho_air=rho_air(Tair)

rho1=[1.296, 1.136, 0.96, 0.832];
T1=[0, 38, 93, 149];

rho2=spline(T1,rho1);

rho_air=ppval(rho2, Tair);