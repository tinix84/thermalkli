%La funzione calcola la temperatura sulla superficie del baseplate nel
%punto le cui coordinate sono passate come ingressi alla funzione stessa
%Vengono passati due vettori Xp ed Yp che contengono le coordinate x,y dei punti
%nei quali vogliamo calcolare la temperatura.
%Viene passato anche un valore Niter che specifica il numero di iterazioni
%che occorre fare per ogni calcolo, a seconda della precisione richiesta.

function [DTheta, Ths]=Temp_calc(Xp, Yp, Niter, Piastra, p_n, a, b, x_g, y_g,...
     Kth_plate, tb, a_n, b_n, Kth_piastra, tr, Th_BP, hf_eq)

%Xp=vettore delle ascisse dei punti dove voglio calcolare la temperatura [mm]

%Yp=vettore delle ordinate dei punti dove voglio calcolare la temperatura%[mm]
%Niter=numero delle iterazioni per il calcolo della T dovuta alla singola
    %sorgente in un punto
%Piastra= quando è 'yes' significa che è presente la piastra aggiuntiva
%Dis=Disosizione IGBT considerata. E' una struttura che contiene tutte le
    %informazioni relative agli IGBT posizionate sul dissipatore.
   
   
DTheta=0;  %inizializzazione 
for f=1:length(p_n)
    if strcmp(Piastra, 'yes')==1
        Ao=(p_n(f)/(a*b/10^6))*(tb/(Kth_plate*10^3)+tr/(Kth_piastra*10^3)+1/hf_eq);
    else 
        Ao=(p_n(f)/(a*b/10^6))*(tb/(Kth_plate*10^3)+1/hf_eq);
    end
    DTheta=DTheta+Ao+ThetaX(Xp, x_g(f), Niter, p_n(f), a, b, a_n(f), Kth_plate, Kth_piastra, tb, tr, hf_eq)+...
        ThetaY(Yp, y_g(f), Niter, p_n(f), a, b, b_n(f), Kth_plate, Kth_piastra, tb, tr, hf_eq)+...
        ThetaXY(Xp, Yp, x_g(f), y_g(f), Niter, p_n(f), a, b, a_n(f), b_n(f), Kth_plate, Kth_piastra, tb, tr, hf_eq);
 
end


Ths=Th_BP+DTheta;
    
%% Qui elenco alcune funzioni che mi servono per il calcolo della temerpatura sul baseplate    
    function ThetaX=ThetaX(x, Xc, Niter, Qs, a, b, digbt, Kth_plate, Kth_piastra, tb, tr, hf_eq)
        %x=ascissa del punto dove voglio conoscere la Temp [mm]

        %Xc=ascissa di baricentro della sorgente considerata [mm]
        %Yc=ordinata di baricentro della sorgente considerata [mm]
        %Qs=potenza termica della sorgente considerata [W]
        ThetaX=0;
        for m=1:Niter
            lambda_m=m*pi/(a/1000);
            A1=(2*Qs*(sin((2*Xc/1000+digbt/1000)*lambda_m/2)-sin((2*Xc/1000-digbt/1000)*lambda_m/2)))...
               /(a*b*digbt*Kth_plate*lambda_m^2*Psicalc(lambda_m, Kth_piastra, Kth_plate, tb, tr, hf_eq)/10^9);
            ThetaX=ThetaX+A1*cos(lambda_m*x/1000);
        end
    end
    
    function ThetaY=ThetaY(y, Yc, Niter, Qs, a, b, higbt, Kth_plate, Kth_piastra, tb, tr, hf_eq)
        %y=ordinata del punto dove voglio conoscere la Temp [mm]
        %Xc=ascissa di baricentro della sorgente considerata [mm]
        %Yc=ordinata di baricentro della sorgente considerata [mm]
        %Qs=potenza termica della sorgente considerata [W]
        ThetaY=0;
        for n=1:Niter
            delta_n=n*pi/(b/1000);
            A2=(2*Qs*(sin((2*Yc/1000+higbt/1000)*delta_n/2)-sin((2*Yc/1000-higbt/1000)*delta_n/2)))...
                /(a*b*higbt*Kth_plate*delta_n^2*Psicalc(delta_n, Kth_piastra, Kth_plate, tb, tr, hf_eq)/10^9);
            ThetaY=ThetaY+A2*cos(delta_n*y/1000);
        end
    end

    function ThetaXY=ThetaXY(x, y, Xc, Yc, Niter, Qs, a, b, digbt, higbt, Kth_plate, Kth_piastra, tb, tr, hf_eq)
        %x=ascissa del punto dove voglio conoscere la Temp [mm]
        %y=ordinata del punto dove voglio conoscere la Temp [mm]
        %Xc=ascissa di baricentro della sorgente considerata [mm]
        %Yc=ordinata di baricentro della sorgente considerata [mm]
        %Qs=potenza termica della sorgente considerata [W]
        ThetaXY=0;
        for m=1:Niter
            lambda_m=m*pi/(a/1000);
            for n=1:Niter
                delta_n=n*pi/(b/1000);
                beta_mn=sqrt(lambda_m^2+delta_n^2);
                A3=(16*Qs*cos(lambda_m*Xc/1000)*sin(lambda_m*digbt/2000)*cos(delta_n*Yc/1000)*sin(delta_n*higbt/2000))...
                    /(a*b*digbt*higbt*Kth_plate*beta_mn*lambda_m*delta_n*Psicalc(beta_mn, Kth_piastra, Kth_plate, tb, tr, hf_eq)/10^12);
                ThetaXY=ThetaXY+A3*cos(lambda_m*x/1000)*cos(delta_n*y/1000);
            end
        end
    end

    function Psicalc=Psicalc(eps, Kth_piastra, Kth_plate, tb, tr, hf_eq)
        if strcmp(Piastra,'yes')==1
            rho=(eps+hf_eq/Kth_piastra)/(eps-hf_eq/Kth_piastra);
            alfa=(1-Kth_piastra/Kth_plate)/(1+Kth_piastra/Kth_plate);
            psiN=alfa*exp(4*eps*tb/1000)-exp(2*eps*tb/1000)+rho*(exp(2*eps*(2*tb/1000+tr/1000))-alfa*exp(2*eps*(tb/1000+tr/1000)));
            psiD=alfa*exp(4*eps*tb/1000)+exp(2*eps*tb/1000)+rho*(exp(2*eps*(2*tb/1000+tr/1000))+alfa*exp(2*eps*(tb/1000+tr/1000)));
            Psicalc=psiN/psiD;
           
            
        else
            Psicalc=(eps*sinh(eps*tb/1000)+(hf_eq/Kth_plate)*cosh(eps*tb/1000))/(eps*cosh(eps*tb/1000)+...
                (hf_eq/Kth_plate)*sinh(eps*tb/1000));
            
        end
    end
end
    