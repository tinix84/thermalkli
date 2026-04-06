function lua_str = femm_drofenik_heatsink(params)
    % femm_drofenik_heatsink - FEMM Lua matching Drofenik/Kolar CIPS06 Fig.1/Fig.3
    %
    % Generates a 2D planar cross-section of the heatsink from:
    %   Drofenik & Kolar, "Analyzing the Theoretical Limits of Forced Air-Cooling..."
    %   CIPS 2006, Fig.1 and thermal network Fig.3
    %
    % Convention (matching paper):
    %   - Heat enters from TOP of baseplate (chip area A_CHIP = b*L on top)
    %   - Fins extend DOWNWARD from baseplate
    %   - Air flows through channels (perpendicular to cross-section)
    %   - Model shows ONE HALF of the heatsink (symmetry at center)
    %
    % Cross-section (y-axis up, x-axis right):
    %   y = d+c : baseplate top (heat flux from chips)
    %   y = c   : baseplate bottom / fin root
    %   y = 0   : fin tips (convection to air)
    %   x = 0   : symmetry axis (center of heatsink)
    %   x = b/2 : outer edge
    %
    % params: struct matching paper notation
    %   .b       [m] heatsink width (= fan diameter = c typically)
    %   .c       [m] fin height (= channel height)
    %   .d       [m] baseplate thickness
    %   .L       [m] heatsink length in airflow direction
    %   .n       [-] number of fins
    %   .s       [m] channel width
    %   .t       [m] fin thickness
    %   .lambda  [W/(m*K)] thermal conductivity of heatsink material
    %   .h       [W/(m2*K)] convective heat transfer coefficient in channels
    %   .T_air   [K] mean air temperature in channels (Kelvin, matches sibling generators)
    %   .P_V     [W] total thermal losses (for heat flux calculation)
    %
    % The Rth from FEMM (per half-heatsink) should be compared with:
    %   R_th,S-a^(HS) = 1/n * (R_th,d + 1/2*(R_th,FIN + R_th,A)) + R_th,DT
    %   (Drofenik eq.14, for both halves: divide by 2 for one side)

    b = params.b;
    c = params.c;
    d = params.d;
    L = params.L;
    n = params.n;
    s = params.s;
    t = params.t;
    k = params.lambda;
    h = params.h;
    T_air = params.T_air;
    P_V = params.P_V;

    % Heat flux on baseplate top: q = P_V / A_CHIP, A_CHIP = b * L
    % For half-heatsink: q stays the same (flux, not total power)
    q_flux = P_V / (b * L);

    % Pitch
    pitch = s + t;

    % The half-heatsink model assumes a symmetry plane at x=0 that splits
    % the fin array into two identical halves, so the total fin count must
    % be even (otherwise floor(n/2) would silently drop one fin).
    if mod(n, 2) ~= 0
        error('femm_drofenik_heatsink:InvalidFinCount', ...
              'params.n must be even for the half-heatsink symmetry model; got n=%d.', n);
    end

    % Number of fins in half-heatsink
    n_half = n / 2;

    L_lines = {};

    L_lines{end+1} = '-------------------------------------------------------';
    L_lines{end+1} = '-- Drofenik/Kolar heatsink cross-section (CIPS06 Fig.1)';
    L_lines{end+1} = sprintf('-- b=%.0fmm, c=%.0fmm, d=%.0fmm, L=%.0fmm', b*1e3, c*1e3, d*1e3, L*1e3);
    L_lines{end+1} = sprintf('-- n=%d fins, s=%.2fmm, t=%.2fmm', n, s*1e3, t*1e3);
    L_lines{end+1} = sprintf('-- lambda=%.0f W/mK, h=%.1f W/(m2K)', k, h);
    L_lines{end+1} = sprintf('-- P_V=%.1f W, q=%.0f W/m2', P_V, q_flux);
    L_lines{end+1} = sprintf('-- Half-heatsink model (symmetry at x=0)');
    L_lines{end+1} = '-------------------------------------------------------';
    L_lines{end+1} = '';
    L_lines{end+1} = 't1 = clock()';
    L_lines{end+1} = 'newdocument(2)';
    L_lines{end+1} = sprintf('hi_probdef("meters", "planar", 1e-8, %.1f, 30)', T_air - 273.15);
    L_lines{end+1} = '';

    % Materials
    L_lines{end+1} = sprintf('hi_addmaterial("heatsink", %.1f, %.1f, 0)', k, k);
    L_lines{end+1} = '';

    % Boundary conditions
    L_lines{end+1} = '-- Boundary conditions';
    L_lines{end+1} = sprintf('hi_addboundprop("chip_heat", 1, 0, %.6e)', -q_flux);
    L_lines{end+1} = sprintf('hi_addboundprop("convection", 2, 0, 0, %.4f, %.4f)', T_air, h);
    L_lines{end+1} = 'hi_addboundprop("symmetry", 1, 0, 0)';
    L_lines{end+1} = 'hi_addboundprop("insulated", 1, 0, 0)';
    L_lines{end+1} = '';

    % Geometry coordinates (paper convention: y=0 fin tips, y=c fin root, y=c+d baseplate top)
    % x=0 center (symmetry), x=b/2 outer edge
    % Half-heatsink: n_half fins from x=0 outward

    W_half = b / 2;
    y_tip = 0;
    y_root = c;
    y_top = c + d;

    L_lines{end+1} = '-- Geometry nodes';
    % Baseplate corners (full width of half-heatsink)
    L_lines{end+1} = sprintf('hi_addnode(0, %.6e)', y_root);
    L_lines{end+1} = sprintf('hi_addnode(%.6e, %.6e)', W_half, y_root);
    L_lines{end+1} = sprintf('hi_addnode(0, %.6e)', y_top);
    L_lines{end+1} = sprintf('hi_addnode(%.6e, %.6e)', W_half, y_top);

    % Fin nodes: each fin at x_left, x_right from center outward
    for i = 1:n_half
        % Fin i: centered at x = (i-0.5)*pitch from center (approximate)
        % More precisely: first channel starts at x=0, then alternating channel/fin
        % With symmetry: x=0 is center of first channel (or fin center)
        % Paper: k = s/(b/n) = s/pitch — "fin spacing ratio"
        % Layout: |s/2|t|s|t|s|t|...|s/2| across full width b
        % Half: starts with s/2 (half channel) then |t|s|t|s|...

        x_left = s/2 + (i-1) * pitch;
        x_right = x_left + t;

        L_lines{end+1} = sprintf('hi_addnode(%.6e, %.6e)', x_left, y_tip);
        L_lines{end+1} = sprintf('hi_addnode(%.6e, %.6e)', x_right, y_tip);
        L_lines{end+1} = sprintf('hi_addnode(%.6e, %.6e)', x_left, y_root);
        L_lines{end+1} = sprintf('hi_addnode(%.6e, %.6e)', x_right, y_root);
    end
    L_lines{end+1} = '';

    % Segments
    L_lines{end+1} = '-- Segments: baseplate';
    % Baseplate top (heat flux)
    L_lines{end+1} = sprintf('hi_addsegment(0, %.6e, %.6e, %.6e)', y_top, W_half, y_top);
    % Baseplate bottom (= fin root level): split by fin positions
    % From x=0 to first fin
    L_lines{end+1} = sprintf('hi_addsegment(0, %.6e, %.6e, %.6e)', y_root, s/2, y_root);
    % Between fins
    for i = 1:n_half - 1
        x_gap_left = s/2 + (i-1)*pitch + t;
        x_gap_right = s/2 + i*pitch;
        L_lines{end+1} = sprintf('hi_addsegment(%.6e, %.6e, %.6e, %.6e)', x_gap_left, y_root, x_gap_right, y_root);
    end
    % After last fin to edge
    x_last_fin_right = s/2 + (n_half-1)*pitch + t;
    if x_last_fin_right < W_half
        L_lines{end+1} = sprintf('hi_addsegment(%.6e, %.6e, %.6e, %.6e)', x_last_fin_right, y_root, W_half, y_root);
    end
    % Baseplate left (symmetry)
    L_lines{end+1} = sprintf('hi_addsegment(0, %.6e, 0, %.6e)', y_root, y_top);
    % Baseplate right (outer edge)
    L_lines{end+1} = sprintf('hi_addsegment(%.6e, %.6e, %.6e, %.6e)', W_half, y_root, W_half, y_top);

    L_lines{end+1} = '';
    L_lines{end+1} = '-- Segments: fins';
    for i = 1:n_half
        x_left = s/2 + (i-1)*pitch;
        x_right = x_left + t;
        % Left wall
        L_lines{end+1} = sprintf('hi_addsegment(%.6e, %.6e, %.6e, %.6e)', x_left, y_tip, x_left, y_root);
        % Right wall
        L_lines{end+1} = sprintf('hi_addsegment(%.6e, %.6e, %.6e, %.6e)', x_right, y_tip, x_right, y_root);
        % Tip (bottom)
        L_lines{end+1} = sprintf('hi_addsegment(%.6e, %.6e, %.6e, %.6e)', x_left, y_tip, x_right, y_tip);
    end
    L_lines{end+1} = '';

    % Block labels
    L_lines{end+1} = '-- Block labels';
    % Baseplate
    L_lines{end+1} = sprintf('hi_addblocklabel(%.6e, %.6e)', W_half/2, (y_root + y_top)/2);
    L_lines{end+1} = sprintf('hi_selectlabel(%.6e, %.6e)', W_half/2, (y_root + y_top)/2);
    L_lines{end+1} = 'hi_setblockprop("heatsink", 0, 0, 0)';
    L_lines{end+1} = 'hi_clearselected()';
    % Fins
    for i = 1:n_half
        x_center = s/2 + (i-1)*pitch + t/2;
        L_lines{end+1} = sprintf('hi_addblocklabel(%.6e, %.6e)', x_center, c/2);
        L_lines{end+1} = sprintf('hi_selectlabel(%.6e, %.6e)', x_center, c/2);
        L_lines{end+1} = 'hi_setblockprop("heatsink", 0, 0, 0)';
        L_lines{end+1} = 'hi_clearselected()';
    end
    L_lines{end+1} = '';

    % Boundary conditions
    L_lines{end+1} = '-- Apply BCs';
    % Heat flux on baseplate top
    L_lines{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', W_half/2, y_top);
    L_lines{end+1} = 'hi_setsegmentprop("chip_heat", 0, 1, 0, 0, "<None>")';
    L_lines{end+1} = 'hi_clearselected()';

    % Symmetry on left edge (baseplate)
    L_lines{end+1} = sprintf('hi_selectsegment(0, %.6e)', (y_root + y_top)/2);
    L_lines{end+1} = 'hi_setsegmentprop("symmetry", 0, 1, 0, 0, "<None>")';
    L_lines{end+1} = 'hi_clearselected()';

    % Insulated on right edge (outer wall)
    L_lines{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', W_half, (y_root + y_top)/2);
    L_lines{end+1} = 'hi_setsegmentprop("insulated", 0, 1, 0, 0, "<None>")';
    L_lines{end+1} = 'hi_clearselected()';

    % Convection on channel base segments (between fins, at y=root)
    % First half-channel (x=0 to s/2)
    L_lines{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', s/4, y_root);
    L_lines{end+1} = 'hi_setsegmentprop("convection", 0, 1, 0, 0, "<None>")';
    L_lines{end+1} = 'hi_clearselected()';
    % Full channels between fins
    for i = 1:n_half - 1
        x_ch = s/2 + (i-1)*pitch + t + s/2;
        L_lines{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', x_ch, y_root);
        L_lines{end+1} = 'hi_setsegmentprop("convection", 0, 1, 0, 0, "<None>")';
        L_lines{end+1} = 'hi_clearselected()';
    end
    % Last partial channel to edge
    if x_last_fin_right < W_half
        x_last_ch = (x_last_fin_right + W_half) / 2;
        L_lines{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', x_last_ch, y_root);
        L_lines{end+1} = 'hi_setsegmentprop("convection", 0, 1, 0, 0, "<None>")';
        L_lines{end+1} = 'hi_clearselected()';
    end

    % Convection on fin walls and tips
    for i = 1:n_half
        x_left = s/2 + (i-1)*pitch;
        x_right = x_left + t;
        % Left wall (channel side)
        L_lines{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', x_left, c/2);
        L_lines{end+1} = 'hi_setsegmentprop("convection", 0, 1, 0, 0, "<None>")';
        L_lines{end+1} = 'hi_clearselected()';
        % Right wall (channel side, except last fin outer wall)
        if i < n_half || x_right < W_half
            L_lines{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', x_right, c/2);
            L_lines{end+1} = 'hi_setsegmentprop("convection", 0, 1, 0, 0, "<None>")';
            L_lines{end+1} = 'hi_clearselected()';
        end
        % Fin tip
        L_lines{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', x_left + t/2, y_tip);
        L_lines{end+1} = 'hi_setsegmentprop("convection", 0, 1, 0, 0, "<None>")';
        L_lines{end+1} = 'hi_clearselected()';
    end
    L_lines{end+1} = '';

    % Solve
    L_lines{end+1} = '-- Solve';
    L_lines{end+1} = 'hi_zoomnatural()';
    L_lines{end+1} = 'hi_saveas("drofenik_heatsink.feh")';
    L_lines{end+1} = 'hi_analyze()';
    L_lines{end+1} = 'hi_loadsolution()';
    L_lines{end+1} = '';

    % Post-processing
    L_lines{end+1} = '-- Extract results';
    L_lines{end+1} = 'f = openfile("femm_results.csv", "w")';
    L_lines{end+1} = 'write(f, "point,x,y,temperature\n")';

    % Baseplate top center (hottest point, under chips)
    L_lines{end+1} = sprintf('T_chip = ho_getpointvalues(0, %.6e)', y_top);
    L_lines{end+1} = sprintf('write(f, string.format("chip_surface,0,%.6e,%%.6f\\n", T_chip))', y_top);

    % Baseplate bottom center (fin root)
    L_lines{end+1} = sprintf('T_root = ho_getpointvalues(0, %.6e)', y_root);
    L_lines{end+1} = sprintf('write(f, string.format("fin_root_center,0,%.6e,%%.6f\\n", T_root))', y_root);

    % Center fin tip
    L_lines{end+1} = sprintf('T_tip_center = ho_getpointvalues(%.6e, 0)', s/2 + t/2);
    L_lines{end+1} = sprintf('write(f, string.format("fin_tip_center,%.6e,0,%%.6f\\n", T_tip_center))', s/2 + t/2);

    % Edge fin tip
    x_edge_fin = s/2 + (n_half-1)*pitch + t/2;
    L_lines{end+1} = sprintf('T_tip_edge = ho_getpointvalues(%.6e, 0)', x_edge_fin);
    L_lines{end+1} = sprintf('write(f, string.format("fin_tip_edge,%.6e,0,%%.6f\\n", T_tip_edge))', x_edge_fin);

    L_lines{end+1} = 'closefile(f)';
    L_lines{end+1} = '';

    % Print analytical comparison values
    L_lines{end+1} = '-- Analytical comparison (Drofenik eq.11-14)';
    L_lines{end+1} = sprintf('print("Drofenik analytical Rth components (per half-heatsink):")');

    % Compute analytical values in Lua for direct comparison
    L_lines{end+1} = sprintf('R_th_d = %.6e / (%.6e * %.6e)', d, (b/n)*L, k);
    L_lines{end+1} = sprintf('R_th_A = 1 / (%.6e * %.6e * %.6e)', h, L, c/2);
    L_lines{end+1} = sprintf('R_th_FIN = (%.6e) / (%.6e * %.6e * %.6e)', c/2, t/2, L, k);
    L_lines{end+1} = sprintf('print(string.format("  R_th_d   = %%.4f K/W", R_th_d))');
    L_lines{end+1} = sprintf('print(string.format("  R_th_A   = %%.4f K/W", R_th_A))');
    L_lines{end+1} = sprintf('print(string.format("  R_th_FIN = %%.4f K/W", R_th_FIN))');
    % NOTE: omits R_th_DT (air temperature rise term in eq.14) — needs flow rate, out of scope here
    L_lines{end+1} = sprintf('R_th_half = 1/%d * (R_th_d + 0.5*(R_th_FIN + R_th_A))', n);
    L_lines{end+1} = sprintf('print(string.format("  R_th_half (eq.14, solid-to-air, no DT term) = %%.4f K/W", R_th_half))');
    L_lines{end+1} = '';
    L_lines{end+1} = sprintf('dT_FEMM = T_chip - %.4f', T_air);
    L_lines{end+1} = sprintf('R_th_FEMM = dT_FEMM / %.4f', P_V/2);
    L_lines{end+1} = 'print(string.format("  R_th_FEMM (half)  = %.4f K/W", R_th_FEMM))';
    L_lines{end+1} = 'print(string.format("  Deviation = %.1f%%", (R_th_FEMM - R_th_half)/R_th_half*100))';
    L_lines{end+1} = '';
    L_lines{end+1} = 't2 = clock()';
    L_lines{end+1} = 'print(string.format("Solve time: %.1f s", t2-t1))';

    lua_str = strjoin(L_lines, '\n');
end
