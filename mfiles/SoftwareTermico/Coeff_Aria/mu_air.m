%% mu_air (Tair) [N*s/m^2]
function mu_air=mu_air(Tair)

mu1=[1.732, 1.910, 2.140, 2.392]/10^5;
T1=[0, 38, 93, 149];

mu2=spline(T1,mu1);

mu_air=ppval(mu2, Tair);