%% Creazione tabelle risultati per Excel

%% METTO IL TITOLO NELLA PRIMA RIGA E L'INTESTAZIONE NELLA SECONDA. I DATI
%% A SEGUIRE
Risultato(1,1)=cellstr(Titolo); % nella prima cella compare il titolo che poi mi serve per ricaricare 
                                % i dati in Matlab se ho solo il foglio excel aperto.
Risultato(2, 1)=cellstr('Solution info'); Risultato(2, 2)=cellstr('a (dim X) [mm]'); Risultato(2, 3)=cellstr('b (dim Y) [mm]');
Risultato(2, 4)=cellstr('Passo [mm]'); Risultato(2, 5)=cellstr('tf [mm]'); Risultato(2, 6)=cellstr('Hf [mm]');
Risultato(2, 7)=cellstr('tb [mm]');Risultato(2, 8)=cellstr('tr [mm]'); Risultato(2, 9)=cellstr('Qv [m^3/s]');
Risultato(2, 10)=cellstr('Hv [Pa]');Risultato(2, 11)=cellstr('Vch2 [m/s]'); Risultato(2, 12)=cellstr('Ths_max [°C]');
Risultato(2, 13)=cellstr('DT_air [°C]');Risultato(2, 14)=cellstr('Volume [m^3]');Risultato(2, 15)=cellstr('Weight [kg]'); 
Risultato(2, 16)=cellstr('Cost [CHF]');Risultato(2, 17)=cellstr('Ths_maxOK');Risultato(2, 18)=cellstr('QventOK');
Risultato(2, 19)=cellstr('Re_idraulico');Risultato(2, 20)=cellstr('Re_termico'); Risultato(2, 21)=cellstr('Tair [°C]'); 
Risultato(2, 22)=cellstr('Soluzione'); 
% L'ultimo campo serve per mettere un identificativo in maniera da poter
% plottare la mappa (vedi foglio Excel)


for koo=1:length(Results)
    
    Risultato(koo+2,1)=cellstr(num2str(Results(koo).HS_type));  %% okkio devo passarli come cell in Excel
    Risultato(koo+2,2)=cellstr(num2str(Results(koo).Dim_X_mm)); 
    Risultato(koo+2,3)=cellstr(num2str(Results(koo).Dim_Y_mm));
    Risultato(koo+2,4)=cellstr(num2str(Results(koo).Passo_mm));
    Risultato(koo+2,5)=cellstr(num2str(Results(koo).Spess_fin_mm));
    Risultato(koo+2,6)=cellstr(num2str(Results(koo).Altezza_fin_mm));
    Risultato(koo+2,7)=cellstr(num2str(Results(koo).Spess_plate_mm));
    Risultato(koo+2,8)=cellstr(num2str(Results(koo).Spessore_Piastra_mm));
    Risultato(koo+2,9)=cellstr(num2str(Results(koo).Portata_totale_m3_s));
    Risultato(koo+2,10)=cellstr(num2str(Results(koo).Prevalenza_Pa));
    Risultato(koo+2,11)=cellstr(num2str(Results(koo).Velocita_air_m_s));
    Risultato(koo+2,12)=cellstr(num2str(Results(koo).Tmax_assoluta_gC));
    Risultato(koo+2,13)=cellstr(num2str(Results(koo).DT_air_gC));
    Risultato(koo+2,14)=cellstr(num2str(Results(koo).Volume_m3));
    Risultato(koo+2,15)=cellstr(num2str(Results(koo).Peso_kg));
    Risultato(koo+2,16)=cellstr(num2str(Results(koo).Costo_CHF));
    Risultato(koo+2,17)=cellstr(num2str(Results(koo).Solved_THERM));
    Risultato(koo+2,18)=cellstr(num2str(Results(koo).Solved_HYDR));
    Risultato(koo+2,19)=cellstr(num2str(Results(koo).Re_hydr));
    Risultato(koo+2,20)=cellstr(num2str(Results(koo).Re_therm));
    Risultato(koo+2,21)=cellstr(num2str(Results(koo).Temperatura_aria_gC));
    Risultato(koo+2,22)=cellstr(['Results(' num2str(koo) ')']);

end
