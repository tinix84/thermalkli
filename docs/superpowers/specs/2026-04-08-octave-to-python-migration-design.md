# Octave → Python Migration Design

**Date**: 2026-04-08
**Status**: Design approved, pending implementation plan
**Target repo**: `~/claude_wsl/octave/thermal`
**Target package**: `thermal-cli` (import: `thermal_cli`)

## 1. Goals and non-goals

### Goals

- Port the full Octave thermal library (`mfiles/Thermal/`) to a Python package (`thermal-cli`) that lives in this repo.
- Absorb the `thermal-layout-analyzer` Python project so it can be archived externally.
- Port the useful portion of the legacy SoftwareTermico tool (analytical multi-source baseplate model + fan database + parametric sweeps) as Python-idiomatic modules — *not* a literal translation.
- Replace the Octave `thermal_cli.m` dispatcher with a Typer-based Python CLI covering all 43 current commands plus new baseplate commands from TLA.
- Replace `prova_grafica.m` and SoftwareTermico's interactive menus with a Jupyter + ipywidgets notebook frontend.
- Deprecate Octave cleanly: `mfiles/` is deleted in a single PR once parity is proven automatically.

### Non-goals

- Literal 1:1 class-for-class translation. Python-idiomatic redesigns (dataclasses, Protocols, registries, composition over inheritance) are expected and encouraged.
- Supporting `.m` config files at runtime (a one-shot converter is provided instead).
- Supporting Excel (`.xlsx`) at runtime — Excel is used only as an output report format.
- Porting `LossTemperatureInteraction/` (depends on external SVM_7 function, explicitly out of scope per CLAUDE.md).
- Porting SoftwareTermico GUI code (`prova_grafica.m`, interactive menus) as-is — these are replaced by Jupyter notebooks.
- A standalone web app (Voilà / Streamlit / Panel) — not in scope.
- A C++/Rust rewrite or WebAssembly build of the solver core (inherited from TLA's roadmap) — filed as open issues, not scheduled.

## 2. Strategic decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| D1 | Target location | `python/` subdirectory of this repo | Octave + Python side-by-side during port; atomic commits touch both sides; easy regression reference. |
| D2 | Scope | Full `mfiles/Thermal/` + `Tplane_dist` from SoftwareTermico + fan DB + parametric sims + Jupyter GUI | Covers 100% of Octave functionality plus TLA's baseplate capability. |
| D3 | Style | Python-idiomatic redesigns allowed | No inheritance tree cloning; dataclasses, Protocols, registries. |
| D4 | FEMM integration | Deferred (stubbed until M13) → wired through `py2femm` | Avoids committing to py2femm's mid-refactor API; ~40 of 43 commands ship without blocking. |
| D5 | Parity gate | Hybrid: literature tests for formulas + Octave-regression tests for workflows | Literature is authoritative for physics; Octave-regression catches integration drift. |
| D6 | Port sequencing | Regression harness first, then bottom-up (Formula → Model → Designer → Optimizer → CLI → GUI) | Harness enforces parity from commit 1; cannot merge numerical drift. |
| D7 | Package name | `thermal-cli` | Matches existing `thermal_cli.m` dispatcher naming. |
| D8 | CLI framework | Typer | Type-hint-driven, least boilerplate across 43 commands. |
| D9 | Config format | YAML (Pydantic v2 validated) at runtime; `.m → .yaml` one-shot converter for legacy | Human-readable, version-controllable, TLA already uses it. |
| D10 | Database format | **CSV authoritative at runtime**; xlsx retained only as output report artifact | Fast, diff-friendly, CI-compatible; xlsx becomes a *product*, not an input. |
| D11 | TLA absorption mechanism | Copy + adapt (no git subtree / history preservation) | TLA is v0.1 with shallow history; clean port is cleaner than graft. |
| D12 | TLA repo fate | Archived externally after M6 | Superseded message in README; read-only on GitHub. |
| D13 | TLA v2 roadmap (C++/Rust, WASM, REST API) | Filed as open issues in absorbing repo | Not scheduled, preserved as future direction. |
| D14 | FEMM commands pre-M13 | Exposed with `NotImplementedError` pointing to blocking issue | Stable command surface; users see "not yet" not "not found". |
| D15 | Post-M14 repo layout | Promote `python/src/thermal_cli/` to top-level `src/thermal_cli/` | Standard Python repo shape after Octave is gone. |
| D16 | Octave regression harness fate | Retired at M14 | Literature tests become the permanent regression floor. |

## 3. Package architecture

### Runtime layout (during port, M0 through M13)

```
~/claude_wsl/octave/thermal/
├── mfiles/                           # FROZEN — Octave reference; deleted at M14
├── db/
│   ├── heatsinks.csv                 # canonical at runtime (migrated in M2/M4)
│   ├── fluids.csv                    # canonical at runtime (migrated in M2)
│   ├── tim.csv                       # canonical at runtime (migrated in M11)
│   └── legacy/                       # original .xlsx kept for reference, deleted at M14
├── docs/
│   ├── prd.md
│   ├── HISTORY.md                    # migration + TLA absorption record
│   └── superpowers/specs/
├── python/
│   ├── pyproject.toml                # name = "thermal-cli"
│   ├── src/thermal_cli/
│   │   ├── __init__.py
│   │   ├── formula/                  # pure functions — fin, radiation, Nusselt helpers
│   │   ├── fluids/                   # GasProperty, LiquidProperty, registry
│   │   ├── layers/                   # ThermalLayer, LayerStack, spreading (Lee/Simons/Ying)
│   │   ├── heatsinks/                # HeatsinkBase Protocol, ExtrudedFin, registry, fan DB, fan scaling laws
│   │   ├── designer/                 # ThermalModelSemi, PCB model, 5 heat-path cases
│   │   ├── baseplate/                # NEW: multi-source 2D — FDM backend (from TLA) + analytical backend (from Tplane_dist)
│   │   ├── optimizer/                # parametric sweep engine (unifies Thermal/Optimizer + Simulazione_multipla)
│   │   ├── cspi/                     # Drofenik/Kolar CSPI, eq. 45/50
│   │   ├── femm/                     # STUBBED until M13 → py2femm client wrapper
│   │   ├── io/
│   │   │   ├── config.py             # Pydantic v2 schemas, YAML load, override merge
│   │   │   ├── databases.py          # CSV readers for db/*.csv
│   │   │   ├── reports.py            # xlsx report writer (openpyxl)
│   │   │   └── convert_m_to_yaml.py  # .m struct → .yaml migration utility
│   │   ├── cli/                      # Typer app + one module per command group
│   │   └── notebook/                 # ipywidgets helpers shared by the 3 GUI notebooks
│   ├── tests/
│   │   ├── unit/                     # pure pytest, no Octave
│   │   ├── literature/               # authoritative reference values (from test_literature.m)
│   │   ├── regression/               # Octave↔Python parity harness
│   │   │   ├── conftest.py           # octave runner, assert_close
│   │   │   └── fixtures/             # one YAML per fixture
│   │   └── shared/                   # cross-layer test fixtures (devices, materials, configs)
│   └── notebooks/
│       ├── examples/                 # absorbed from thermal-layout-analyzer
│       └── gui/
│           ├── layout_builder.ipynb
│           ├── parametric_explorer.ipynb
│           └── cspi_explorer.ipynb
└── .github/workflows/
    └── ci.yml                        # pytest (unit + literature + regression), lint, octave install
```

### Post-M14 layout (after Octave deprecation)

```
~/claude_wsl/octave/thermal/
├── src/thermal_cli/        # promoted from python/src/
├── tests/                  # no regression/ directory — only unit/ and literature/
├── notebooks/
├── db/                     # CSV only; legacy/ deleted
├── docs/
├── pyproject.toml
└── .github/workflows/ci.yml # no octave dependency
```

### Python-idiomatic mapping guidelines

| Octave pattern | Python pattern |
|---|---|
| `classdef X < handle` (mutable) | `class X:` regular class |
| `classdef X` (value object) | `@dataclass(frozen=True)` |
| `classdef X < handle` with `get.*` dependent properties | `@dataclass` + `@cached_property` |
| `fluidPropertyFactory('airDry')` | `fluid_registry["airDry"]()` (dict-based registry) |
| `xlsread('db/heatsinks.xlsx', 'Sheet1')` | `pandas.read_csv("db/heatsinks.csv")` |
| `parse_args(varargin)` | Typer function with type hints |
| Italian var names (SoftwareTermico) | English + SI units enforced by Pydantic validators |
| `mm` units in SoftwareTermico | meters throughout; convert at I/O boundary |
| `error('...')` | `raise ValueError(...)` with structured error messages |

## 4. Regression harness

This is the **cornerstone** of the migration — it makes "deprecate Octave" an automated decision instead of a judgment call.

### Mechanism

```python
# python/tests/regression/conftest.py
def run_octave(script: str, workdir: Path) -> dict:
    """Run an Octave snippet, expect jsonencode'd stdout, return parsed dict."""
    result = subprocess.run(
        ["octave", "--no-gui", "--quiet", "--path", OCTAVE_PATHS, "--eval", script],
        capture_output=True, text=True, cwd=workdir, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"octave failed: {result.stderr}")
    return json.loads(result.stdout.strip())

def assert_close(oct_out: dict, py_out: dict, rtol: float = 1e-6, atol: float = 1e-12):
    """Recursively compare nested dicts with numerical tolerance."""
    ...
```

### Fixture shape

One YAML file per fixture, living in `python/tests/regression/fixtures/<command>/<case>.yaml`:

```yaml
command: fin-efficiency
description: Basic rectangular fin, literature-style inputs
inputs:
  length: 0.05
  k: 200.0
  h: 30.0
octave_script: |
  addpath('mfiles/Thermal/Formula');
  eta = finEfficieny(0.05, 200, 30);
  disp(jsonencode(struct('eta', eta)));
python_call:
  module: thermal_cli.formula.fin
  function: fin_efficiency
  args: {length: 0.05, k: 200.0, h: 30.0}
tolerance:
  rtol: 1e-6
  atol: 1e-12
```

### Test runner

```python
@pytest.mark.parametrize("fixture_path", discover_fixtures())
def test_regression_parity(fixture_path):
    fx = load_fixture(fixture_path)
    oct_out = run_octave(fx.octave_script, REPO_ROOT)
    py_out = call_python(fx.python_call)
    assert_close(oct_out, py_out, **fx.tolerance)
```

### Design rules

- **Wire format is JSON** — Octave `jsonencode()` ↔ Python `json.loads()`. No stdout regex parsing.
- **Default tolerance**: `rtol=1e-6`, `atol=1e-12`. FEMM regressions (M13) use looser `rtol=5e-2` because FEM has its own discretization error budget.
- **Every ported command ships with ≥1 regression fixture** in the same PR — non-negotiable.
- **On diff**: test output shows side-by-side Octave value / Python value / relative error / tolerance for quick triage.
- **M0 ships 1 proof-of-life fixture** (`fin_efficiency/basic.yaml`) to validate the mechanism before any porting begins.
- **CI installs Octave headless via apt** — `octave-cli` on ubuntu-latest runners; ~5s startup per script, acceptable for ≤100 fixtures in the steady state.
- **Future optimization (not MVP)**: batch all regressions into one Octave process via a single driver script to amortize startup cost.
- **Sunset at M14**: the entire `tests/regression/` directory is deleted with `mfiles/`. Literature tests in `tests/literature/` remain as the permanent reference.

## 5. Port order and milestones

14 milestones, each a merge-able PR bundle.

| # | Milestone | Scope | Gate |
|---|---|---|---|
| **M0** | Bootstrap | `python/` skeleton, `pyproject.toml`, CI (pytest + lint + octave install), regression harness infra, 1 proof fixture (`fin_efficiency`) | Harness runs in CI, proof fixture green |
| **M1** | Formula layer + `.m → .yaml` converter | Port `mfiles/Thermal/Formula/` → `thermal_cli/formula/` (fin efficiency, 5 radiation helpers, standalone Nusselt). `convert-config` utility for legacy `.m` structs | Unit + literature + regression fixtures for every function |
| **M2** | Fluids + `db/fluids.csv` | `GasProperty`, `LiquidProperty`, `fluidPropertyFactory` → `thermal_cli/fluids/`. Migrate `FluidData.xlsx` → `fluids.csv`. `db/legacy/` created | 3 fluid refs parity-tested across temperature range |
| **M3** | Layers and spreading | `ThermalLayer`, `ThermalLayerStack`, Lee/Simons/Ying spreading → `thermal_cli/layers/` | Regression on 5+ layer-stack configs; literature on spreading |
| **M4** | Heatsinks + channel model + `db/heatsinks.csv` | `HeatsinkBase`, `ExtrudedFin`, channel Nusselt (laminar + Gnielinski), Reynolds, hydraulic ops. Migrate `heatsinks.xlsx` → `heatsinks.csv` | `channel-rth`, `channel-dp`, `heatsink-rth` green with regression |
| **M5** | Designer / semi-on-PCB | `ThermalModelSemi`, `ThermalPcb`, 5 heat-path cases → `thermal_cli/designer/`; `semi-on-pcb` workflow command | Regression on all 5 heat-path cases using existing TO247 / CSC128 configs |
| **M6** | Baseplate multi-source (absorb TLA) | Import TLA FDM solver + port `Tplane_dist.m` analytical backend → `thermal_cli/baseplate/` behind a common `BaseplateSolver` Protocol. Pydantic schema. `baseplate-fdm`, `baseplate-analytical`, `baseplate-compare` commands | TLA's existing tests pass; Octave-regression on `Tplane_dist`; **TLA repo archived** |
| **M7** | Natural / forced convection + radiation h-coeffs | `h-coeff`, `free-conv`, `natural-conv-hs`, `radiation`, `water-cooling`, `hydraulic-op`, `fin-rth` | All basic commands green |
| **M8** | CSPI / Drofenik / fan scaling | Port `cmd_cspi`, `cmd_cspi_optimize`, `cmd_fan_fit`, eq. 45/50 | `cspi`, `cspi-optimize`, `fan-fit`, `cspi-sweep` green |
| **M9** | Optimizer + parametric sims | Unified sweep engine (absorbs `Thermal/Optimizer/` + SoftwareTermico `Simulazione_multipla`) | `optimize-fin`, `multi-sim` green + sweep DSL documented |
| **M10** | Fan database + `forced-conv-sim` workflow | Port SoftwareTermico fan DB (Italian → English/SI), plane-distribution workflow | `forced-conv-sim` green |
| **M11** | Transient + TIM + `db/tim.csv` | Zth, TIM lookup. Migrate `Thermal_Interface_Materials.xlsx` → `tim.csv` | `zth`, `tim-lookup` green |
| **M12** | Jupyter frontend | 3 notebooks: `layout_builder`, `parametric_explorer`, `cspi_explorer`. ipywidgets helpers in `thermal_cli/notebook/` | Demoable notebook gallery |
| **M13** | FEMM integration via py2femm | Wire `gen-femm` and `compare-femm` through `py2femm` client. Port 5 Lua generators to Python geometry specs. Auto-run pipeline replaces manual FEMM round-trip | `gen-femm`, `compare-femm` green against all 5 generator types (rtol=5e-2) |
| **M14** | Deprecation | Delete `mfiles/`, delete `db/legacy/`, remove octave from CI, delete `tests/regression/`, promote `python/src/thermal_cli/` → top-level `src/`. Tag `v1.0.0` | Single green PR ends Octave |

### Dependency graph

```
M0 ──► M1 ──► M2 ──► M3 ──► M4 ──► M5
                  │                  │
                  │                  ├─► M7 ──► M8 ──► M9 ──► M10
                  │                  │                         │
                  └─► M6             └─► M11                   │
                      │                   │                    │
                      └───┬───────────────┘                    │
                          │                                    │
                          └─► M12 ◄─────────────────────────────┘
                                   │
                                   └─► M13 (blocked on py2femm Phase 1)
                                          │
                                          └─► M14
```

- **M0 blocks everything.**
- M1–M4 are parallelizable after M0 if multiple people / sessions work in parallel.
- **M6 unblocks TLA deprecation** — as soon as M6 ships, `thermal-layout-analyzer` is archived.
- **M13 is externally blocked** on py2femm Phase 1 MVP; M14 cannot start until M13 is green.
- M12 needs a minimum of M5 + M6 + M9 for its three notebooks to have real backends.

## 6. Jupyter frontend

### Scope

Replaces: `prova_grafica.m` (old Octave GUI), SoftwareTermico interactive menus, the "run a script and squint at the figure" workflow.

Pure Jupyter + `ipywidgets` + `matplotlib` / `plotly`. No web app.

### Three notebooks (shipped in M12)

**`layout_builder.ipynb`** — interactive baseplate layout editor
- Widgets: baseplate dimensions, material picker, heatsink R_sa slider, device table (x, y, w, h, P, R_jc)
- Matplotlib canvas rendering baseplate + device rectangles; click-drag to reposition
- "Solve" button runs `baseplate-fdm` or `baseplate-analytical` backend, renders T-field heatmap
- "Export" button saves widget state as YAML — reproducible outside the notebook
- Direct replacement for TLA's intended (never-shipped) notebook UX

**`parametric_explorer.ipynb`** — sweep visualizer
- Widgets: select 1–2 swept parameters from a dropdown (fin width, spacing, flowrate, …)
- Backend: `thermal_cli.optimizer.sweep(...)`
- Plot: 1D line chart or 2D heatmap of objective (Rth, CSPI, T_j_max) vs swept dimensions
- Replaces `Simulazione_multipla/` menus

**`cspi_explorer.ipynb`** — Drofenik CSPI study replicator
- Widgets: fan diameter, material, target airflow
- Reproduces Drofenik CIPS06 Fig. 4/5 interactively
- Side-by-side: user's design point vs Drofenik reference curves
- Fan scaling law fit if user uploads a P-Q CSV

### Architectural rules

- **Notebooks contain zero business logic.** Every computation is a thin call to `thermal_cli.*`. Anything a notebook does must be reproducible from the CLI with the same inputs.
- **No Octave runtime dependency.** Jupyter is Python-pure; regression harness (which needs Octave) is CI-only.
- **Config round-trip.** Every widget state serializes to the same YAML schema as the CLI; loading a YAML restores widget state. Guarantees notebook and CLI are interchangeable.
- **Plotting**: matplotlib for static / publication figures, plotly for interactive (hover, zoom) heatmaps.
- **`thermal_cli/notebook/` module**: shared ipywidgets helpers (device table editor, material dropdown, unit-aware number input) so the three notebooks don't duplicate widget code.

## 7. I/O, configs, databases

### Configs

- **Format**: YAML, validated by **Pydantic v2** models in `thermal_cli/io/config.py`.
- **Override mechanism**: `thermal semi-on-pcb config.yaml --heatsink.flowrate 0.02` — Typer parses, `apply_overrides(config, flags)` merges into the Pydantic model with re-validation.
- **Discovery**: explicit path or `./thermal.yaml` in CWD (like `pyproject.toml`).
- **Legacy `.m` support**: one-shot `thermal convert-config old.m new.yaml` utility ships in M1. Parses flat Octave struct definitions with a small regex-based reader.

### Databases

- **Runtime format**: CSV in `db/*.csv` — authoritative, version-controlled, diff-friendly, CI-compatible.
- **Original xlsx files**: moved to `db/legacy/` at migration time, deleted at M14.
- **Migration**: `scripts/migrate_xlsx_to_csv.py` one-shot utility (not a CLI command) reads current xlsx and writes canonical CSVs once. Committed outputs are the source of truth thereafter.
- **Readers**: `thermal_cli/io/databases.py` — pandas-based, with caching and column schema validation.

### Reports

- **xlsx is output-only**: `thermal_cli/io/reports.py` provides `write_xlsx_report(results, path)` using openpyxl with formatted tables.
- **Used by**: `multi-sim`, `cspi-sweep`, `optimize-fin` via a `--report out.xlsx` flag.
- **Other output formats**: `--output results.json` or `--output results.csv` (extension-detected). JSON is also the regression harness wire format.
- **Figures**: `--plot` flag saves matplotlib PNG or plotly HTML next to the results file.

## 8. TLA absorption mechanics

### What to pull

| TLA source | Destination | Milestone |
|---|---|---|
| `src/thermal_analyzer/core/domain.py` | `thermal_cli/baseplate/grid.py` | M6 |
| `src/thermal_analyzer/core/physics.py` | Merged into `thermal_cli/fluids/` + `thermal_cli/baseplate/physics.py` | M6 |
| `src/thermal_analyzer/core/solver.py` | `thermal_cli/baseplate/fdm_solver.py` | M6 |
| `src/thermal_analyzer/app/input_parser.py` | **Dropped** — superseded by Pydantic configs | M6 |
| `src/thermal_analyzer/app/thermal_calc.py` | `thermal_cli/cli/baseplate.py` (Typer command) | M6 |
| `src/thermal_analyzer/app/comparator.py` | `thermal_cli/baseplate/compare.py` + `baseplate-compare` CLI | M6 |
| `src/thermal_analyzer/utils/validation.py` | `thermal_cli/baseplate/validation.py` | M6 |
| `tests/` | `python/tests/unit/test_baseplate_*.py` | M6 |
| `examples/*.yaml` | `python/tests/fixtures/baseplate/` | M6 |
| `notebooks/examples/` | `python/notebooks/examples/baseplate/` | M6 → M12 |
| `docs/`, `SPRINT_PLAN.md` | Merged into this repo's `docs/`, attributed in `HISTORY.md` | M6 |
| TLA `pyproject.toml` deps | Merged into `python/pyproject.toml` | M0 |
| `LICENSE` | Kept, noted in `HISTORY.md` | M0 |

### Mechanism

- **Copy + adapt**, not `git subtree` or `git filter-repo`. TLA is v0.1 with shallow history; the absorption is a port + redesign, not a graft.
- **Commit convention during M6**: `feat(baseplate): port TLA solver [absorbed from thermal-layout-analyzer@<sha>]`. Traceable without history surgery.
- **M6 completion action**: add a banner to `thermal-layout-analyzer` README ("Superseded by `thermal-cli` in [this repo]. Archived 2026-XX-XX.") and archive the GitHub repo read-only.

### Redesign decisions during absorption

- **Devices unified**: TLA's `HeatSource` dataclass merges with the general `Device` type used by `semi-on-pcb` — one canonical device representation.
- **Pluggable vertical coupling**: TLA's implicit uniform `R''_vert` becomes explicit; M6 ships with a `UniformVerticalCoupling` default, but the interface allows spatially-varying extensions later.
- **Two backends behind one Protocol**: `BaseplateSolver` Protocol; `FDMBackend` (from TLA) and `AnalyticalBackend` (from `Tplane_dist`). `baseplate-compare` can run both and report the discrepancy as a validation signal.

### Items explicitly NOT pulled

- TLA `input_parser.py` (Pydantic replaces it)
- TLA internal dataclass shapes (redesigned)
- TLA v2 roadmap (C++/Rust rewrite, WASM, REST API) — filed as GitHub issues in this repo, not scheduled

## 9. FEMM integration (M13)

### Interim state (M0 → M12)

- `thermal_cli/femm/` module exists with stubbed functions that raise `NotImplementedError("pending py2femm Phase 1 — see issue #N")`
- `gen-femm` and `compare-femm` CLI commands are **exposed** and documented; running them exits with a clear message pointing to the blocking issue
- Keeps the command surface stable — users see "not yet implemented" rather than "command not found"

### Activation

Triggered when py2femm ships a stable Phase 1 client API (per memory, currently Task 1 of 15 on `feat/client-agent-architecture`).

- Add `py2femm = ">=<version>"` to `python/pyproject.toml`
- Port the 5 Octave Lua generators (`femm_semi_on_pcb`, `femm_extruded_fin`, `femm_baseplate_spreading`, `femm_forced_air_heatsink`, `femm_drofenik_heatsink`) to Python functions that emit py2femm geometry specs
- `gen-femm` calls `py2femm_client.run(spec)` end-to-end: FEMM is invoked automatically, CSV is parsed, comparison happens in one shot
- `compare-femm` becomes a thin wrapper that additionally runs the analytical model and diffs
- Regression fixtures use `rtol=5e-2` (FEM discretization error budget)

## 10. End-state (post-M14)

### Repo layout

```
~/claude_wsl/octave/thermal/
├── src/thermal_cli/          # promoted from python/src/
├── tests/
│   ├── unit/
│   └── literature/           # NO regression/ — retired with Octave
├── notebooks/
│   ├── examples/
│   └── gui/
├── db/                       # CSV only; legacy/ deleted
├── docs/
│   ├── prd.md
│   ├── architecture.md
│   └── HISTORY.md
├── pyproject.toml
└── .github/workflows/ci.yml  # no octave
```

### M14 PR steps (atomic)

1. Verify: all regression fixtures green, all literature tests green, no live `NotImplementedError` except genuinely advanced FEMM cases.
2. `git rm -r mfiles/ db/legacy/ python/tests/regression/`
3. Remove `octave` from `.github/workflows/ci.yml`.
4. `git mv python/src/thermal_cli src/thermal_cli`; `git mv python/tests tests`; `git mv python/notebooks notebooks`; remove empty `python/` dir.
5. Update `pyproject.toml` paths.
6. Update `README.md` and `CLAUDE.md` to reflect Python-only state.
7. Tag `v1.0.0`.
8. Confirm `thermal-layout-analyzer` external repo is archived (should already be from M6).

## 11. Testing strategy summary

Three permanent test layers + one transitional layer:

| Layer | Location | Runs | Purpose | Lifetime |
|---|---|---|---|---|
| **Unit** | `tests/unit/` | pytest | Isolated module behavior, edge cases, error paths | Permanent |
| **Literature** | `tests/literature/` | pytest | Validate against published reference values (ported from `test_literature.m`) | Permanent — the authoritative reference after M14 |
| **Regression** | `tests/regression/` | pytest + octave subprocess | Catch Octave↔Python numerical drift during port | **Transitional** — deleted at M14 |
| **Notebook smoke** | `tests/notebook/` (optional, M12) | `pytest --nbmake` | Run notebooks top-to-bottom, verify no cells error | Permanent |

CI configuration:
- M0 installs `octave-cli` via apt
- M14 removes the octave install step
- Lint: `ruff check` + `ruff format --check`
- Type-check: `mypy` on `thermal_cli/` (strict on new code, permissive during early ports)

## 12. Open questions and deferred decisions

None blocking. The following are intentionally deferred:

- **py2femm API shape** — decided at M13, when py2femm Phase 1 ships.
- **Exact fan DB schema** — decided at M10, after reading SoftwareTermico's fan database structure.
- **Sweep DSL syntax** — decided at M9, informed by existing `Simulazione_multipla` use cases.
- **Whether to publish `thermal-cli` to PyPI** — decided after M14; not in scope for this migration.

## 13. Success criteria

Migration is complete when all of the following hold:

1. All 43 Octave CLI commands have Python equivalents exposed via `thermal` entrypoint.
2. All literature tests (19+ cases from `test_literature.m`) pass in Python.
3. All Octave-regression fixtures pass with `rtol ≤ 1e-6` (formulas/workflows) or `rtol ≤ 5e-2` (FEMM).
4. The 3 Jupyter notebooks run top-to-bottom without error.
5. `thermal-layout-analyzer` repo is archived externally.
6. `mfiles/` is deleted.
7. CI no longer depends on Octave.
8. `v1.0.0` is tagged.
