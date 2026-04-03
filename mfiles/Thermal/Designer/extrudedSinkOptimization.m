clear all
close all
clc

thickFin0 = 0.8*10^-3;
optParam0 = [thickFin0];

for i = 4:15
    depthChannel = i*10^-3;
    lb = [0.2*10^-3];
    ub = [1.5*10^-3];

    fun = @(optParam) extrudedSinkObjectiveFun(optParam, depthChannel);
    
    opts = optiset('solver','nlopt','solverOpts',nloptset('algorithm','LN_SBPLX'));
%     opts = optiset('solver','nlopt','tolrfun',0.00000000001,'solverOpts',nloptset('algorithm','LN_SBPLX'));
%     opts = optiset('solver','ipopt');
%     opts = optiset('solver','lbfgsb');
    Opt = opti('fun',fun,'bounds',lb,ub,'x0',optParam0,'options',opts);
    [x1] = solve(Opt);
    depthChannelArr(i-3) = depthChannel;
    xArr(i-3,1) = x1(1);
%     xArr(i-29,2) = x1(2);
    rThSinkArr(i-3) = fun(x1);
end

hold on

yyaxis left
xlabel('depth of channel [mm]')
ylabel('Rth contact area to fluid [K/W]')
plot(depthChannelArr*10^3, rThSinkArr)

yyaxis right
plot(depthChannelArr*10^3, xArr(:,1)*10^3)
ylabel('wall thickness [mm]')

hold off

