%%% DATI PER LA SIMULAZIONE DEI DISSIPATORI

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% STEP 0: DEFINIZIONE INIZIALE DISSIPATORE

%% DATI GEOMETRICI:
%% LA DIMENSIONE X È QUELLA PERPENDICOLARE ALLE ALETTE; LA DIMENSIONE Y È
%% QUELLA PARALLELA ALLE ALETTE

a=650; % dimensione X (mm)
b=330; % dimensione Y (mm)        

% versione a menu per la selezione del tipo di dissipatore (aggiunta Teo 02.08.2011)
heatsink_type=menu('Profilo dissipatore','I117','I76','P443','P309','P390','P612','P573','I98T','SOCO','P442(H=54 P=4.5)','I100A','I54','Pada SF','VHSmallHeatsink28mm','VHSmallHeatsink30mm');
	switch heatsink_type
   	case 1,   
		heatsink_type='I117';
	case 2,
		heatsink_type='I76';
    case 3,
		heatsink_type='P443';
    case 4,
		heatsink_type='P309';
    case 5,
		heatsink_type='P390';
    case 6,
		heatsink_type='P612';
    case 7,
		heatsink_type='P573';
    case 8,
		heatsink_type='I98T';
    case 9,
		heatsink_type='SOCO';
    case 10,
		heatsink_type='P442';
	case 11,
		heatsink_type='I100A';
    case 12,
		heatsink_type='I54';
    case 13,
		heatsink_type='Pada SF'; 
    case 14,
		heatsink_type='VHSmallHeatsink28mm'; 
    case 15,
		heatsink_type='VHSmallHeatsink30mm'; 
    end

% versione per la selezione del tipo di dissipatore (aggiunta Teo luglio 2011)

% heatsink_type='I76';  % Questa stringa identifica il profilo del dissipatore dal file HS_Type

[tb, Hf, tf, bch]=HS_Type(heatsink_type)
if isempty(tb)==1
    msgbox('Ocio hai scritto male il modello del dissipatore. Guarda quelli disponibili nel file HS_Type.m')
end

tr=1; %spessore piastra aggiuntiva (mm) (non possiamo mettere zero)
Nf=round(a/(bch+tf)); % Numero di alette.


%% DATI FISICI:
tecnology='all_aluminum'; % 'plate_al_fin_cu''all_copper'  Questa stringa identifica un tipo di dissipatore all'interno del file HS_Tech.m
                            % okkio che bisogna scriverlo giusto, come scritto nel file HS_Tech.m

[Kth_plate, Kth_fin, Kth_piastra, Cost_kg, Piastra, rho_plate_fin_piastra]=HS_Tech(tecnology)
if isempty(Kth_plate)==1
    msgbox('Ocio hai scritto male il nome del dissipatore. Guarda quelli disponibili nel file HS_Tech.m')
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% STEP 1: PROCEDURA INIZIALIZZAZIONE SORGENTI

%% LA DIMENSIONE X È QUELLA PERPENDICOLARE ALLE ALETTE; LA DIMESIONE Y È
%% QUELLA PARALLELA ALLE ALETTE
%% IL FLUSSO D'ARIA E CONSIDERATO VERTICALE!!! 

% Ponte inv-rect SG20-40kVA I76 280x280 2 ventilatori-ACi4420HH SOT227
% a_n=[38 38 38 25 25 25 38 38 38 38 60 60];  % dimensione sorgenti parallela asse X
% b_n=[25 25 25 38 38 38 25 25 25 25 55 55]; %dimensione sorgenti parallela asse Y
% p_n=[125 150 125 125 150 125 125 150 125 150 400 400]; % losses of the sources
% x_g=[45 45 45 100 140 180 235 235 235 140 65 210]; % source centerpoint X coordinate
% y_g=[153 200 247 240 240 240 153 200 247 153 60 60]; % source centerpoint Y coordinate

% Ponte inv-rect SG20-40kVA I76 280x280 2 ventilatori-ACi4420HH
% a_n=[34 94 34 94 60 60];  % dimensione sorgenti parallela asse X
% b_n=[94 34 94 34 55 55]; %dimensione sorgenti parallela asse Y
% p_n=[350 350 350 100 411 411]; % losses of the sources
% x_g=[45 140 235 140 65 210]; % source centerpoint X coordinate
% y_g=[195 235 195 155 60 60]; % source centerpoint Y coordinate

% Ponte rect+inv SG40kVA I76 340x250 2 ventilatori 150x172 impinge
%  a_n=[94 94 94 94 60 60];  % dimensione sorgenti parallela asse X
%  b_n=[34 34 34 34 55 55]; %dimensione sorgenti parallela asse Y
%  p_n=[326 326 326 100 411 411]; % losses of the sources
%  x_g=[60 170 280 170 80 260]; % source centerpoint X coordinate
%  y_g=[200 200 200 150 60 60]; % source centerpoint Y coordinate

