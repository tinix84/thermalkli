%% Tplane_calc
%% Questo file calcola la distribuzione di temperatura sul piano di
%% posizionamento degli IGBT. Viene usato per visualizzare la distribuzione
%% termica una volta ottenuta la soluzione.



function [Ths, Th_BP]=Tplane_dist(Rth_fin, p_n, Tair, Tin, Niter, Piastra, a, b, x_gg, y_gg,...
    Kth_plate, tb, a_n, b_n, Kth_piastra, tr, hf_eq, Xp, Yp)

% Rth_fin= resistenza termica equivalente alette [°C/W]
% p_n=vettore con le potenze delle singole sorgenti (W)
% Tair= temperatura media aria (°C)
% Tin=temepratura aria in ingresso (°C)
% Niter= numero di iterazioni del calcolo temerpature nel punto Xp,Yp
% Piastra= indica löa presenza o meno della piastra di rame sulla superficie
% a=dimensione dissipatore nella direzione x (mm) perpendicolare alle alette
% b=dimensione del dissipatore nella direzione y (mm) parallela alle alette
% x_gg= coordinata punto centrale sorgenti (direzione X) (mm)
% y_gg= coordinata punto centrale sorgenti (direzioneY) (mm)
% kth_plate=conducib termica baseplate (W/°C*m^2)
% kth_piastra=conducib termica piastra (W/°C*m^2)
% tb, tr= spessore base e piastra (mm)
% a_n; b_n= dimensione componente lungo direzione X e lungo direzione Y
% rispettivamente (mm)
% Xp, Yp= vettori delle coordinate dei punti nei quali si vuole calcolare la temperatura sul basplate (mm)
% hf_eq=conducibilità equivalente delle alette (W/°C*m^2)



%%% CALCOLO DELL'LMTD E DELLA Th DEL FONDO DEL BASEPLATE
LMTD=Rth_fin*sum(p_n)
Tfluido_out=(Tair-Tin)*2+Tin
Th_BP=(Tin-Tfluido_out*exp((Tfluido_out-Tin)/LMTD))/(1-exp((Tfluido_out-Tin)/LMTD))-LMTD
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% QUI SOTTO ITERO IL CALCOLO DELLA TEMPERATURA SU TUTTI I PUNTI Xp, Yp DEFINITI
for n1=1:length(Xp)
    for n2=1:length(Yp)
        [DTheta, Ths1]=Temp_calc(Xp(n1), Yp(n2), Niter, Piastra, p_n, a, b, x_gg, y_gg,...
     Kth_plate, tb, a_n, b_n, Kth_piastra, tr, Th_BP, hf_eq);
        Ths(n2, n1)=Ths1;
    end
    n1
end
[r, c]=find(Ths==max(max(Ths)))  %Qui trovo il max della matrice


figure
[C, h]=contourf(Xp, Yp, Ths);
caxis([20, max(max(Ths))*1.05]);
axis equal
v=20:2:106;   % qui definisco la scala delle temperature che voglio compaiano sulla mappa termica
set(h, 'levelStepMode', 'Manual', 'levelStep', 1, 'Linestyle', 'none');
clabel(C,h,v, 'FontSize', 6, 'Rotation', 0)
%text(Dis.Xc(n), Dis.Yc(n), num2str(Thsmax));
text(Xp(c), Yp(r), num2str(max(max(Ths))));
%title(Soluzione.Name)

for nn=1:length(p_n)
    rectangle('Position',[(x_gg(nn)-a_n(nn)/2),(y_gg(nn)-b_n(nn)/2),a_n(nn),b_n(nn)]);
end
end

