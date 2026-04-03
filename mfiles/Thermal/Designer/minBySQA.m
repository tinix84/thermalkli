function [ x1, y1 ] = minBySQA( fun, x0L, x0U, lb, ub, maxIter, tolX, tolY )
%solveBySQA tries to minimize a scalar, nonlinear, convex, smooth problem
%of form f(x)= y by approximating the problem with a quadratic function
%   Detailed explanation goes here

    if nargin < 6
        maxIter = 1000;
        tolX = 10^-7;
    elseif nargin < 7
        tolX = 10^-7;
    elseif nargin < 8
        tolY = 10^-10;
    end
    

    xLow = min(x0L, x0U);
    yLow = fun(xLow);
    xUp = max(x0L, x0U);
    yUp = fun(xUp);
    xM = (xLow+xUp)/2;
    yM = fun(xM);
    if (yUp <= yLow) && (yUp <= yM)
        x1 = xUp;
        y1 = yUp;
    elseif (yLow <= yUp) && (yLow <= yM)
        x1 = xLow;
        y1 = yLow;
    else
        x1 = xM;
        y1 = yM;
    end
%     [ ~, x1 ] = simplQA( xLow, yLow, xUp, yUp );
    if xLow == xUp
        runIter = false;
    else
        runIter = true;
    end
    numIter = 0;
    while runIter
        numIter = numIter + 1;
        [ ~, xNew ] = quadAppr( xLow, yLow, xM, yM, xUp, yUp );
        if nargin > 3
            xNew = max(xNew, lb);
            xNew = min(xNew, ub);
        end
        yNew = fun(xNew);
        
        % very basic handling of nonconvex sections in the objective
        % function
        if yNew >= y1+tolY
            xNewTry = xLow - 4/3*abs(xUp-xLow);
            if nargin > 3
                xNewTry = max(xNewTry, lb);
            end
            yNewTry = fun(xNewTry);
            if yNewTry < yNew
                xNew = xNewTry;
                yNew = yNewTry;
%                 xNewTry
%                 yNewTry
            end
        end
        if yNew >= y1+tolY
            xNewTry = xUp + 4/3*abs(xUp-xLow);
            if nargin > 3
                xNewTry = min(xNewTry, ub);
            end
            yNewTry = fun(xNewTry);
            if yNewTry < yNew
                xNew = xNewTry;
                yNew = yNewTry;
%                 xNewTry
%                 yNewTry
            end
        end
        
        if xNew <= xLow
            xUp = xM;
            yUp = yM;
            xM = xLow;
            yM = yLow;
            xLow = xNew;
            yLow = yNew;
        elseif xNew >= xUp
            xLow = xM;
            yLow = yM;
            xM = xUp;
            yM = yUp;
            xUp = xNew;
            yUp = yNew;
        elseif xNew <= xM
            xLow = xNew;
            yLow = yNew;
        else
            xUp = xNew;
            yUp = yNew;
        end
        if (xM == xLow) || (xM == xUp)
            xM = (xLow+xUp)/2;
            yM = fun(xM);
        end
        
        if numIter >= maxIter
            runIter = false;
        elseif (abs(x1-xNew) <= tolX)
            runIter = false;
        elseif xLow == xUp
            runIter = false;
        end
        if yNew < y1
            x1 = xNew;
            y1 = yNew;
        end
    end

end

