%% Termico Rth_fin. Modifica dall'originale
function [Rebavg, Vch1, Vch2, Rth_fin, hf_eq]=Rth_fin(Qv_f, a, b, s, tf, bch, Hf, Tair, vent_type, Kth_fin, Nf)
%
%Vch1=velocità aria nel canale verticale; (solo in impinge)[m/s]
%Vch2=velocità aria nel canale orizzontale; [m/s] (direzione Y)
%Qv_f=portata complessiva ventola; [m^3/s]
%Tair=temperatura media dell'aria per il calcolo delle grandezze fisiche [°C]
%a=dimensione del dissipatore perpendicolare alle alette. [mm] (direzione X)
%b=dimensione del dissipatore parallela alle alette [mm] (direzione Y)
%s=apertura per l'afflusso d'aria [mm]
%Nf=numero delle alette 
%tf=larghezza aletta [mm]
%bch=larghezza del canale [mm]
%Hf=altezza fin [mm]
%impinge=indica se è impige('yes') oppure push ('no')
%Kth_fin=conducibilità termica del materiale dell'aletta [W/(m*°C)]

if strcmp(vent_type, 'impinge')==1
    Leff1=Hf/2000; Leff2=b/2000-s/4000;  % Lunghezze efficaci nella direzione verticale ed orizz. [m]
    Vch1=Qv_f*10^6/((Nf-1)*s*bch);  Vch2=Qv_f*10^6/(2*(Nf-1)*bch*Hf); % Velocità di canale [m/s]
    %Dh1=4*bch*s/((2*s+2*bch)*10^3);  Dh2=4*bch*Hf/((2*bch+2*Hf)*10^3);  % Diametri idraulici [m]
    Reb1=(bch/1000)*Vch1/(mu_air(Tair)/rho_air(Tair))*(bch/1000/Leff1); % Numero di Reynolds modificato
    Reb2=(bch/1000)*Vch2/(mu_air(Tair)/rho_air(Tair))*(bch/1000/Leff2); % Numero di Reynolds modificato
    Rebavg=(Reb1+Reb2)/2;
    Pr=mu_air(Tair)*Cp_air(Tair)/Kt_air(Tair); %Numero di Prandtl
    Nu1=(1/((Reb1*Pr/2)^3)+1/((0.664*sqrt(Reb1)*Pr^0.3333*sqrt(1+3.65/sqrt(Reb1)))^3))^-0.3333;
    Nu2=(1/((Reb2*Pr/2)^3)+1/((0.664*sqrt(Reb2)*Pr^0.3333*sqrt(1+3.65/sqrt(Reb2)))^3))^-0.3333;
    h1=Nu1*Kt_air(Tair)/(bch/1000);   h2=Nu2*Kt_air(Tair)/(bch/1000);
    hbare=h1*s/b+h2*(b-s)/b;  % coeff. di scambio termico convettivo medio pesato sulle lunghezze
    Nuavg=Nu1*s/b+Nu2*(b-s)/b;  % Nu medio pesato sulle lunghezze
    eta_fin=1.0*tanh(sqrt(2*Nuavg*(Kt_air(Tair)/Kth_fin)*(Hf/bch)*(Hf/tf)*(tf/b+1)))/...
        sqrt(2*Nuavg*(Kt_air(Tair)/Kth_fin)*(Hf/bch)*(Hf/tf)*(tf/b+1));
    Nufin=1*Nuavg*eta_fin; %% aggiunto il fattore penalizzante
    hfin=Nufin*Kt_air(Tair)/(bch/1000);
    Abare=(a*b-Nf*b*tf)/10^6;  %superficie del dissipatore tra un aletta e l'altra [m^2]
    Afin=(Nf-1)*b*Hf*2/10^6; %superficie delle sole alette che vengono lambite dall'aria [m^2]
    Rth_fin=1/(Abare*hbare+Afin*hfin); % resistenza termica dei fin+plate [°C/W]
    hf_eq=1/(a*b*Rth_fin/10^6); % Coefficiente di scambio termico equivalente [W/(m^2*°C)]
else
    Leff1=0; Leff2=b/1000;  % Lunghezze efficaci nella direzione verticale ed orizz. [m]
    Vch1=0;  Vch2=Qv_f*10^6/((Nf-1)*bch*Hf); % Velocità di canale [m/s]
    Reb2=(bch/1000)*Vch2/(mu_air(Tair)/rho_air(Tair))*(bch/1000/Leff2); % Numero di Reynolds modificato
    Rebavg=Reb2;
    Pr=mu_air(Tair)*Cp_air(Tair)/Kt_air(Tair); %Numero di Prandtl
   
    Nu2=(1/((Reb2*Pr/2)^3)+1/((0.664*sqrt(Reb2)*Pr^0.3333*sqrt(1+3.65/sqrt(Reb2)))^3))^-0.3333;
    h2=Nu2*Kt_air(Tair)/(bch/1000);
    hbare=h2;  % coeff. di scambio termico convettivo 
    eta_fin=tanh(sqrt(2*Nu2*(Kt_air(Tair)/Kth_fin)*(Hf/bch)*(Hf/tf)*(tf/b+1)))...
        /sqrt(2*Nu2*(Kt_air(Tair)/Kth_fin)*(Hf/bch)*(Hf/tf)*(tf/b+1));
    Nufin=1*Nu2*eta_fin; %% aggiunto il fattore penalizzante
    hfin=Nufin*Kt_air(Tair)/(bch/1000);
    Abare=(a*b-Nf*b*tf)/10^6;  %superficie del dissipatore tra un aletta e l'altra [m^2]
    Afin=(Nf-1)*b*Hf*2/10^6; %superficie delle sole alette che vengono lambite dall'aria [m^2]
    Rth_fin=1/(Abare*hbare+Afin*hfin); % resistenza termica dei fin+plate [°C/W]
    hf_eq=1/(a*b*Rth_fin/10^6); % Coefficiente di scambio termico equivalente [W/(m^2*°C)]
end
