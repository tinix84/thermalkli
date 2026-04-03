%%% DATI PER LA SIMULAZIONE DEI DISSIPATORI

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% ASSEGNO UN TITOLO ALL'ANALISI DI OTTIMIZZAZIONE. i RISULTATI VERRANNO
%% SALVATI CON IL NOME QUI ASSEGNATO IN FORMATO .MAT NELLA DIRECTORY
%% DATABASE_RISULTATI. ps NON LASCIARE SPAZI NEL TITOLO

Titolo='HS_600A_T25_20may2008';

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% TEMPERATURA ARIA PER ILC CALCOLO TERMICO
Tin=25;  %temperatura aria ingresso (°C)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%DEFINIZIONE DIMENSIONE MINIMA E DIMENSIONE MASSIMA DISSIPATORE
%%E DEGLI INTERVALLI DI VARIAZIONE DELLE GRANDEZZE GEOMETRICHE

%% DATI GEOMETRICI:
%% LA DIMENSIONE X È QUELLA PERPENDICOLARE ALLE ALETTE; LA DIMESIONE Y È
%% QUELLA PARALLELA ALLE ALETTE
% amin=350; % dimensione minima X  (mm)
% bmin=450; % dimensione minima Y (mm)
% amax=500; % dimensione massima X (mm)
% bmax=650; % dimensione massima Y (mm)
tb=[10 15 20]; % spessore base (mm)
Hf=[48 63 96]; % altezza aletta (mm)
Tp=[4 5.5 6]; % passo profilo (mm)
tf=[1.5 2 2.5]; % spessore aletta (mm)
tr=10; %spessore piastra aggiuntiva (mm) (non possiamo mettere zero)
% tb=[5 10]; % spessore base (mm)
% Hf=[45]; % altezza aletta (mm)
% Tp=[4]; % passo profilo (mm)
% tf=[1.5 2.5]; % spessore aletta (mm)
% tr=10; %spessore piastra aggiuntiva (mm) (non possiamo mettere zero)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% CARATTERIZZAZIONE DELLE SORGENTI E POSIZIONAMENTO INIZIALE

%% LA DIMENSIONE X È QUELLA PERPENDICOLARE ALLE ALETTE; LA DIMESIONE Y È
%% QUELLA PARALLELA ALLE ALETTE

a_n=[110 110 110 110 110 110 110 110 110]; % dimensione sorgenti parallela asse X
b_n=[80 80 80 80 80 80 80 80 80];  %dimensione sorgenti parallela asse Y
p_n=[710 710 710 710 710 710 710 710 710]; % losses of the sources

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% SUDDIVIDO LE DIVERSE SORGENTI PER RIGHE E COLONNE. MI SERVE NEL LOOP DI
%% OTTIMIZZAZIONE PER SPOSTARE LE SORGENTI A GRUPPI DI RIGHE E COLONNE A
%% SECONDA CHE VI SIANO O MENO PROBLEMI TERMICI NELLE STESSE

colonne=[1 2 3 1 2 3 1 2 3]; %si costruisce guardando i valori riportati nel vettore x_g
righe=[1 1 1 2 2 2 3 3 3];  %si costruisce guardando i valori riportati nel vettore y_g

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% FISSO LE ITERAZIONI DEL CALCOLO DELLE TEMPERATURE SUL BASPLATE

Niter=25; %25 è il numero di iterazioni standard stabilite in base al confronto con numeri vicini. Se si vuole una soluzione + rapida
   % ma meno precisa, diminuire il numero di iterazioni

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% IMPOSTO IL dX E dY DI VARIAZIONE DELLE COORDINATE DI RIGHE E COLONNE
%% NELLA RICERCA DELLA SOLUZIONE OTTIMA
Dx=5; % (mm) ogni colonna che termicamente non è OK viene spostata di Dx verso destra
Dy=5; % (mm) ogni riga che termicamente non è OK viene spostata di Dy verso alto
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% SCELTA DEI PUNTI NEI QUALI CALCOLARE LE TEMPERATURE DA CONFFRONTARE CON Tmax
%% SI SCEGLIE SOLO CENTRO OPPURE SIDE. sIDE È IL FIANCO DEL LATO + LUNGO
%% DELL'igbt (SI CALCOLA SUI DUE LATI LUNGHI)

