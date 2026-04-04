# thermalkli

Octave CLI toolbox for thermal engineering: heatsink design, thermal resistance modeling, semiconductor thermal analysis, and cooling system optimization.

## Quick Start

```bash
# Compute thermal resistance from power and temperatures
octave thermal_cli.m calc-rth --power 50 --tref 300 --tmeas 350

# Fin efficiency
octave thermal_cli.m fin-efficiency --length 0.02 --h 50 --area 0.04 --k 200 --ac 0.001

# Semiconductor on PCB thermal model
octave thermal_cli.m semi-on-pcb --config configs/example_semi_on_pcb.m

# CSPI optimization (Drofenik/Kolar)
octave thermal_cli.m cspi-optimize --lambda 210 --a-chip 32e-4 --c 0.04 --p-fan 20

# Natural convection surface temperature
octave thermal_cli.m free-conv --config configs/example_free_conv.m

# Generate FEMM verification script
octave thermal_cli.m gen-femm --model semi-on-pcb --config configs/example_semi_on_pcb.m --output model.lua
```

## Requirements

- GNU Octave 8.x+
- `io` package: `pkg install -forge io` (for xlsx database reading)

## Commands

Run `octave thermal_cli.m --help` for the full list, or `octave thermal_cli.m <command> --help` for command-specific usage.

| Category | Commands |
|----------|----------|
| Basic calculations | `calc-rth`, `fin-efficiency`, `radiation`, `h-coeff` |
| Layer/stack Rth | `layer-rth`, `stack-rth` |
| Drofenik channel | `channel-rth`, `channel-dp` |
| CSPI optimizer | `cspi`, `cspi-optimize`, `fan-fit` |
| Forced convection | `hydraulic-op`, `fin-rth`, `water-cooling` |
| Natural convection | `free-conv` |
| Heatsink from DB | `heatsink-create`, `heatsink-rth` |
| FEMM verification | `gen-femm`, `compare-femm` |

## Workflows

| Workflow | Description |
|----------|-------------|
| `semi-on-pcb` | Semiconductor on PCB: Rth network, Tjunction, PMax |
| `extruded-fin` | Extruded fin heatsink with liquid cooling |
| `forced-conv-sim` | Air-cooled heatsink: hydraulic OP + fin Rth + temperature distribution |
| `multi-sim` | Multi-configuration sweep with auto-resize |
| `optimize-fin` | Parametric fin geometry optimization |
| `cspi-sweep` | CSPI vs fan diameter and material |

## Configuration

All workflows use `.m` config files returning a struct. See `configs/` for examples. CLI flags override config values:

```bash
octave thermal_cli.m semi-on-pcb --config configs/example_semi_on_pcb.m --pLossJunction 100
```

## Tests

```bash
octave --no-gui tests/run_tests.m
# 95 tests, all passing
```

## Key References

- Lee et al., "Constriction/Spreading Resistance Model for Electronics Packaging" (1995) — spreading resistance
- Drofenik & Kolar, CIPS 2006/2008 — CSPI, fan scaling laws, optimal heatsink geometry
- Incropera & DeWitt, "Fundamentals of Heat and Mass Transfer" — fin efficiency, radiation, convection correlations
- Baehr & Stephan, "Warme- und Stoffubertragung" — channel Nusselt correlations
