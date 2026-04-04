function lua_str = femm_forced_air_heatsink(cfg, h_channel, n_fins_show)
    % femm_forced_air_heatsink - FEMM Lua for full forced-air heatsink cross-section
    %
    % Generates a 2D planar model showing multiple fins with:
    % - Heat flux on baseplate top (from component)
    % - Convection BCs on all channel walls (from computed h)
    % - Full cross-section: n fins visible
    %
    % cfg: struct with heatsink geometry
    %   .baseThickness  [m] baseplate thickness
    %   .finHeight      [m] fin height above base
    %   .finThickness   [m] fin thickness
    %   .channelWidth   [m] channel width between fins
    %   .k              [m] thermal conductivity [W/(m*K)]
    %   .heatSource.width  [m] heat source width (centered on base)
    %   .heatSource.flux   [W/m2] heat flux (or compute from P/A)
    %
    % h_channel: convective heat transfer coefficient [W/(m2*K)]
    %            (from hydraulic-op + fin-rth calculation)
    %
    % n_fins_show: number of fins to show (default: all that fit)
    %              Use odd number for symmetry

    if nargin < 3
        % Show enough fins to cover the heat source width + 2 extra each side
        pitch = cfg.finThickness + cfg.channelWidth;
        n_fins_show = ceil(cfg.heatSource.width / pitch) + 4;
        if mod(n_fins_show, 2) == 0
            n_fins_show = n_fins_show + 1;  % force odd for symmetry
        end
    end

    tb = cfg.baseThickness;
    Hf = cfg.finHeight;
    tf = cfg.finThickness;
    s = cfg.channelWidth;
    k = cfg.k;
    pitch = tf + s;

    % Total width of model
    W_total = n_fins_show * pitch;

    % Heat source centered on baseplate
    src_half = cfg.heatSource.width / 2;
    src_left = W_total / 2 - src_half;
    src_right = W_total / 2 + src_half;
    q_flux = cfg.heatSource.flux;

    % Fluid temperature
    T_fluid = cfg.tFluid;

    L = {};
    L{end+1} = '-------------------------------------------------------';
    L{end+1} = '-- Auto-generated: forced-air heatsink (full cross-section)';
    L{end+1} = sprintf('-- %d fins, h_channel = %.1f W/(m2K)', n_fins_show, h_channel);
    L{end+1} = sprintf('-- Date: %s', datestr(now, 'yyyy-mm-dd'));
    L{end+1} = '-------------------------------------------------------';
    L{end+1} = '';
    L{end+1} = 't1 = clock()';
    L{end+1} = 'newdocument(2)';
    L{end+1} = sprintf('hi_probdef("meters", "planar", 1e-8, %.1f, 30)', T_fluid - 273.15);
    L{end+1} = '';

    % Materials
    L{end+1} = '-- Materials';
    L{end+1} = sprintf('hi_addmaterial("heatsink", %.1f, %.1f, 0)', k, k);
    L{end+1} = '';

    % Boundary conditions
    L{end+1} = '-- Boundary conditions';
    L{end+1} = sprintf('hi_addboundprop("heat_source", 1, 0, %.6e)', -q_flux);
    L{end+1} = sprintf('hi_addboundprop("convection", 2, 0, 0, %.4f, %.4f)', T_fluid, h_channel);
    L{end+1} = 'hi_addboundprop("insulated", 1, 0, 0)';
    L{end+1} = '';

    % =================================================================
    % Geometry: baseplate + fins
    % =================================================================
    % Coordinate system:
    %   x: 0 to W_total (left to right)
    %   y: 0 = base bottom, tb = base top / fin start, tb+Hf = fin top

    L{end+1} = '-- Geometry: nodes';

    % Base corners
    L{end+1} = sprintf('hi_addnode(0, 0)');
    L{end+1} = sprintf('hi_addnode(%.6e, 0)', W_total);
    L{end+1} = sprintf('hi_addnode(0, %.6e)', tb);
    L{end+1} = sprintf('hi_addnode(%.6e, %.6e)', W_total, tb);

    % Heat source boundaries on base bottom
    L{end+1} = sprintf('hi_addnode(%.6e, 0)', src_left);
    L{end+1} = sprintf('hi_addnode(%.6e, 0)', src_right);

    % Fin nodes: each fin is a rectangle from (x_left, tb) to (x_left+tf, tb+Hf)
    for i = 1:n_fins_show
        x_left = (i - 1) * pitch;
        x_right = x_left + tf;
        L{end+1} = sprintf('hi_addnode(%.6e, %.6e)', x_left, tb);
        L{end+1} = sprintf('hi_addnode(%.6e, %.6e)', x_right, tb);
        L{end+1} = sprintf('hi_addnode(%.6e, %.6e)', x_left, tb + Hf);
        L{end+1} = sprintf('hi_addnode(%.6e, %.6e)', x_right, tb + Hf);
    end
    L{end+1} = '';

    % =================================================================
    % Segments
    % =================================================================
    L{end+1} = '-- Segments: baseplate';

    % Base bottom (split at source boundaries)
    L{end+1} = sprintf('hi_addsegment(0, 0, %.6e, 0)', src_left);
    L{end+1} = sprintf('hi_addsegment(%.6e, 0, %.6e, 0)', src_left, src_right);
    L{end+1} = sprintf('hi_addsegment(%.6e, 0, %.6e, 0)', src_right, W_total);

    % Base left and right walls
    L{end+1} = sprintf('hi_addsegment(0, 0, 0, %.6e)', tb);
    L{end+1} = sprintf('hi_addsegment(%.6e, 0, %.6e, %.6e)', W_total, W_total, tb);

    % Base top: segments between/around fins
    % Left of first fin
    x_first_fin = 0;
    if x_first_fin > 0
        L{end+1} = sprintf('hi_addsegment(0, %.6e, %.6e, %.6e)', tb, x_first_fin, tb);
    end
    % Between fins (channel top surfaces)
    for i = 1:n_fins_show - 1
        x_ch_left = (i - 1) * pitch + tf;
        x_ch_right = i * pitch;
        L{end+1} = sprintf('hi_addsegment(%.6e, %.6e, %.6e, %.6e)', x_ch_left, tb, x_ch_right, tb);
    end
    % Right of last fin
    x_last_fin_right = (n_fins_show - 1) * pitch + tf;
    if x_last_fin_right < W_total
        L{end+1} = sprintf('hi_addsegment(%.6e, %.6e, %.6e, %.6e)', x_last_fin_right, tb, W_total, tb);
    end

    L{end+1} = '';
    L{end+1} = '-- Segments: fins';

    % Each fin: left wall, right wall, top
    for i = 1:n_fins_show
        x_left = (i - 1) * pitch;
        x_right = x_left + tf;
        % Left wall
        L{end+1} = sprintf('hi_addsegment(%.6e, %.6e, %.6e, %.6e)', x_left, tb, x_left, tb + Hf);
        % Right wall
        L{end+1} = sprintf('hi_addsegment(%.6e, %.6e, %.6e, %.6e)', x_right, tb, x_right, tb + Hf);
        % Top
        L{end+1} = sprintf('hi_addsegment(%.6e, %.6e, %.6e, %.6e)', x_left, tb + Hf, x_right, tb + Hf);
    end
    L{end+1} = '';

    % =================================================================
    % Block labels
    % =================================================================
    L{end+1} = '-- Block labels';

    % Baseplate block
    L{end+1} = sprintf('hi_addblocklabel(%.6e, %.6e)', W_total / 2, tb / 2);
    L{end+1} = sprintf('hi_selectlabel(%.6e, %.6e)', W_total / 2, tb / 2);
    L{end+1} = 'hi_setblockprop("heatsink", 0, 0, 0)';
    L{end+1} = 'hi_clearselected()';

    % Fin blocks
    for i = 1:n_fins_show
        x_center = (i - 1) * pitch + tf / 2;
        y_center = tb + Hf / 2;
        L{end+1} = sprintf('hi_addblocklabel(%.6e, %.6e)', x_center, y_center);
        L{end+1} = sprintf('hi_selectlabel(%.6e, %.6e)', x_center, y_center);
        L{end+1} = 'hi_setblockprop("heatsink", 0, 0, 0)';
        L{end+1} = 'hi_clearselected()';
    end
    L{end+1} = '';

    % =================================================================
    % Boundary condition assignment
    % =================================================================
    L{end+1} = '-- Apply boundary conditions';

    % Heat source on base bottom (center segment)
    L{end+1} = sprintf('hi_selectsegment(%.6e, 0)', (src_left + src_right) / 2);
    L{end+1} = 'hi_setsegmentprop("heat_source", 0, 1, 0, 0, "<None>")';
    L{end+1} = 'hi_clearselected()';

    % Insulated: base bottom outside source
    L{end+1} = sprintf('hi_selectsegment(%.6e, 0)', src_left / 2);
    L{end+1} = 'hi_setsegmentprop("insulated", 0, 1, 0, 0, "<None>")';
    L{end+1} = 'hi_clearselected()';
    L{end+1} = sprintf('hi_selectsegment(%.6e, 0)', (src_right + W_total) / 2);
    L{end+1} = 'hi_setsegmentprop("insulated", 0, 1, 0, 0, "<None>")';
    L{end+1} = 'hi_clearselected()';

    % Insulated: base left and right walls
    L{end+1} = sprintf('hi_selectsegment(0, %.6e)', tb / 2);
    L{end+1} = 'hi_setsegmentprop("insulated", 0, 1, 0, 0, "<None>")';
    L{end+1} = 'hi_clearselected()';
    L{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', W_total, tb / 2);
    L{end+1} = 'hi_setsegmentprop("insulated", 0, 1, 0, 0, "<None>")';
    L{end+1} = 'hi_clearselected()';

    % Convection on ALL channel walls (fin left/right walls facing air + channel tops + fin tops)
    L{end+1} = '';
    L{end+1} = '-- Convection on channel walls';
    for i = 1:n_fins_show
        x_left = (i - 1) * pitch;
        x_right = x_left + tf;

        % Left wall of fin (channel side) — skip first fin's left (outer wall)
        if i > 1
            L{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', x_left, tb + Hf / 2);
            L{end+1} = 'hi_setsegmentprop("convection", 0, 1, 0, 0, "<None>")';
            L{end+1} = 'hi_clearselected()';
        else
            % First fin left wall: insulated (outer edge)
            L{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', x_left, tb + Hf / 2);
            L{end+1} = 'hi_setsegmentprop("insulated", 0, 1, 0, 0, "<None>")';
            L{end+1} = 'hi_clearselected()';
        end

        % Right wall of fin (channel side) — skip last fin's right (outer wall)
        if i < n_fins_show
            L{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', x_right, tb + Hf / 2);
            L{end+1} = 'hi_setsegmentprop("convection", 0, 1, 0, 0, "<None>")';
            L{end+1} = 'hi_clearselected()';
        else
            L{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', x_right, tb + Hf / 2);
            L{end+1} = 'hi_setsegmentprop("insulated", 0, 1, 0, 0, "<None>")';
            L{end+1} = 'hi_clearselected()';
        end

        % Fin top: convection
        L{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', x_left + tf / 2, tb + Hf);
        L{end+1} = 'hi_setsegmentprop("convection", 0, 1, 0, 0, "<None>")';
        L{end+1} = 'hi_clearselected()';
    end

    % Channel base (between fins): convection
    for i = 1:n_fins_show - 1
        x_ch_center = (i - 1) * pitch + tf + s / 2;
        L{end+1} = sprintf('hi_selectsegment(%.6e, %.6e)', x_ch_center, tb);
        L{end+1} = 'hi_setsegmentprop("convection", 0, 1, 0, 0, "<None>")';
        L{end+1} = 'hi_clearselected()';
    end
    L{end+1} = '';

    % =================================================================
    % Solve
    % =================================================================
    L{end+1} = '-- Solve';
    L{end+1} = 'hi_zoomnatural()';
    L{end+1} = 'hi_saveas("forced_air_heatsink.feh")';
    L{end+1} = 'hi_analyze()';
    L{end+1} = 'hi_loadsolution()';
    L{end+1} = '';

    % =================================================================
    % Post-processing: extract temperatures
    % =================================================================
    L{end+1} = '-- Extract results to CSV';
    L{end+1} = 'f = openfile("femm_results.csv", "w")';
    L{end+1} = 'write(f, "point,x,y,temperature\n")';

    % Base bottom center (hottest point, under heat source)
    L{end+1} = sprintf('T1 = ho_getpointvalues(%.6e, 0)', W_total / 2);
    L{end+1} = sprintf('write(f, string.format("base_center,%.6e,0,%%.6f\\n", T1))', W_total / 2);

    % Base top center
    L{end+1} = sprintf('T2 = ho_getpointvalues(%.6e, %.6e)', W_total / 2, tb);
    L{end+1} = sprintf('write(f, string.format("base_top_center,%.6e,%.6e,%%.6f\\n", T2))', W_total / 2, tb);

    % Center fin tip
    center_fin = ceil(n_fins_show / 2);
    x_center_fin = (center_fin - 1) * pitch + tf / 2;
    L{end+1} = sprintf('T3 = ho_getpointvalues(%.6e, %.6e)', x_center_fin, tb + Hf);
    L{end+1} = sprintf('write(f, string.format("center_fin_tip,%.6e,%.6e,%%.6f\\n", T3))', x_center_fin, tb + Hf);

    % Edge fin tip
    L{end+1} = sprintf('T4 = ho_getpointvalues(%.6e, %.6e)', tf / 2, tb + Hf);
    L{end+1} = sprintf('write(f, string.format("edge_fin_tip,%.6e,%.6e,%%.6f\\n", T4))', tf / 2, tb + Hf);

    L{end+1} = 'closefile(f)';
    L{end+1} = '';
    L{end+1} = 't2 = clock()';
    L{end+1} = 'print(string.format("Solve time: %.1f s", t2-t1))';
    L{end+1} = 'print("Results saved to femm_results.csv")';

    lua_str = strjoin(L, '\n');
end