% Il vettore delle temperature ha dimensione uguale al numero di sorgenti
% se le temperature sono misurate al centro, doppia rispetto al numero di
% sorgenti se le T sono misurate a lato. In questo caso infatti devo
% calcolarle su entrambi i lati.

scelta='centro'; % sel la stringa è posta uguale al centro considera le temperature sotto i chips altrimenti al fianco
Tmax=[93 93 93 93 93 93 93 93 93];   % massime temperature dei singoli componenti. 
% se scelgo di calcolare le temeprature a lato componenti, allora Tmax avrà
% dimensione doppia rispetto al numero di sorgenti presenti sul HS

%[xThs, yThs]=XY_Thscalc(x_g, y_g, a_n, b_n, scelta);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% COSTRUZIONE DELLE SOLUZIONI TECNOLOGICHE DA ANALIZZARE (INSIEME HS +FANS)

% DECIDO DI METTERE LE DIMENSIONI DEL DISSIPATORE E LE COORDINATE
% DELLE SORGENTI ALL'INTERNO DEI CAMPI DELLA SOLUZIONE PERCHÈ SONO
% DIPENDENTI DAL NUMERO DI VENTOLE UTILIZZATE. NATURALMENTE OCCORRE TENERE
% PRESENTE LE DIMENSIONI DEI COMPONENTI (IL CODICE NON LO FA) ED I
% COLLEGAMENTI ED I CONDENSATORI ELCO ETC...

%%% SOLUZIONI PER VENTOLA EBMW1G180dc
Soluzione(1)=struct('HS_type', 'all_aluminum', 'Fan', 'EBMW1G180_axial_DC', 'Nventole', 2, 'Apertura_impinge', 250,...
    'vent_type', {'impinge'}, 'ainit', 400, 'binit', 400, 'amax', 550, 'bmax', 600, 'XG', [65 200 335 65 200 335 65 200 335]...
    ,'YG',[50 50 50 200 200 200 350 350 350]); 
Soluzione(2)=struct('HS_type', 'all_aluminum', 'Fan', 'EBMW1G180_axial_DC', 'Nventole', 1.5, 'Apertura_impinge', 250,...
    'vent_type', {'impinge'}, 'ainit', 340, 'binit', 400, 'amax', 550, 'bmax', 600, 'XG', [57 170 283 57 170 283 57 170 283]...
    ,'YG',[50 50 50 200 200 200 350 350 350]); 
Soluzione(3)=struct('HS_type', 'all_alum_piastra_rame', 'Fan', 'EBMW1G180_axial_DC', 'Nventole', 2, 'Apertura_impinge', 250,...
    'vent_type', {'impinge'}, 'ainit', 400, 'binit', 400, 'amax', 550, 'bmax', 600, 'XG', [65 200 335 65 200 335 65 200 335]...
    ,'YG',[50 50 50 200 200 200 350 350 350]);
Soluzione(4)=struct('HS_type', 'all_alum_piastra_rame', 'Fan', 'EBMW1G180_axial_DC', 'Nventole', 1.5, 'Apertura_impinge', 250,...
    'vent_type', {'impinge'}, 'ainit', 340, 'binit', 400, 'amax', 550, 'bmax', 600, 'XG', [57 170 283 57 170 283 57 170 283]...
    ,'YG',[50 50 50 200 200 200 350 350 350]);

%%% SOLUZIONI PER VENTOLA EBM208ac
Soluzione(5)=struct('HS_type', 'all_aluminum', 'Fan', 'EBM208_axial_AC', 'Nventole', 2, 'Apertura_impinge', 250,...
    'vent_type', {'impinge'}, 'ainit', 470, 'binit', 400, 'amax', 550, 'bmax', 600, 'XG', [65 235 405 65 235 405 65 235 405]...
    ,'YG',[50 50 50 200 200 200 350 350 350]);  % qui le ventole sono + grosse
