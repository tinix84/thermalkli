%cooling estimation
Pout=150e3; %[W];
eta=.95; 
Ploss=Pout*(1-eta);
q=2:9; %[l/min];
%cp=4.187 %[kJ/kgK] clean water 20°C
cp=3.4834; %[kJ/kgK] glycol-water solution 50% 48.9°C
SG=1.064; %specific gravity coolant    
rho_H2O=1; %[kg/m3] @ 4°C
rho=rho_H2O*SG;
Tin=73.0; %[°C]
Tout=88.4; %[°C]
						
qm=rho*q/60 %[kg/s] coolant mass flow

dT=Ploss./(cp*1e3*qm)
plot(q,dT)
xlabel('Flow rate coolant[l/min]')
ylabel('Coolant temperature increase[K]')

Rjc=1.5 %[K/W] thermal resist junction-case
nIGBT=24
Rcl=linspace(0,2,100);; %[K/W] thermal resist case-liquid
Tjmax=.8*175;
Tj=Ploss/nIGBT*(Rjc+Rcl)+Tin;
figure
plot(Rcl, Tj)
