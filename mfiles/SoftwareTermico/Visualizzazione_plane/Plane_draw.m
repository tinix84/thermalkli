%% Plane_draw: verifica la corretta distribuzione delle sorgenti sul
%% dissipatore
%% Quando uso lo script da dati provenienti da risultati, devo generare le
%% informazioni necessarie:
%% a=Results(n).Dim_X_mm;
%% b=Results(n).Dim_Y_mm;
%% x_g1=Results(n).Coordinata_X_comp_mm;
%% y_g1=Results(n).Coordinata_Y_comp_mm;
%% a_n=Results(n).Dim_componente_X_mm;
%% b_n=Results(n).Dim_componente_Y_mm;

figure
axis equal
rectangle('Position',[0,0,a,b]);


for nn=1:length(p_n)
    rectangle('Position',[(x_g1(nn)-a_n(nn)/2),(y_g1(nn)-b_n(nn)/2),a_n(nn),b_n(nn)]);
end