Soluzione(6)=struct('HS_type', 'all_alum_piastra_rame', 'Fan', 'EBM208_axial_AC', 'Nventole', 2, 'Apertura_impinge', 250,...
    'vent_type', {'impinge'}, 'ainit', 470, 'binit', 400, 'amax', 550, 'bmax', 600, 'XG', [65 235 405 65 235 405 65 235 405]...
    ,'YG',[50 50 50 200 200 200 350 350 350]);
Soluzione(7)=struct('HS_type', 'all_aluminum', 'Fan', 'EBM208_axial_AC', 'Nventole', 1.5, 'Apertura_impinge', 250,...
    'vent_type', {'impinge'}, 'ainit', 350, 'binit', 400, 'amax', 550, 'bmax', 600, 'XG', [57 175 293 57 175 293 57 175 293]...
    ,'YG',[50 50 50 200 200 200 350 350 350]);
Soluzione(8)=struct('HS_type', 'all_alum_piastra_rame', 'Fan', 'EBM208_axial_AC', 'Nventole', 1.5, 'Apertura_impinge', 250,...
    'vent_type', {'impinge'}, 'ainit', 350, 'binit', 400, 'amax', 550, 'bmax', 600, 'XG', [57 175 293 57 175 293 57 175 293]...
    ,'YG',[50 50 50 200 200 200 350 350 350]);

%%% SOLUZIONI PER VENTOLA EBM250ac (analizzo solo 1.5Vent perchè 2 sono troppo grosse)
Soluzione(9)=struct('HS_type', 'all_aluminum', 'Fan', 'EBM250_axial_AC', 'Nventole', 1.5, 'Apertura_impinge', 250,...
    'vent_type', {'impinge'}, 'ainit', 420, 'binit', 400, 'amax', 550, 'bmax', 600, 'XG', [65 210 355 65 210 355 65 210 355]...
    ,'YG',[50 50 50 200 200 200 350 350 350]);  % qui le ventole sono troppo grosse per usarne 2, guardo solo il caso 1.5
Soluzione(10)=struct('HS_type', 'all_alum_piastra_rame', 'Fan', 'EBM250_axial_AC', 'Nventole', 1.5, 'Apertura_impinge', 250,...
    'vent_type', {'impinge'}, 'ainit', 420, 'binit', 400, 'amax', 550, 'bmax', 600, 'XG', [65 210 355 65 210 355 65 210 355]...
    ,'YG',[50 50 50 200 200 200 350 350 350]);  % qui le ventole sono troppo grosse per usarne 2, guardo solo il caso 1.5

% Soluzione(2)=struct('HS_type', 'all_copper', 'Fan', 'EBMW1G180_axial_DC', 'Nventole', 2, 'Apertura_impinge', 250,...
%     'vent_type', {{'impinge', 'push'}});
% Soluzione(3)=struct('HS_type', 'plate_al_fin_cu', 'Fan', 'EBMW1G180_axial_DC', 'Nventole', 2, 'Apertura_impinge', 250,...
%     'vent_type', {{'impinge', 'push'}});
% Soluzione(6)=struct('HS_type', 'all_copper', 'Fan', 'EBM208_axial_AC', 'Nventole', 2, 'Apertura_impinge', 250,...
%     'vent_type', {{'impinge', 'push'}});
% Soluzione(7)=struct('HS_type', 'plate_al_fin_cu', 'Fan', 'EBM208_axial_AC', 'Nventole', 2, 'Apertura_impinge', 250,...
%     'vent_type', {{'impinge', 'push'}});
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% SCELTA DEI PUNTI DEL PLATE DOVE CALCOLARE LE TEMPERATURE SU CASI SPOT
%% DEL RESULTS

%% decido la suddivisione in punti del baseplate del dissipatore
NpX=40;  NpY=40;  %fisso qui il numero dei punti che voglio sulla X e sulla Y



