%% Idraulico.
function [Redhavg, Hv_f, Qv_f]=idraulico(b, s, Nf, tf, bch, Hf, Tair, vent_type, Qv, Hv)

%Hv=prevalenza ventola; [Pa]
%Vch1=velocità aria nel canale verticale; (solo in impinge)[m/s]
%Vch2=velocità aria nel canale orizzontale; [m/s]
%Qv=portata complessiva ventola; [m^3/s]
%Tair=temperatura media dell'aria per il calcolo delle grandezze fisiche [°C]
%b=dimensione del dissipatore parallela alle alette [mm]
%s=apertura per l'afflusso d'aria [mm]
%Nf=numero delle alette
%tf=larghezza aletta [mm]
%bch=larghezza del canale [mm]
%Hf=altezza fin [mm]
%vent_type=indica indica il tipo di ventilazione 'impinge' oppure 'push'

% Qui trovo il punto di funzionamento idraulico
Q1=Qv(1);  Q2=Qv(length(Qv));  %Rv=Vent.Dvent/2000; % raggio ventola
%Nv=Vent.Nv;
Qv_f=Q1;  
error=1; % errore relativo sul DP del punto di funzionamento idraulico
% Uso la bisezione per trovare lo zero.
while abs(error)>0.01

    Qv_f=Q1+0.5*(Q2-Q1);

    Hv_f1=interp1(Qv,Hv,Qv_f,'linear');


    if strcmp(vent_type,'impinge')

        Leff1=Hf/2000; Leff2=b/2000-s/4000;  % Lunghezze efficaci nella direzione verticale ed orizz. [m]
        Vch1=Qv_f*10^6/((Nf-1)*s*bch);  Vch2=Qv_f*10^6/(2*(Nf-1)*bch*Hf); % Velocità di canale [m/s]
        Dh1=4*bch*s/((2*s+2*bch)*10^3);  Dh2=4*bch*Hf/((2*bch+2*Hf)*10^3);  % Diametri idraulici [m]
        Redh1=Dh1*Vch1/(mu_air(Tair)/rho_air(Tair)); % Numero di Reynolds modificato
        Redh2=Dh2*Vch2/(mu_air(Tair)/rho_air(Tair)); % Numero di Reynolds modificato
        Redhavg=(Redh1+Redh2)/2;
        Ld1=(Hf/1000)/(Dh1*Redh1); % lunghezza di flusso adimensionale perpendicolare al canale
        Ld2=(b/1000)/(Dh2*Redh2); % lunghezza di flusso adimensionale parallelo al canale
        fRedh1=24/((1+(bch/s)^2)*(1-(192/(pi^5))*(bch/s)*tanh(pi*s/(2*bch))));
        fRedh2=24/((1+(bch/Hf)^2)*(1-(192/(pi^5))*(bch/Hf)*tanh(pi*Hf/(2*bch))));
        fapp1=sqrt((3.44/sqrt(Ld1))^2+fRedh1^2)/Redh1;
        fapp2=sqrt((3.44/sqrt(Ld2))^2+fRedh2^2)/Redh2;
        K90=(Hf/s<=1)*(3.64-9.15*Hf/s+10.87*(Hf/s)^2-4.93*(Hf/s)^3)+(Hf/s>1)*0.5*((1+Vch2/Vch1)/2);
        sigma=bch/(bch+tf);
        Kc=0.4*(1-sigma^2)+0.4;  Ke=1-sigma^2-0.4*sigma;
        %Vduct=(Qv_f/2)/((Nv/2)*pi*Rv^2)*0; % Velocità dell'aria nel duct. Metto a 0 se trascuro le cdp nel camino
%         Hv=1.0*(((Kc+K90+4*fapp1*Leff1/Dh1)*(4*Hf^2/s^2)+4*fapp2*Leff2/Dh2+Ke)*0.5*rho_air(Tair)*Vch2^2 ...
%         +1*0.5*rho_air(Tair)*Vduct^2);
        Hv_f=1.0*(((Kc+K90+4*fapp1*Leff1/Dh1)*(4*Hf^2/s^2)+4*fapp2*Leff2/Dh2+Ke)*0.5*rho_air(Tair)*Vch2^2);
    else
        Leff2=b/1000;  % Lunghezze efficaci nella direzione verticale ed orizz. [m]
        Vch1=0;  Vch2=Qv_f*10^6/((Nf-1)*bch*Hf); % Velocità di canale [m/s]
        Dh2=4*bch*Hf/((2*bch+2*Hf)*10^3);  % Diametri idraulici [m]
        Redh2=Dh2*Vch2/(mu_air(Tair)/rho_air(Tair)); % Numero di Reynolds modificato
        Redhavg=Redh2;
        Ld2=b/1000/(Dh2*Redh2); % lunghezza di flusso adimensionale parallelo al canale
        fRedh2=24/((1+(bch/Hf)^2)*(1-(192/(pi^5))*(bch/Hf)*tanh(pi*Hf/(2*bch))));
        fapp2=sqrt((3.44/sqrt(Ld2))^2+fRedh2^2)/Redh2;
        sigma=bch/(bch+tf);
        Kc=0.4*(1-sigma^2)+0.4;  Ke=(1-sigma)^2-0.4*sigma;
        Hv_f=1.2*(Kc+4*fapp2*Leff2/Dh2+Ke)*0.5*rho_air(Tair)*Vch2^2;
    end

    error=(Hv_f1-Hv_f)/Hv_f1;  %errore relativo sulla portata pompa.
    if error>0
        Q1=Qv_f;
    else
        Q2=Qv_f;
    end

end
end
