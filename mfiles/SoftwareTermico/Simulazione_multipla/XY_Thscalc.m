%% Funzione che calcola lee cordinate dei punti ove calcolare la
%% temperatura nel calcolo multiplo in funzione della scelta sotto il
%% modulo oppure a fianco del modulo.Viene chiamata da Dati come
%% inizializzazione e poi da simulazione multipla ad ogni iterazione quando
%% allargo il dissipatore per ricalcolare i punti dove la temperatura deve
%% essere calcolata

function [xThs, yThs]=XY_Thscalc(x_g, y_g, a_n, b_n, scelta)

if strcmp(scelta,'centro')           % per la creazione del vettore vedi nota sul xThs ed yThs
    xThs=x_g; yThs=y_g;
else
    i1=0;    %Questo è un contatore che uso per mettere le coordinate nei punti giusti del vettore 
    for i=1:length(x_g)
        % se devo calcolare le T a lato, il vettore delle coordinate dei
        % punti di calcolo viene creato in maniera da avere vicini i punti
        % relativi allo stesso IGBT . Cosi' i primi due pti si riferiscono
        % all'igbt nella colonna(1) e riga(1), i pti 3 e 4 si riferiscono a
        % colonne(2), righe(2) etc...Inoltre il primo dei due punti è nella
        % posizione basso/sx, mentre l'altro è nella posizione alto/dx a
        % seconda che l'IGBT sia disposto orizzontale o verticale.
        if a_n(i)>b_n(i)  % il lato lungo è a_n quindi parallelo ad X
            xThs(i+i1)=x_g(i); xThs(i+i1+1)=x_g(i);
            yThs(i+i1)=y_g(i)-bn(i)/2; % punto in basso
            yThs(i+i1+1)=y_g(i)+bn(i)/2; % punto in alto
        else  % il lato lungo è b_n quindi parallelo ad Y
            xThs(i+i1)=x_g(i)-a_n(i)/2; % punto a sx
            xThs(i+i1+1)=x_g(i)+a_n(i)/2; % punto a dx
            yThs(i+i1)=y_g(i); yThs(i+i1+1)=y_g(i);
        end
        i1=i1+1;
    end
end