% Ponte bypass SG40kVA 160x100 I76 con flusso 0.005
% a_n=[40 40 40];  % dimensione sorgenti parallela asse X
% b_n=[28 28 28]; %dimensione sorgenti parallela asse Y
% p_n=[70 70 70]; % losses of the sources
% x_g=[30 80 130]; % source centerpoint X coordinate
% y_g=[50 50 50]; % source centerpoint Y coordinate

% ponte TL 160-200kVA semix3s dissipatore 425x160 (stile socomec)
% a_n=[115 115 115 115 115 115];  % dimensione sorgenti parallela asse X
% b_n=[55 55 55 55 55 55]; %dimensione sorgenti parallela asse Y
% p_n=[344 180 183 298 294 398]; % losses of the sources
% x_g=[80 80 80 80 80 80]; % source centerpoint X coordinate
% y_g=[35 102 169 236 303 370]; % source centerpoint Y coordinate

% ponte TL 200kVA Fuji dissipatore 550x140 I76
% a_n=[93 93 93 93 93 93];  % dimensione sorgenti parallela asse X
% b_n=[62 62 62 62 62 62]; %dimensione sorgenti parallela asse Y
% p_n=[450 450 450 450 450 450]; % losses of the sources
% x_g=[70 70 70 70 70 70]; % source centerpoint X coordinate
% y_g=[50 140 230 320 410 500]; % source centerpoint Y coordinate

% booster TL 200kVA Fuji dissipatore 550x180 I76
% a_n=[110 110 110 110];  % dimensione sorgenti parallela asse X
% b_n=[80 80 80 80]; %dimensione sorgenti parallela asse Y
% p_n=[850 850 850 850]; % losses of the sources
% x_g=[90 90 90 90]; % source centerpoint X coordinate
% y_g=[60 180 300 420]; % source centerpoint Y coordinate

% Ponte SSM TL 400kVA SKKT570(124x60) diss.370x190
% a_n=[124 124 124];  % dimensione sorgenti parallela asse X
% b_n=[60 60 60]; %dimensione sorgenti parallela asse Y
% p_n=[585 585 585]; % losses of the sources
% x_g=[95 95 95]; % source centerpoint X coordinate
% y_g=[50 182 320]; % source centerpoint Y coordinate

% Ponte SSM TL 200kVA SKKT250(92x50) diss.350x140
% a_n=[92 92 92];  % dimensione sorgenti parallela asse X
% b_n=[50 50 50]; %dimensione sorgenti parallela asse Y
% p_n=[290 290 290]; % losses of the sources
% x_g=[76.5 76.5 76.5]; % source centerpoint X coordinate
% y_g=[43 175 307]; % source centerpoint Y coordinate

% thyristor Powerex PD431207 per ponte SSM SG 600kVA I76 500x240
% a_n=[101.6 101.6 101.6];  % dimensione sorgenti parallela asse X
% b_n=[177.8 177.8 177.8]; %dimensione sorgenti parallela asse Y
% p_n=[1020 1020 1020]; % losses of the sources
% x_g=[74 250 426]; % source centerpoint X coordinate
% y_g=[120 120 120]; % source centerpoint Y coordinate

% thyristor Powerex PD431215 per ponte SSM SG 800kVA I76 650x330
% a_n=[177.8 177.8 177.8 177.8 177.8 177.8];  % dimensione sorgenti parallela asse X
% b_n=[101.6 101.6 101.6 101.6 101.6 101.6]; %dimensione sorgenti parallela asse Y
% p_n=[725 725 725 725 725 725]; % losses of the sources
% x_g=[110 110 325 325 540 540]; % source centerpoint X coordinate
% y_g=[90 240 90 240 90 240]; % source centerpoint Y coordinate

% Mitsubishi CM400DY-12NF inverter SG 600kVA@0.8 100%
% a_n=[108 108 108 108 108 108 108 108 108 50 50 50 50 50 50];  % dimensione sorgenti parallela asse X
% b_n=[62 62 62 62 62 62 62 62 62 16 16 16 16 16 16]; %dimensione sorgenti parallela asse Y
% p_n=[457 457 457 457 457 457 457 457 457 0 0 0 0 0 0]; % losses of the sources
% x_g=[70 70 70 200 200 200 330 330 330 70 200 330 70 200 330]; % source centerpoint X coordinate
% y_g=[80 250 410 80 250 410 80 250 410 472 472 472 497 497 497]; % source centerpoint Y coordinate

