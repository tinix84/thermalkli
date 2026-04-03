function cli_print_help(command)
    % cli_print_help - print help for all commands or a specific command

    if nargin == 0 || isempty(command)
        fprintf('Usage: octave thermal_cli.m <command> [options]\n\n');
        fprintf('Commands:\n');
        fprintf('  calc-rth           Thermal resistance from power and temperatures\n');
        fprintf('  fin-efficiency     Fin efficiency (tanh model)\n');
        fprintf('  radiation          Radiation heat transfer (5 modes)\n');
        fprintf('  layer-rth          Single layer thermal resistance with spreading\n');
        fprintf('  stack-rth          Layer stack thermal resistance\n');
        fprintf('  heatsink-create    Create heatsink from database reference\n');
        fprintf('  heatsink-rth       Extruded fin heatsink thermal resistance\n');
        fprintf('  free-conv          Free convection surface temperature\n');
        fprintf('  water-cooling      Water cooling system analysis\n');
        fprintf('  hydraulic-op       Fan-heatsink hydraulic operating point\n');
        fprintf('  fin-rth            Finned heatsink thermal resistance\n');
        fprintf('  temp-dist          Temperature distribution on heatsink plane\n');
        fprintf('  gen-femm           Generate FEMM Lua verification script\n');
        fprintf('  compare-femm       Compare FEMM results with analytical\n');
        fprintf('\nWorkflows:\n');
        fprintf('  semi-on-pcb        Semiconductor on PCB thermal model\n');
        fprintf('  extruded-fin       Extruded fin heatsink design\n');
        fprintf('  optimize-fin       Parametric fin optimization\n');
        fprintf('  forced-conv-sim    Forced convection simulation\n');
        fprintf('  multi-sim          Multi-configuration simulation\n');
        fprintf('\nOptions:\n');
        fprintf('  --help             Show help for a command\n');
        fprintf('  --config <file>    Load configuration from .m file\n');
    end
end
