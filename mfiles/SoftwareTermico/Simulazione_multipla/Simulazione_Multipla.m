%% SIMULAZIONE SINGOLA
%% calcola la distribuzione della temperatura relativa al caso definito in
%% Dati.m


Dati_multipla   %% Carico tutti i dati

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Nsoluz=length(Soluzione);  % determino il numero di soluzioni che devo analizzare
cont=1; % questo è il contatore delle soluzioni. Viene incrementato ogni volta che si genera una nuova soluzione
for n1=1:Nsoluz  % ciclo tutte le soluzioni
    
    for n2=1:length(Soluzione(n1).vent_type) % ciclo tutti i modi di ventilazione della soluzione
        for k1=1:length(tf) % ciclo tutti gli spessori alette proposti
            for k2=1:length(Hf)  % ciclo tutte le altezze alette proposte
                for k3=1:length(Tp)  % ciclo tutti i passi
                    if (Tp(k3)-tf(k1))>=2;  % verifica che l'aperturta del canale non sia troppo piccola altrimenti salta la soluzione

                        for k4=1:length(tb)  % ciclo  gli spessori di base proposti
                            % posso ricavare qui le caratt del HS perchè
                            % non dipendono dalle dimensioni dello stesso
                            [Kth_plate, Kth_fin, Kth_piastra, Cost_kg, Piastra, rho_plate_fin_piastra]=HS_Tech(Soluzione(n1).HS_type); % ricavo le caratteristiche del modello HS
                            for k5=1:length(tr) % ciclo gli spessore di piastra proposti
                                %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                                %% RICAVO I DATI CHE MI SERVONO PER LA SOLUZIONE DI IDRAULICO ED RTH_FIN
                                a=Soluzione(Nsoluz).ainit; b=Soluzione(Nsoluz).binit; % qui assegno le dimensioni iniziali del HS
                                x_g1=Soluzione(Nsoluz).XG; y_g1=Soluzione(Nsoluz).YG; % qui assegno le posizioni iniziali sorgenti 
                                amax=Soluzione(Nsoluz).amax; bmax=Soluzione(Nsoluz).bmax; %qui assegno le relative dimensioni massime del dissipatore
                                s=Soluzione(n1).Apertura_impinge; % Apertura posteriore (solo per impinge)
                                vent_type=char(Soluzione(n1).vent_type(n2)); % estraggo il tipo di ventole dalla Soluzione in analisi
                                bch=Tp(k3)-tf(k1); % la larghezza del canale viene calcolata
                                [Hv1, Qv1, Qvmin1, Qvmax1, Cost_Fan1, Volume_Fan1]=Fan_Model(Soluzione(n1).Fan); %  Ricavo le caratteristiche della ventola scelta
                                %% Caratteristiche equivalenti in base al numero di ventole in parallelo
                                Nv=Soluzione(n1).Nventole;
                                Qv=Nv*Qv1; % portata totale ventola equivalente
                                Hv=Hv1;
                                Qvmin=Nv*Qvmin1; % Portata minima ventola equivalente
                                Qvmax=Nv*Qvmax1; % Portata massima ventola equivalente
                                Cost_Fan=Nv*Cost_Fan1; % Costo totale ventole
                                Volume_Fan=Nv*Volume_Fan1; % volume ingombro totale delle ventole
                                Qguess=(Qvmin+Qvmax)/2; % portata di guess. Siccome il punto di funzionamento della ventola non è
                                % noto si ipotizza una media del campo di portate della ventola
                                Tair=Tin+0.5*sum(p_n)/(Cp_air(Tin)*rho_air(Tin)*Qguess); % per il calcolo delle proprietà aria uso la T media
                                %% inizio il ciclo di ottimizzazione del dissipatore
                                Ths=Tmax*2; % inizializzo il vettore delle Ths ad un valore che mi consenta di entrare nel ciclo
                                while sum(Ths<Tmax)~=length(Tmax)  % qui controllo che tutte le temperature nei punti richiesti in Dati_multipla
                                    % siano inferiori alle corrispondenti massime richieste
                                    
                                    Nf=round(a/(bch+tf(k1))); % Numero di alette.
                                    [Re_hydr, Hv_f, Qv_f]=idraulico(b, s, Nf, tf(k1), bch, Hf(k2), Tair, vent_type, Qv, Hv);    %Risolvo qui l'idraulica ed il termico perchè poi non cambia nulla
                                    Tair=Tin+0.5*sum(p_n)/(Cp_air(Tin)*rho_air(Tin)*Qv_f); %ricalcolo la Tair (media ingresso uscita) ora che conosco la reale portata
                                    
                                    [Re_therm, Vch1, Vch2, Rth_fin1, hf_eq]=Rth_fin(Qv_f, a, b, s, tf(k1), bch, Hf(k2), Tair, vent_type, Kth_fin, Nf); % Ricavo Rthfin della soluzione presente

                                    %% CALCOLO DELLE TEMPERATURE NEI PUNTI STABILITI
                                    %%% CALCOLO DELL'LMTD E DELLA Th DEL FONDO DEL BASEPLATE
                                    LMTD=Rth_fin1*sum(p_n);
                                    Tfluido_out=(Tair-Tin)*2+Tin;
                                    Th_BP=(Tin-Tfluido_out*exp((Tfluido_out-Tin)/LMTD))/(1-exp((Tfluido_out-Tin)/LMTD))-LMTD;
                                    [xThs, yThs]=XY_Thscalc(x_g1, y_g1, a_n, b_n, scelta);
                                    for i=1:length(Tmax) 
                                        % il Ths qui calcolato è ordinat in maniera da poter essere
                                        % confrontato con la Tmax 1 ad 1
                                        %[xThs, yThs]=XY_Thscalc(x_g1, y_g1, a_n, b_n, scelta);
                                        [DTheta, Ths(i)]=Temp_calc(xThs(i), yThs(i), Niter, Piastra, p_n, a, b, x_g1, y_g1,...
                                            Kth_plate, tb(k4), a_n, b_n, Kth_piastra, tr(k5), Th_BP, hf_eq);
                                    end
                                    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                                    % SPOSTAMENTO COLONNE E RIGHE

                                    %analisi per colonne
                                    Nmovex=0; Nmovey=0;  % inizializzo il numero di spostamenti che poi effettuo sotto
                                    if a<amax  %% qui verifico che il massimo aumento della dimensione a non debordi amax
                                        for nc=1:max(colonne)
                                            c=find(colonne==nc); % trovo gli indici del vettore colonne che hanno valore nc
                                            c1=find(colonne>nc); %trovo le colonne con indice maggiore dell'attuale
                                            % A seconda di dove viene misurata la temperatura, il criterio
                                            % cambia perchè Ths è un vettore con elementi in numero uguale o
                                            % diverso rispetto ai componenti dissipanti
                                            if strcmp(scelta, 'centro')
                                                criterio_c=sum(Ths(c)>Tmax(c));
                                            else
                                                criterio_c=sum([Ths(2*c-1) Ths(2*c)]>[Tmax(2*c-1) Tmax(2*c)]);
                                            end
                                            if criterio_c>0 % confronto le temperature calcolate con quelle massime nei punti
                                                % relativi agli IGBT della colonna considerata
                                                x_g1(c)=x_g1(c)+Dx; x_g1(c1)=x_g1(c1)+2*Dx;
                                                Nmovex=Nmovex+1; % tiene conto delle colonne mosse
                                            end
                                        end
                                    end
                                    if b<bmax  %% qui verifico che il massimo aumento della dimensione a non debordi amax
                                        for nr=1:max(righe)
                                            r=find(righe==nr); % trovo gli indici del vettore righe che hanno valore nr
                                            r1=find(righe>nr); %trovo le righe con indice maggiore dell'attuale
                                            % A seconda di dove viene misurata la temperatura, il criterio
                                            % cambia perchè Ths è un vettore con elementi in numero uguale o
                                            % diverso rispetto ai componenti dissipanti
                                            if strcmp(scelta, 'centro')
                                                criterio_r=sum(Ths(r)>Tmax(r));
                                            else
                                                criterio_r=sum([Ths(2*r-1) Ths(2*r)]>[Tmax(2*r-1) Tmax(2*r)]);
                                            end
                                            if criterio_r>0 % confronto le temperature calcolate con quelle massime nei punti
                                                % relativi agli IGBT della colonna considerata
                                                y_g1(r)=y_g1(r)+Dy; y_g1(r1)=y_g1(r1)+2*Dy;
                                                Nmovey=Nmovey+1; % tiene conto delle righe mosse
                                            end
                                        end
                                    end
                                    a1=a+2*(Nmovex)*Dx; b1=b+2*(Nmovey)*Dy; % determino le nuove dimensioni del dissipatore in base al numero di colonne e righe che ho dovuto spostare.
                                    a=a1*(a1<amax)+amax*(a1>=amax); b=b1*(b1<bmax)+bmax*(b1>=bmax); % posso raggiungere le dimensioni massime in due tempi diversi, 
                                                                                                    % cosi' continuo ad aumentare una e lascio fissa l'altra
                                    
                                                                        
                                    if (a>=amax)&&(b>=bmax), break, end % se raggiungo il massimo valore consentito su entrambe le dimensioni, esco dal ciclo while e passo al prossimo
                                    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                                end % del While sum(Ths<Tmax)~=length(Tmax)
                                %%%%% CHECK DELLA BONTÀ DELLA SOLUZIONE TROVATA
                                
                                if (Qv_f>Qvmin) && (Qv_f<Qvmax) %controllo che la portata della pompa sia compresa nei limiti
                                    Solved_HYDR='YES'; 
                                else
                                    Solved_HYDR='NO';
                                end
                                 if Ths<=Tmax   % controllo che tutte le temperature dei punti critici siano sotto i corrispondenti valori massimi
                                    Solved_THERM='YES';
                                else
                                    Solved_THERM='NO';
                                end
                                
                                %%%%  DI SEGUITO IMMAGAZZINO I DATI CHE
                                %%%%  MI INTERESSA ESPORTARE NELLA
                                %%%%  VARIABILE: RESULTS
                                
                                %% Calcolo pesi e costi totali soluzione:
                                rho_plate=rho_plate_fin_piastra(1); rho_fin=rho_plate_fin_piastra(2); rho_piastra=rho_plate_fin_piastra(3); %fisso le densità dei diversi materiali in kg/m^3
                                Vol_plate=tb(k4)*a*b/10^9; Vol_fin=Nf*Hf(k2)*tf(k1)*b/10^9; Vol_piastra=strcmp(Piastra,'yes')*tr(k5)*a*b/10^9% calcolo volumi in m^3
                                %% Considero il backplate per Hf>70mm. In
                                %% questi casi il profilo è molto probabilmente chiuso
                                if Hf(k2)>=70
                                    if strcmp(vent_type, 'impinge')
                                        Vol_backplane=5*a*b*0.5/10^9; % 5mm spessore in impinge considero solo metà backplane
                                    else
                                        Vol_backplane=5*a*b/10^9; % 5mm spessore in push considero tutto il backplane
                                    end
                                else
                                    Vol_backplane=0;  % se l'aletta è sufficientemente bassa posso lasciarla aperta
                                end
                                PesoHS=(Vol_plate+Vol_backplane)*rho_plate+Vol_fin*rho_fin+Vol_piastra*rho_piastra;  % Peso totale HS
                                Costo_Soluzione=Cost_kg*PesoHS+Cost_Fan;  % Calcolo totale soluzione (il Cost_Fan è già relativo alla somma dei ventilatori)
                                Volume_Soluzione=Vol_plate+Vol_piastra+Vol_fin+Volume_Fan; % Calcolo del volume totale della soluzione
                                %%Vch2=Qv_f*1000000/((a-Nf*tf(k1))*Hf(k2)) Cannato, viene già calcolato sopra
                                Xp=0:a/NpX:a; Yp=0:b/NpY:b;  % qui determino il numero dei punti per la visualizzazione
                                %% Butto tutto nella struttura dei risultati
                                %Results=zeros(1,200);  % dimensiono a caso
                                %il vettore results.. Non funziona...
                                Results(cont)=struct('Nome_analisi', Titolo, 'HS_type', [Soluzione(n1).HS_type ' ' vent_type ' ' num2str(Nv) 'x' ...
                                        Soluzione(n1).Fan ' Dim (X,Y)=' num2str(a) ';' num2str(b) ' Passo=' num2str(Tp(k3))]...
                                        , 'Dim_X_mm', a, 'Dim_Y_mm', b, 'Passo_mm', Tp(k3), 'Spess_fin_mm', tf(k1), 'Solved_THERM', Solved_THERM ...
                                        , 'Solved_HYDR', Solved_HYDR, 'Altezza_fin_mm', Hf(k2), 'Spess_plate_mm', tb(k4),...
                                        'Spessore_Piastra_mm', strcmp(Piastra,'yes')*tr(k5), 'HS_Tech', [Kth_plate, Kth_fin, Kth_piastra, Cost_kg, Piastra, rho_plate_fin_piastra],  ...
                                        'Temp_critiche_gC', round(Ths), 'Temp_massime_gC', Tmax,'Portata_totale_m3_s', Qv_f, 'Prevalenza_Pa', Hv_f...
                                        , 'Peso_kg', PesoHS, 'Volume_m3', Volume_Soluzione, 'Costo_CHF', Costo_Soluzione,...
                                         'Dim_componente_X_mm', a_n, 'Dim_componente_Y_mm', b_n, 'Perdite_componenti_W', p_n,...
                                         'Coordinata_X_comp_mm', x_g1, 'Coordinata_Y_comp_mm', y_g1, 'Velocita_air_m_s', Vch2, 'Tmax_assoluta_gC', round(max(Ths)), ...
                                         'DT_air_gC', (Tair-Tin), 'Re_hydr', Re_hydr, 'Re_therm', Re_therm, 'Temperatura_aria_gC', Tin, 'Temp_media_aria', Tair, 'Temp_base_plate_gC', Th_BP, ...
                                         'Rth_fin', Rth_fin1, 'hf_eq_fin', hf_eq, 'Niterazioni', Niter, 'Punti_Xp_Tplane', Xp, 'Punti_Yp_Tplane', Yp);
                                cont=cont+1
                                if strcmp(Piastra, 'no'), break, end  % se la soluzione analizzata non prevede la piastra è inutile ciclare sul tr.
                            end % del for k5=1:length(tr)
                        end % del for k4=1:length(tb)
                    end % end dell'if (Tp(k3)-tf(k1))>=2;
                end %end del for sul Tp
            end %end del for sul Hf
        end %end del for sul tf
    end %end del for sul vent type
end %end del for sul Soluzione

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Salvo la configurazione calcolata
save(['D:\Documents and Settings\120006009\My Documents\Software Termico\Database_risultati\' Titolo], 'Results');