% Mitsubishi CM600DY-12NF inverter SG 600kVA@0.9 100%
% a_n=[110 110 110 110 110 110 110 110 110 50 50 50 50 50 50];  % dimensione sorgenti parallela asse X
% b_n=[80 80 80 80 80 80 80 80 80 16 16 16 16 16 16]; %dimensione sorgenti parallela asse Y
% p_n=[624 624 624 624 624 624 624 624 624 38 38 38 38 38 38]; % losses of the sources
% x_g=[70 70 70 200 200 200 330 330 330 70 200 330 70 200 330]; % source centerpoint X coordinate
% y_g=[80 250 410 80 250 410 80 250 410 472 472 472 497 497 497]; % source centerpoint Y coordinate

% IGBT rectifier 300kVA su scheda con dissipatore 520x465 4moduli/fase
% a_n=[106.4 106.4 106.4 106.4 106.4 106.4 106.4 106.4 106.4 106.4 106.4 106.4 94 94 94 94];  % dimensione sorgenti parallela asse X
% b_n=[61.4 61.4 61.4 61.4 61.4 61.4 61.4 61.4 61.4 61.4 61.4 61.4  34 34 34 34]; %dimensione sorgenti parallela asse Y
% p_n=[576 576 576 576 576 576 576 576 576 576 576 576 110 110 110 110]; % losses of the sources
% x_g=[76.2 232.7 389.2 76.2 232.7 389.2 76.2 232.7 389.2 76.2 232.7 389.2 145 319.5 145 319.5]; % source centerpoint X coordinate
% y_g=[63 63 63 198 198 198 322 322 322 457 457 457 132 132 388 388]; % source centerpoint Y coordinate

% Ponte 160kVA dissipatore I117(710x520) INV+IGBTrect+SSM orizzontali
% a_n=[62 62 62 62 62 62 16 16 16 106.4 106.4 106.4 106.4 106.4 106.4 94 94 94 94 94];  % dimensione sorgenti parallela asse X
% b_n=[108 108 108 108 108 108 50 50 50 61.4 61.4 61.4 61.4 61.4 61.4 34 34 34 34 34]; %dimensione sorgenti parallela asse Y
% p_n=[468 468 468 468 468 468 38 38 38 628 628 628 628 628 628 118 118 410 410 410]; % losses of the sources
% x_g=[94 94 94 210 210 210 25 25 25 405.5 608.5 405.5 608.5 405.5 608.5 507 507 320 468 616]; % source centerpoint X coordinate
% y_g=[154.5 299.5 444.5 154.5 299.5 444.5 154.5 299.5 444.5 120 120 285.5 285.5 449.5 449.5 203 368 40 40 40]; % source centerpoint Y coordinate

% Ponte 160kVA dissipatore I117(710x520) SSM orizzontali
% a_n=[92 92 92];  % dimensione sorgenti parallela asse X
% b_n=[50 50 50]; %dimensione sorgenti parallela asse Y
% p_n=[260 260 260]; % losses of the sources
% x_g=[320 468 616]; % source centerpoint X coordinate
% y_g=[40 40 40]; % source centerpoint Y coordinate

% Ponte SSM SG 500kVA SKET800(104x70) o MCO500 92x50 diss.I100A 530x200
% a_n=[50 50 50 50 50 50];  % dimensione sorgenti parallela asse X
% b_n=[92 92 92 92 92 92]; %dimensione sorgenti parallela asse Y
% p_n=[367 367 367 367 367 367]; % losses of the sources
% x_g=[45 133 221 309 397 485]; % source centerpoint X coordinate
% y_g=[100 100 100 100 100 100]; % source centerpoint Y coordinate

% Ponte LP10kVA 240x140 2 ventilatori
% a_n=[55 31 30 40 30];  % dimensione sorgenti parallela asse X
% b_n=[60 55 30 28 30]; %dimensione sorgenti parallela asse Y
% p_n=[340 250 115 90 126]; % losses of the sources
% x_g=[45 205 91.5 145 203]; % source centerpoint X coordinate
% y_g=[60 43 118 118 118]; % source centerpoint Y coordinate

% Ponte LP20kVA 360x180 3 ventilatori
% a_n=[55 55 31 31 30 40 34];  % dimensione sorgenti parallela asse X
% b_n=[60 60 55 55 30 28 34]; %dimensione sorgenti parallela asse Y
% p_n=[340 340 250 250 171 107 127]; % losses of the sources
% x_g=[50 150 245 320 190 260 330]; % source centerpoint X coordinate
% y_g=[50 50 55 55 150 150 150]; % source centerpoint Y coordinate

