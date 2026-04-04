function cspi = cspi_calc(rth, vol_cs)
    % cspi_calc - compute CSPI metric (Drofenik & Kolar, CIPS06 eq. 41)
    %   rth:    heatsink thermal resistance [K/W]
    %   vol_cs: heatsink volume [liters]
    %   cspi:   cooling system performance index [W/(K*liter)]
    cspi = 1 / (rth * vol_cs);
end
