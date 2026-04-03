%% This file hold all necessary data to define the HS tecnology under the
%% technical and economical point of view.


function [Kth_plate, Kth_fin, Kth_piastra, Cost_kg, Piastra, rho_plate_fin_piastra]=HS_Tech(HS_name)

%% Add a new structure element for each new Heatsink structure
HS_Type(1)=struct('Name', 'all_aluminum', 'K_fin', 200, 'K_plate', 200, 'K_piastra', 0, 'Price_kg', 10, 'Piastra', 'no', 'rho_plate_fin_piastra', [2700 2700 8230]);
HS_Type(2)=struct('Name', 'all_copper', 'K_fin', 350, 'K_plate', 350, 'K_piastra', 0, 'Price_kg', 22, 'Piastra', 'no', 'rho_plate_fin_piastra', [8230 8230 8230]);
HS_Type(3)=struct('Name', 'plate_al_fin_cu', 'K_fin', 350, 'K_plate', 200, 'K_piastra', 0, 'Price_kg', 18, 'Piastra', 'no', 'rho_plate_fin_piastra', [2700 8230 8230]);
HS_Type(4)=struct('Name', 'all_alum_piastra_rame', 'K_fin', 200, 'K_plate', 200, 'K_piastra', 350, 'Price_kg', 18, 'Piastra', 'yes', 'rho_plate_fin_piastra', [2700 2700 8230]);

t={HS_Type.Name};
n = strmatch(HS_name, t,'exact'); % trovo l'indice della struttura che contiene tutti i dati di cui ho bisogno

Kth_fin=HS_Type(n).K_fin; 
Kth_plate=HS_Type(n).K_plate; 
Kth_piastra=HS_Type(n).K_piastra; 
Cost_kg=HS_Type(n).Price_kg;
Piastra=HS_Type(n).Piastra;
rho_plate_fin_piastra=HS_Type(n).rho_plate_fin_piastra;