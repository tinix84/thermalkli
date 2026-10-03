# M8–M10 liquid, transient, validation, and performance workflows

## M8: pump-limited liquid cooler

The liquid model is available through the Python API in thermal_cli.liquid_cooling and the command thermal liquid-cooler --config FILE. YAML values for flow, pressure, dimensions, heat, and temperatures use SI units; temperatures are kelvin.

The pump curve gives available pressure over its declared total-flow domain. The solver does not extrapolate outside it. Equal parallel channels receive Q_total / channel_count; each branch reports its flow, Reynolds number, friction drop, local minor loss, and any empirical port correction. Slot and circular channels use separate hydraulic-diameter and laminar friction relations, with a blended 2300–4000 transition and a smooth-pipe/rough-pipe Haaland turbulent factor.

Liquid property tables are linearly interpolated only inside their tabulated temperature range. The bulk energy balance iterates density and heat capacity at mean fluid temperature until Q = m_dot * cp(T_mean) * (Tout - Tin). Zero flow with positive heat is reported as invalid.

The ideal slot resistance is the plate-to-mean-bulk convection estimate. The optional inlet/outlet heat-transfer-area resistance is kept separate and combined in parallel; the bulk mean-temperature rise is then added to express a plate-to-inlet-coolant resistance. The smooth flat-plate Nusselt blend is an engineering estimate, not an exact reproduction of PESC Eq. 7. The PESC 2004 inlet/outlet pressure correction is empirical and applies only to its unchanged port geometry. The B06 literature value remains a source observation until matching geometry and boundary data are available.

Cold-plate, pump, pipe, and heat-exchanger volumes are separate inputs. The system total is their sum; a cold-plate-only value is not used as full-loop volume.

## M9: physical transient networks

thermal_cli.transient.rc_network provides a nodal model with grounded capacitances and explicit resistive connections, plus a Cauer ladder constructor. Cauer arrays remain series ladder elements and are not interpreted as parallel Foster branches.

PowerWaveform accepts an explicit time grid and one independent power column per network node. The solver propagates piecewise-linear power segments with an exact augmented matrix exponential and retains initial node temperatures, ambient reference, fit provenance, and supported pulse duration. The periodic solver repeats a cycle until the start-of-cycle state meets its absolute and relative tolerances; the cycle count is a maximum bound. The onsemi AND8215/D Rev. 1 factory constructs the source's grounded 16-node SPICE-compatible network and rejects pulses shorter than its fastest fitted time constant.

## M10: evidence registry

Run thermal validation-report --output docs/validation_registry_m8_m10_reviewed.json to execute the accepted reference and behavior cases through one report format. Records include B01, B02, B03, B05, B06, B07, B08, M8 energy balance, and M9 dynamic behavior.

Each record distinguishes execution_status from acceptance_status and retains its acceptance criteria, outputs, evidence status, conditions, and limitations. A source observation can be recorded without claiming model validation. B01/B02 transient curve parity, B03 FEMM/source-field parity, exact B05 source parity, B06 model reproduction, and B08 source-geometry parity remain unresolved. B07 uses the Sol-reviewed 20% fixture-specific resistance comparison criterion; this is not a general accuracy bound or exact source parity.

The report-level status is passed only when an executed acceptance predicate passes, recorded when evidence is retained without a model acceptance predicate, and failed when execution or an acceptance predicate fails. B05's resistance estimates are zero-load small-signal values at the source's 313.15 K constant-property reference; the separate M8 energy case covers loaded outlet heating with a temperature-dependent glycol table.

The canonical generated registry is docs/validation_registry_m8_m10_reviewed.json. Earlier reports are preserved as historical snapshots in docs/archive/validation_registry_pre_m10_20261003.json and docs/archive/validation_registry_m8_m10_pre_review_20261003.json; they are not the canonical current report.

## M10: representative performance report

Run thermal performance-report --output docs/performance_m10_20261003.json --iterations 5 to benchmark a 3 by 3 workload matrix: grids of 21 by 21, 41 by 41, and 81 by 81 points; device counts of 1, 4, and 16; and 3 repeated scenarios in each orchestration sample. Each workload has five timed samples per measured phase after one warmup.

The report measures YAML parsing/configuration mapping, source mapping, sparse matrix assembly, SciPy factorization plus solve, and full workflow orchestration separately. It records median, p95, minimum latency and operations per second, with Python, NumPy, SciPy, operating system, processor, and logical CPU count. FEMM is explicitly marked not measured because no FEMM backend is configured in this benchmark workload.

The 2026-10-03 post-optimization WSL2 run used Python 3.12.3, NumPy 2.4.1, SciPy 1.17.0, and 24 logical CPUs. Orchestration p95 for three repeated scenarios ranged from 2.3–3.7 ms at 21 by 21 points, 8.3–8.8 ms at 41 by 41, and 31.9–41.5 ms at 81 by 81 across the three device counts. These synthetic baseplate measurements describe this runtime and workload only.

The sparse assembly loop was vectorized after the initial benchmark identified it as a hotspot. Across the three device counts, median assembly time fell from 0.521 to 0.067 ms at 21 by 21, from 1.917 to 0.096 ms at 41 by 41, and from 7.477 to 0.263 ms at 81 by 81. The preserved pre-optimization comparison is docs/archive/performance_m10_pre_vectorization_20261003.json. SciPy factorization plus solve remains separately measured; no Rust recommendation is supported without a user latency target.

No user latency target is currently declared, so the report makes no Rust recommendation. A future recommendation requires a declared target, the specific optimized numerical phase, a description of the Python optimization, and evidence that Python parity passed; these details are serialized with the benchmark result.
