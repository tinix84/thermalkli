function [ a, xs, ys ] = quadAppr( x1, y1, x2, y2, x3, y3 )
%apprFunParam returns the parameters of function a*(x-xs)^2+ys = y
%given three different points on the function.
    
    a = (-x1*y2 + x1*y3 + x2*y1 - x2*y3 - x3*y1 + x3*y2)/...
        ((x1 - x2)*(x1 - x3)*(x2 - x3));
    xs = (x1^2*a - x3^2*a - y1 + y3)/(2*a*(x1 - x3));
    ys = y3 - a*(x3 - xs)^2;
    
end