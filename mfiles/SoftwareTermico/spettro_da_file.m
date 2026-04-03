% per acquisire i punti da lecroy (cioe' da file esterno)
filename='SC1001.DAT';

choice_f=menu('frequenza',' EU 50Hz ',' UL 60 Hz ');

	switch choice_f
   
		case 1,   
		fond_freq=50; % frequenza della fondamentale

		case 2,
		fond_freq=60; % frequenza della fondamentale
      
   end
   
   choice_samp=menu('campionamento',' 500KS/s ',' 1MS/s ','altro');

	switch choice_samp
   
		case 1,   
		np=500e3/fond_freq; % numero di punti acquisiti (o da considerare)
		case 2,
		np=1e6/fond_freq; % numero di punti acquisiti (o da considerare)
      case 3,
      samp =input('sampling frequency (Samples/s): ');
		np=samp/fond_freq;
   end

   
fID=fopen(filename,'r');

[Vexp,count]=fscanf(fID,'%f',np);

spec=(fft(Vexp))/np*2;
spec(1)=0; % tolta la componente continua
spec=spec(1:np/2);
asc=[0:fond_freq:(fond_freq*(np/2-1))];
specr = spec/abs(spec(2));
Pspectot=spec'*spec;
Pspec0 = spec(2)*conj(spec(2));
specthd=100*sqrt(Pspectot-Pspec0)/sqrt(Pspec0);



%sfasamenti delle armoniche
ph_fond = angle(specr(2))    %sfasamento della fondamentale
ph_3 = (angle(specr(4))-ph_fond)*360/(2*pi)
ph_5 = (angle(specr(6))-ph_fond)*360/(2*pi)
ph_7 = (angle(specr(8))-ph_fond)*360/(2*pi)

abs_3 = abs(specr(4))
abs_5 = abs(specr(6))
abs_7 = abs(specr(8))


figure(1)
clf;
plot( asc, abs(specr),'-');
grid on;
title('Spettro segnale');
xlabel(['specTHD ' num2str(specthd) '%']);
zoom;


figure(2)
clf;
plot(Vexp,'-');
grid on;
title('segnale');
zoom;
