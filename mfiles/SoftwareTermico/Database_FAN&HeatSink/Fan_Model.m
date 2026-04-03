%% This File holds data that identify the fan model choosea among those
%% here specified

function [Hv, Qv, Qvmin, Qvmax, Cost_Fan, Volume_Fan]=Fan_Model(fan_name)

%% Tutti i costi sono in CHF
% 
% Qv= portata aria in m3/h
% Hv= pressione (in Pa) relativa ai punti inseriti per Qv (1incH2O=248.76Pa, 1incH2O=9.80665Pa)
% http://www.translatorscafe.com/cafe/EN/units-converter/flow/
% Qmin e Qmax = secondo ed penultimo punto di Qv/3600
% Volume = dimensioni del ventilatore

Fan(1)=struct('Name', 'EBMW1G180_axial_DC', 'Qv', [0, 400, 500, 600, 700, 800, 920]/3600,...
    'Hv', [710, 300, 288, 250, 180, 100, 0], 'Qmin', 400/3600, 'Qmax', 800/3600, 'Cost', 108, 'Volume', (70*pi*(200/2)^2)/10^9);
Fan(2)=struct('Name', 'EBM208_axial_AC', 'Qv', [0, 500, 600, 700, 800]/3600,...
    'Hv', [200, 135, 107, 70, 0], 'Qmin', 500/3600, 'Qmax', 750/3600, 'Cost', 71, 'Volume', (80*pi*(225/2)^2)/10^9);
Fan(3)=struct('Name', 'EBM250_axial_AC', 'Qv', [0, 1200, 1400, 1600, 1850]/3600,...
    'Hv', [220, 105, 85, 60, 0], 'Qmin', 1200/3600, 'Qmax', 1800/3600, 'Cost', 103, 'Volume', (80*pi*(280/2)^2)/10^9);  
Fan(4)=struct('Name', 'EBM_4118_NH4', 'Qv', [0 104 150 188 244 304 358]/3600,...
    'Hv', [357 224 193 184 148 86 0], 'Qmin', 120/3600, 'Qmax', 300/3600, 'Cost', 49, 'Volume', (119*119*38)/10^9); 
Fan(5)=struct('Name', 'EBM_4118_NH6', 'Qv', [0 40 80 130 170 300 400 440]/3600,...
    'Hv', [660 600 500 400 320 280 120 0], 'Qmin', 40/3600, 'Qmax', 400/3600, 'Cost', 75, 'Volume', (119*119*38)/10^9); 
Fan(6)=struct('Name', 'EBM208_axial_AC_60Hz', 'Qv', [0, 650, 720, 800, 925]/3600,...
    'Hv', [200, 135, 107, 70, 0], 'Qmin', 500/3600, 'Qmax', 800/3600, 'Cost', 71, 'Volume', (80*pi*(225/2)^2)/10^9);
Fan(7)=struct('Name', 'EBMW1G208_axial_DC', 'Qv', [370, 500, 600, 676, 760, 930, 1050]/3600,...
    'Hv', [300, 225, 200, 185, 150, 75, 0], 'Qmin', 400/3600, 'Qmax', 930/3600, 'Cost', 180, 'Volume', (80*pi*(210/2)^2)/10^9);
Fan(8)=struct('Name', 'Sunon_DP200_2123XBT_AC_60Hz', 'Qv', [0 25 50 76 101 126 152 177 194]/3600,...
    'Hv', [97 87 72 40 32 29 25 15 0], 'Qmin', 25/3600, 'Qmax', 177/3600, 'Cost', 20, 'Volume', (119*119*38)/10^9);
Fan(9)=struct('Name', 'Sunon_DP200_2123XBT_AC_50Hz', 'Qv', [0 25 50 76 101 126 152 164]/3600,...
    'Hv', [84 77 62 33 28 25 12 0], 'Qmin', 25/3600, 'Qmax', 152/3600, 'Cost', 20, 'Volume', (119*119*38)/10^9);
Fan(10)=struct('Name', 'EBMW2E200_axial_AC_50Hz', 'Qv', [0,150,300,375,450,525,600,750,915]/3600,...
    'Hv', [165,140,120,105,100,95,85,60,0], 'Qmin', 150/3600, 'Qmax', 800/3600, 'Cost', 71, 'Volume', (80*pi*(225/2)^2)/10^9);
Fan(11)=struct('Name', 'EBMW2E142BB_AC_50Hz', 'Qv', [0,15,65,95,125,150,180,265,285,310,340]/3600,...
    'Hv', [164,160,140,120,100,80,60,50,40,20,0], 'Qmin', 15/3600, 'Qmax', 310/3600, 'Cost', 71, 'Volume', (80*pi*(225/2)^2)/10^9);
Fan(12)=struct('Name', 'EBMACi_4420HH_AC', 'Qv', [0,5,13,24,37,52,68,86,108,137,149,159,164,170,176,180]/3600,...
    'Hv', [72,70,65,60,55,50,45,40,35,30,25,20,15,10,5,0], 'Qmin', 13/3600, 'Qmax', 176/3600, 'Cost', 24, 'Volume', (119*119*38)/10^9);

Hvtemp = [36.2830   34.8272   33.3714   31.9156   30.0119   27.9961   25.9804   23.6287   21.5010   19.3733, ...
   17.1336   15.6778   14.4460   12.7662   11.8704   10.8625   10.1906    9.0708    7.8389    6.7191, ...
    5.2633    4.1434    2.5756    1.3438    0.2240];

Qvtemp = [0    1.9988    3.9977    5.8299    8.1619   10.8270   13.4921   16.8235   20.3215   24.1526, ...
    28.4834   31.3151   34.1468   38.3110   40.9761   43.9744   46.3064   49.8043   52.9692   55.4677, ...
    58.1328   59.9651   62.1305   63.7962   64.9622];

Fan(13)=struct('Name', 'JF0825-1H-02', 'Qv', Qvtemp,...
    'Hv', Hvtemp, 'Qmin', Qvtemp(2), 'Qmax', Qvtemp(end-1), 'Cost', 24, 'Volume', (80*80*25.4));


%% Creo la cell con tutte le stringhe dei nomi presenti come elementi
%% singoli
t={Fan.Name};
n = strmatch(fan_name, t,'exact'); % trovo l'indice della struttura che contiene tutti i dati di cui ho bisogno

Hv=Fan(n).Hv; 
Qv=Fan(n).Qv; 
Qvmin=Fan(n).Qmin; 
Qvmax=Fan(n).Qmax; 
Cost_Fan=Fan(n).Cost;
Volume_Fan=Fan(n).Volume;