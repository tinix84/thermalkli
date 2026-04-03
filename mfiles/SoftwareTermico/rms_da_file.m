
clear;
home;
% per acquisire i punti da lecroy o da goliath (cioe' da file esterno)
filename='ref.dat';  % segnale da elaborare

freq_sig=menu('frequenza segnale',' EU 50Hz ',' UL 60 Hz ');
	switch freq_sig
   	case 1,   
		fond_freq=50; % frequenza della fondamentale
		case 2,
		fond_freq=60; % frequenza della fondamentale
   end

% scelta della freq. di campionamento
% Goliath campiona ad ogni accesso alla routine di interrupt
% Lecroy lo si imposta generalmente a 500kS/s

freq_sample=menu('frequenza acquisizione',' Goliath 50us ',' Goliath 100us ','Lecroy 500kS/s',' altro ');
	switch freq_sample
   	case 1,
      freqC = 20e3; 
      case 2,
      freqC = 10e3;
		case 3,   
		freqC = 500e3;   %frequenza di campionamento Lecroy (sample/sec)
		case 4,
      % inserire la freq. di campionamento   
      freqC =input('sampling frequency: ');
   end
   
   % il file proveniente da goliath contiene N colonne, corrispondenti
   % ai segnali acquisiti. La prima colonna è il tempo.
   % il programma preleva la N-esima colonna dal file .dat consentendo
   % dunque di fare acquisizioni multiple su goliath.
   
   if freq_sample < 5,
  
   N=menu('number of acquired signals',' 1 ',' 2 ',' 3 ',' 4 ',' more ');
	if N == 5,
      % inserire il n. di segnali   
      N =input('number of acquired signals: ');
   end
   N = N+1;
    num=menu('signal to be processed',' 1° ',' 2° ',' 3° ',' 4° ',' more ');
	if num == 5,
      % inserire il segnale da elaborare   
      num =input('signal to be processed: ');
   end
   num = num + 1;
   
np=freqC/fond_freq; % numero di punti acquisiti (o da considerare). E' sempre 1 periodo
fID=fopen(filename,'r');
[Vexp,count]=fscanf(fID,'%f',N*np);

for s = 1:np,
   Vexpr(s) = Vexp(N*(s-1)+num);
end
Vexp = Vexpr;

else   % se il segnale proviene da LeCroy
   np=freqC/fond_freq;
   fID=fopen(filename,'r');
   [Vexp,count]=fscanf(fID,'%f',np);
end

% calcolo rms del segnale
spacing = 1/freqC;            %distanza tra 2 campioni
T = 1/fond_freq;				   % periodo
f2=real(Vexp).^2;				   % vettore somma qudratica
integ = spacing*trapz(f2);    %calcolo integrale
rms = sqrt((1/(T))*integ)     %calcolo rms
peak = max(real(Vexp))        %valore di picco

% visualizzazioni
Tp = spacing*[0:np-1];
figure(1)
clf;
plot( Tp,Vexp,'-');
grid on;
title('segnale');
xlabel(['RMS ' num2str(rms)]);

hold on;
ord = rms*ones(np,1);
plot(Tp,ord,'r');
grid
zoom