% VH small heatsink for inverter
b=130; % dimensione X (mm) perpendicolare all'aria
a=63; % dimensione Y (mm) parallela al flusso della ventola
a_n=[13 13 13 13 13];  % dimensione sorgenti parallela asse X
b_n=[13 13 13 13 13]; %dimensione sorgenti parallela asse Y
p_n=[0.1 30 30 30 30]; % losses of the sources
%y_g=[11 36 58.5 95 117]; % source centerpoint X coordinate
y_g=[119 94 71.5 35 13]
x_g=[16.5 16.5 16.5 16.5 16.5]; % source centerpoint Y coordinate

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% STEP 2: DEFINIZIONE VENTILAZIONE

%% TIPO DI VENTILAZIONE
% versione originale della scelta ventole
% vent_type= 'push' ; %   'impinge'
vent_type=menu('Scegliere modo di ventilazione','Impinge','Push');
    switch vent_type
    case 1,
        vent_type='impinge';
    case 2,
        vent_type='push' ;
    end
    
s=220; %% Apertura per impinge (mm)

%% CALCOLO AUTOMATICO O MANUALE
calc_mode='auto'; %'flux_spec'
flux=0.005; % imposed flux (m^3/s) usato solo se calc_mode = flux_spec. si intende la portata complessiva

%% SELEZIONE VENTOLE

% versione originale della scelta ventole
% fan_model= 'EBMW2E200_axial_AC_50Hz' ;

% versione a menu per la selezione del tipo di ventilatore (aggiunta Teo 02.08.2011)
fan_model=menu('Modello ventilatore','EBMW1G180_axial_DC','EBM208_axial_AC','EBM208_axial_AC_60Hz','EBM_4118_NH4','EBM_4118_NH6','EBM250_axial_AC','EBMW1G208_axial_DC','Sunon_DP200_2123XBT_AC_50Hz','Sunon_DP200_2123XBT_AC_60Hz','EBMW2E200_axial_AC_50Hz','EBMW2E142BB_AC_50Hz','EBMACi_4420HH_AC', 'JF0825-1H-02');
	switch fan_model
   	case 1,   
		fan_model='EBMW1G180_axial_DC';
	case 2,
		fan_model='EBM208_axial_AC';
    case 3,
		fan_model='EBM208_axial_AC_60Hz';
    case 4,
		fan_model='EBM_4118_NH4';
    case 5,
		fan_model='EBM_4118_NH6';
    case 6,
		fan_model='EBM250_axial_AC';
    case 7,   
		fan_model='EBMW1G208_axial_DC';
	case 8,
		fan_model='Sunon_DP200_2123XBT_AC_50Hz';
    case 9,
		fan_model='Sunon_DP200_2123XBT_AC_60Hz';
    case 10,
		fan_model='EBMW2E200_axial_AC_50Hz';
    case 11,
		fan_model='EBMW2E142BB_AC_50Hz';
    case 12,
		fan_model='EBMACi_4420HH_AC'; 
    case 13,
		fan_model='JF0825-1H-02';
   end

[Hv1, Qv1, Qvmin1, Qvmax1, Cost_Fan1, Volume_Fan1]=Fan_Model(fan_model)

% seguenti 3 righe da utilizzare solo con la versione originale della scelta ventole
% if isempty(Hv1)==1
%    msgbox('Ocio hai scritto male il nome della ventola. Guarda quelli disponibili nel file Fan_Model.m')
% end

%% SCELTA NUMERO VENTOLE IN PARALLELO

%scelta manuale del numero di ventilatori (aggiunta Teo 02.08.2011)
Nv=menu('Numero di ventilatori','1','2','3','4','more...');
	switch Nv
   	case 1,   
		Nv=1;
	case 2,
		Nv=2;
    case 3,
		Nv=3;
    case 4,
		Nv=4;
    case 5,
		Nv=input('Inserisci q.tà ventilatori: ');
   end

% Nv=1; % quantità di ventilatori
Qv=Nv*Qv1; % portata totale ventola equivalente
Hv=Hv1;
Qvmin=Nv*Qvmin1; % Portata minima ventola equivalente
Qvmax=Nv*Qvmax1; % Portata massima ventola equivalente
Cost_Fan=Nv*Cost_Fan1; % Costo totale ventole
Volume_Fan=Nv*Volume_Fan1; % Volume ingombro Fan (m^3)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% CALCOLO DATI DI PARTENZA PER CALCOLI IDRAULICI E TERMICI

% Calcolo Tair per le caratteristiche dell'aria 
if strcmp(calc_mode,'auto')==1
    Qguess=(Qvmin+Qvmax)/2; % portata di guess. Siccome il punto di funzionamento della ventola non è
                            % noto si ipotizza una media del campo di portate della ventola
else
    Qguess=flux;  % se voglio calcolare la termica saltando l'idraulica la portata è imposta e quindi nota
end

Tair=Tin+0.5*sum(p_n)/(Cp_air(Tin)*rho_air(Tin)*Qguess); % per il calcolo delle proprietà aria uso la T media
 






