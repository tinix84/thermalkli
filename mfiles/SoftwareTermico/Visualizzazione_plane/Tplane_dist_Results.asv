%% Questo file usa il Tplane_dist come core per il calcolo ed il relativo
%% plottaggio delle temeprature sul plate, ma ricava i dati che servono
%% agendo sui diversi campi del Results che contiene i risultati delle
%% analisi di ottimizzazione.

function[Rth_fin]=Tplane_dist_Results(Titolo, Results)

%% Titolo= il nome dell'analisi da caricare (se non già presente nel Wspace)
%% Results=il risultato tra i tanti presenti nell'analisi che si vuole plottare

if ~exist('Titolo', 'var')
       load(['D:\Documents and Settings\120006009\My Documents\Software Termico\Database_risultati\' Titolo]);
end

   Rth_fin= Results.Rth_fin;
   p_n=Results.Perdite_componenti_W;
   Tair=Results.Temp_media_aria;
   Tin=Results.Temperatura_aria_gC;
   Niter=Results.Niterazioni;
   if Results.Spessore_Piastra_mm ~=0
       Piastra='yes';
   else
       Piastra='no';
   end
   a=Results.Dim_X_mm;
   b=Results.Dim_Y_mm;
   x_gg=Results.Coordinata_X_comp_mm
   y_gg=Results.Coordinata_Y_comp_mm
   Kth_plate=Results.HS_Tech(1);
   tb=Results.Spess_plate_mm;
   a_n=Results.Dim_componente_X_mm;
   b_n=Results.Dim_componente_Y_mm;
   Kth_piastra=Results.HS_Tech(3);
   tr=Results.Spessore_Piastra_mm;
   hf_eq=Results.hf_eq_fin;
   Xp=Results.Punti_Xp_Tplane;
   Yp=Results.Punti_Yp_Tplane;
   
   
   
  
 [Ths, Th_BP]=Tplane_dist(Rth_fin, p_n, Tair, Tin, Niter, Piastra, a, b, x_gg, y_gg,...
    Kth_plate, tb, a_n, b_n, Kth_piastra, tr, hf_eq, Xp, Yp)


end
