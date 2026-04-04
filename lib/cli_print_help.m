function cli_print_help(command)
    % cli_print_help - print help for all commands or a specific command

    if nargin == 0 || isempty(command)
        fprintf('Usage: octave thermal_cli.m <command> [options]\n\n');
        fprintf('Basic Calculations:\n');
        fprintf('  calc-rth           Thermal resistance from power and temperatures\n');
        fprintf('  fin-efficiency     Fin efficiency (tanh model)\n');
        fprintf('  radiation          Radiation heat transfer (--mode parallel|cylinder|sphere|enclosure|convex)\n');
        fprintf('  h-coeff            Heat transfer coefficient (--mode forced|natural|radiation)\n');
        fprintf('\nLayer/Stack Thermal Resistance:\n');
        fprintf('  layer-rth          Single layer Rth with optional spreading\n');
        fprintf('  stack-rth          Multi-layer stack Rth (--config required)\n');
        fprintf('\nDrofenik Channel Model:\n');
        fprintf('  channel-rth        Channel thermal resistance (Drofenik/Shabany)\n');
        fprintf('  channel-dp         Channel pressure drop\n');
        fprintf('\nCSPI (Cooling System Performance Index):\n');
        fprintf('  cspi               Compute CSPI from Rth and volume\n');
        fprintf('  cspi-optimize      Find optimal heatsink geometry for max CSPI\n');
        fprintf('  fan-fit            Fit fan scaling law constants k1,k2,k3\n');
        fprintf('\nForced Convection (SoftwareTermico):\n');
        fprintf('  hydraulic-op       Fan-heatsink hydraulic operating point\n');
        fprintf('  fin-rth            Finned heatsink thermal resistance\n');
        fprintf('  water-cooling      Water/glycol cooling system analysis\n');
        fprintf('\nFEMM Verification:\n');
        fprintf('  gen-femm           Generate FEMM Lua script (--model semi-on-pcb|extruded-fin|baseplate)\n');
        fprintf('  compare-femm       Compare FEMM CSV results with analytical\n');
        fprintf('\nWorkflows:\n');
        fprintf('  semi-on-pcb        Semiconductor on PCB thermal model\n');
        fprintf('  extruded-fin       Extruded fin heatsink design (liquid cooling)\n');
        fprintf('  forced-conv-sim    Forced convection simulation (air cooling)\n');
        fprintf('  cspi-sweep         CSPI parametric study vs fan size/material\n');
        fprintf('  multi-sim          Multi-configuration heatsink optimization\n');
        fprintf('  optimize-fin       Parametric fin geometry optimization\n');
        fprintf('\nOptions:\n');
        fprintf('  --help             Show help for a command\n');
        fprintf('  --config <file>    Load configuration from .m file\n');
        fprintf('  --save-csv <file>  Export results to CSV\n');
        fprintf('  --femm-lua <file>  Generate FEMM Lua script alongside calculation\n');
    end
end
