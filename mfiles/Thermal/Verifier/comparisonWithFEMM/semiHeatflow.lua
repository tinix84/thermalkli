------------------------------------------------------- 
-- 
-- Heat Flow in pcb
-- 
-- dissipation on top and bottom, forced air
-------------------------------------------------------

t1=clock()
newdocument(2);

-- define problem parameters
hi_probdef("meters","axi",1e-8,20,30);

-- add in materials and boundary conditions
hi_addmaterial("Cu",400,400,0);
hi_addmaterial("Fr4",0.3,0.3,0);
hi_addmaterial("Via",0.3,2.1,0);
hi_addmaterial("Alu",200,200,0);

a = 80*10^-6
p = 0.9
q = -p/a
l = 0.001*10^-3
ab = 1000*10^-6

hi_addboundprop("chip",1,0,q);
hi_addboundprop("bottom",2,0,0,70+273.15,500);
hi_addboundprop("top",2,0,0,70+273.15,0);

-- draw the geometry
b = (ab/pi)^0.5
rc = (a/pi)^0.5
y0 = 0
d1 = 0.070*10^-3
y1 = -d1
d2 = 0.463*10^-3
y2 = y1-d2
d3 = 0.035*10^-3
y3 = y2-d3
d4 = 0.463*10^-3
y4 = y3-d4
d5 = 0.035*10^-3
y5 = y4-d5
d6 = 0.463*10^-3
y6 = y5-d6
d7 = 0.070*10^-3
y7 = y6-d7
ds = 3.000*10^-3
ys = y7-ds

hi_addnode(0,y0);
hi_addnode(rc,y0);
hi_addnode(b,y0);

hi_addnode(0,y1);
hi_addnode(rc,y1);
hi_addnode(b,y1);

hi_addnode(rc,y2);
hi_addnode(b,y2);

hi_addnode(rc,y3);
hi_addnode(b,y3);

hi_addnode(rc,y4);
hi_addnode(b,y4);

hi_addnode(rc,y5);
hi_addnode(b,y5);

hi_addnode(0,y6);
hi_addnode(rc,y6);
hi_addnode(b,y6);

hi_addnode(0,y7);
hi_addnode(rc,y7);
hi_addnode(b,y7);

hi_addnode(0,ys);
hi_addnode(b,ys);


hi_addsegment(0,y0,rc,y0);
hi_addsegment(rc,y0,b,y0);

hi_addsegment(0,y0,0,y1);
hi_addsegment(b,y0,b,y1);

hi_addsegment(0,y1,rc,y1);
hi_addsegment(rc,y1,b,y1);

hi_addsegment(0,y1,0,y6);

hi_addsegment(rc,y1,rc,y2);
hi_addsegment(b,y1,b,y2);

hi_addsegment(rc,y2,b,y2);

hi_addsegment(rc,y2,rc,y3);
hi_addsegment(b,y2,b,y3);

hi_addsegment(rc,y3,b,y3);

hi_addsegment(rc,y3,rc,y4);
hi_addsegment(b,y3,b,y4);

hi_addsegment(rc,y4,b,y4);

hi_addsegment(rc,y4,rc,y5);
hi_addsegment(b,y4,b,y5);

hi_addsegment(rc,y5,b,y5);

hi_addsegment(rc,y5,rc,y6);
hi_addsegment(b,y5,b,y6);

hi_addsegment(0,y6,rc,y6);
hi_addsegment(rc,y6,b,y6);

hi_addsegment(0,y6,0,y7);
hi_addsegment(b,y6,b,y7);

hi_addsegment(0,y7,rc,y7);
hi_addsegment(rc,y7,b,y7);

hi_addsegment(0,y7,0,ys);
hi_addsegment(b,y7,b,ys);

hi_addsegment(0,ys,b,ys);


-- assign materials to regions

hi_addblocklabel(rc+l,y0-l);
hi_addblocklabel(rc+l,y2-l);
hi_addblocklabel(rc+l,y4-l);
hi_addblocklabel(rc+l,y6-l);

hi_addblocklabel(rc+l,y1-l);
hi_addblocklabel(rc+l,y3-l);
hi_addblocklabel(rc+l,y5-l);

hi_addblocklabel(l,y1-l);

hi_addblocklabel(l,y7-l);


hi_selectlabel(rc+l,y0-l);
hi_selectlabel(rc+l,y2-l);
hi_selectlabel(rc+l,y4-l);
hi_selectlabel(rc+l,y6-l);
hi_setblockprop("Cu",0,0.05,0);
hi_clearselected()

hi_selectlabel(rc+l,y1-l);
hi_selectlabel(rc+l,y3-l);
hi_selectlabel(rc+l,y5-l);
hi_setblockprop("Fr4",0,0.05,0);
hi_clearselected()

hi_selectlabel(l,y1-l);
hi_setblockprop("Via",0,0.05,0);
hi_clearselected()

hi_selectlabel(l,y7-l);
hi_setblockprop("Alu",0,0.05,0);
hi_clearselected()

hi_zoomnatural()

-- apply the boundary conditions

hi_selectsegment(l,y0);
hi_setsegmentprop("chip",0,1,0,0,"<None>");
hi_clearselected()


hi_selectsegment(l,ys);
hi_setsegmentprop("bottom",0,1,0,0,"<None>");
hi_clearselected()

hi_selectsegment(rc+l,y0);
hi_setsegmentprop("top",0,1,0,0,"<None>");
hi_clearselected()


-- the file has to be saved before it can be analyzed.
hi_saveas("semiHeatFlow.feh");
hi_analyze()
t2=clock()
print(t2-t1)

-- view the results
hi_loadsolution()
