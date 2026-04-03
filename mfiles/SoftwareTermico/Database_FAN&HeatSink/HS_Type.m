%% This file hold all necessary data to define the HS type

%tb= spessore base (mm)
%Hf= altezza aletta (mm)
%tf= spessore aletta (mm)
%bch= larghezza canale (mm)

function [tb, Hf, tf, bch]=HS_Type(HS_name)

%% Add a new structure element for each new Heatsink structure
%% Triphase section 
HS_Type(1)=struct('Name', 'I117', 'tb', 15, 'Hf', 102, 'tf', 1.7, 'bch', 4.3);
HS_Type(2)=struct('Name', 'I76', 'tb', 15, 'Hf', 61, 'tf', 1.3, 'bch', 2.7);
HS_Type(3)=struct('Name', 'P443', 'tb', 17.5, 'Hf', 60, 'tf', 3, 'bch', 6.8);
HS_Type(4)=struct('Name', 'P309', 'tb', 15, 'Hf', 47.5, 'tf', 2.2, 'bch', 3.8);
HS_Type(5)=struct('Name', 'P390', 'tb', 14, 'Hf', 70, 'tf', 1.4, 'bch', 4.1);
HS_Type(6)=struct('Name', 'P612', 'tb', 14, 'Hf', 103, 'tf', 2, 'bch', 4);
HS_Type(7)=struct('Name', 'P573', 'tb', 16.5, 'Hf', 60.5, 'tf', 1.7, 'bch', 2.3);
HS_Type(8)=struct('Name', 'I98T', 'tb', 26, 'Hf', 72, 'tf', 1.3, 'bch', 4.7);
HS_Type(9)=struct('Name', 'SOCO', 'tb', 15, 'Hf', 62, 'tf', 1.5, 'bch', 4);
HS_Type(10)=struct('Name', 'P442', 'tb', 15, 'Hf', 39, 'tf', 1, 'bch', 3.5);
HS_Type(11)=struct('Name', 'I100A', 'tb', 16, 'Hf', 78, 'tf', 1.3, 'bch', 3.2);
HS_Type(12)=struct('Name', 'I54', 'tb', 13, 'Hf', 41.5, 'tf', 1, 'bch', 2.5);
HS_Type(13)=struct('Name', 'Pada SF', 'tb', 15, 'Hf', 100, 'tf', 2, 'bch', 3);

%% Single phase section
%HS_Type(14)=struct('Name', 'VHBigHeatsink30mm', 'tb', 4, 'Hf', 26, 'tf', 1, 'bch', 5.2);
HS_Type(14)=struct('Name', 'VHSmallHeatsink28mm', 'tb', 4, 'Hf', 26, 'tf', 1.67, 'bch', 6);
HS_Type(15)=struct('Name', 'VHSmallHeatsink30mm', 'tb', 4, 'Hf', 24, 'tf', 1, 'bch', 5.2);

%% Resolution 
t={HS_Type.Name};
n = strmatch(HS_name, t,'exact'); % trovo l'indice della struttura che contiene tutti i dati di cui ho bisogno

tb=HS_Type(n).tb; 
Hf=HS_Type(n).Hf; 
tf=HS_Type(n).tf; 
bch=HS_Type(n).bch;
