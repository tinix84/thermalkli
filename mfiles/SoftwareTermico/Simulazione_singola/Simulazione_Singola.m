close all
clear all

%% SIMULAZIONE SINGOLA
%% calcola la distribuzione della temepratura relativa al caso definito in
%% Dati.m

Tin=40;  %temperatura aria ingresso (°C)
Dati   %% Carico tutti i dati 

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% CALCOLO IL PUNTO DI FUNZIONAMENTO IDRAULICO.Re_hydr è il numero di Re
%% medio. Serve per controllare i limiti di validità delle relazioni
%% empiriche usate. Qv_f ed Hv_f è il punto di funzionamento calcoato per la
%% ventola (Qv_f è la portata della ventola equivalente).

if strcmp(calc_mode,'auto')==1
    
[Re_hydr, Hv_f, Qv_f]=idraulico(b, s, Nf, tf, bch, Hf, Tair, vent_type, Qv, Hv);
else
    Qv_f=Qguess;
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% CALCOLO LA RESISTENZA TERMICA EQUIVALENTE DELLE ALETTE

%% Re_therm è il numero di Re medio termico. Serve per verificare la
%% validità delle formule empiriche usate.
%Vch1=velocità aria nel canale verticale; (solo in impinge)[m/s]
%Vch2=velocità aria nel canale orizzontale; [m/s] (direzione Y)
%Rth_fin=resistenza termica equivalente delle alette [°C/W]
%hf_eq=conducibilità termica equivalente alette [W/(°C*m^2)]
Tair=Tin+0.5*sum(p_n)/(Cp_air(Tin)*rho_air(Tin)*Qv_f); %ricalcolo la Tair ora che conosco la reale portata
[Re_therm, Vch1, Vch2, Rth_fin, hf_eq]=Rth_fin(Qv_f, a, b, s, tf, bch, Hf, Tair, vent_type, Kth_fin, Nf);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% CALCOLO LA DISTRIBUZIONE DI TEMPERATURE SUL PLATE

%% decido la suddivisione in punti del baseplate del dissipatore
Xp=0:a/40:a; Yp=0:b/40:b;

%% su tutti i punti definiti sopra, calcolo la distribuzione di temepratura
Niter=25; % in base ad alcuni test abbiamo visto che sopra 25 iterazioni non cambia nulla nel calcolo dell temperature

% metto qui il calcolo della Tairmax perchè solo ora conosco la reale Qv_f
%Tairmax=Tin+sum(p_n)/(Cp_air(Tin)*rho_air(Tin)*Qv_f); % per il calcolo dell'LMTD occorre la Tair max

[Ths, Th_BP]=Tplane_dist(Rth_fin, p_n, Tair, Tin, Niter, Piastra, a, b, x_g, y_g,...
    Kth_plate, tb, a_n, b_n, Kth_piastra, tr, hf_eq, Xp, Yp)

