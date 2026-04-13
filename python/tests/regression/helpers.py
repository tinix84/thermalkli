"""Thin wrapper functions for regression fixtures.

The regression harness calls module-level functions, but fluid properties
are methods on class instances. These wrappers bridge the gap.
"""

from __future__ import annotations

from thermal_cli.fluids import fluid_registry

# ---------------------------------------------------------------------------
# M7 convection wrappers
# ---------------------------------------------------------------------------

#: Sutherland constants (must match convection.py)
_SUTHERLAND_TREF: float = 291.15
_SUTHERLAND_S: float = 120.0
_MU_REF: float = 18.27e-6


def _air_mu(T: float) -> float:
    return (
        _MU_REF
        * (_SUTHERLAND_TREF + _SUTHERLAND_S)
        / (T + _SUTHERLAND_S)
        * (T / _SUTHERLAND_TREF) ** 1.5
    )


def _air_rho(T: float) -> float:
    return 101325.0 / (287.058 * T)


def _air_kf(T: float) -> float:
    return 7e-5 * T + 5.1e-3


def run_h_forced_laminar(
    length: float, velocity: float, t_ambient: float, t_surface: float
) -> dict:
    """Return {'h': h, 'Re': Re} for forced convection over flat plate.

    Parameters use K (Python convention), matching h_forced.
    """
    from thermal_cli.formula.convection import h_forced

    h, Re = h_forced(length=length, velocity=velocity, t_ambient=t_ambient, t_surface=t_surface)
    return {"h": h, "Re": Re}


def run_h_natural_vertical(length: float, t_ambient: float, t_surface: float) -> dict:
    """Return {'h': h, 'Ra': Ra} for natural convection, vertical plate.

    Ra is computed from first principles (matching the Octave formula) since
    h_natural() only returns (h, Nu).
    """
    from thermal_cli.formula.convection import h_natural

    h, _Nu = h_natural(
        orientation="vertical", length=length, t_ambient=t_ambient, t_surface=t_surface
    )
    Tf = (t_ambient + t_surface) / 2.0
    rho = _air_rho(Tf)
    mu = _air_mu(Tf)
    beta = 1.0 / Tf
    Ra = 0.71 * rho**2 * 9.81 * beta * (t_surface - t_ambient) * length**3 / mu**2
    return {"h": h, "Ra": Ra}


def run_h_radiation(emissivity: float, t_ambient: float, t_surface: float) -> dict:
    """Return {'h': h} for linearized radiation coefficient.

    Parameters use K (Python convention).
    """
    from thermal_cli.formula.convection import h_radiation_linearized

    h = h_radiation_linearized(emissivity=emissivity, t_ambient=t_ambient, t_surface=t_surface)
    return {"h": h}


def run_water_cooling_basic() -> dict:
    """Return {'dT_coolant': ..., 'T_out': ..., 'T_junction': ...} in °C.

    Octave cmd_water_cooling takes °C inputs and outputs °C temperatures.
    Python water_cooling takes K and returns K, so this helper converts back.
    """
    from thermal_cli.formula.water_cooling import water_cooling

    r = water_cooling(
        p_loss=1000.0,
        flow_lpm=5.0,
        t_inlet=298.15,
        rth_jc=0.5,
        n_devices=4,
        cp=3483.0,
        rho=1064.0,
        rth_cl=0.0,
    )
    return {
        "dT_coolant": r.dt_coolant,
        "T_out": r.t_outlet - 273.15,
        "T_junction": r.t_junction - 273.15,
    }


def air_density(temperature: float, pressure: float = 101325.0) -> float:
    air = fluid_registry("airDry")
    return air.density(temperature, pressure)


def air_dynamic_viscosity(temperature: float) -> float:
    air = fluid_registry("airDry")
    return air.dynamic_viscosity(temperature)


def air_thermal_conductivity(temperature: float) -> float:
    air = fluid_registry("airDry")
    return air.thermal_conductivity(temperature)


def air_specific_heat_cp(temperature: float) -> float:
    air = fluid_registry("airDry")
    return air.specific_heat_cp(temperature)


def glycol_density(temperature: float) -> float:
    g = fluid_registry("H2OGly50")
    return g.density(temperature)


def glycol_dynamic_viscosity(temperature: float) -> float:
    g = fluid_registry("H2OGly50")
    return g.dynamic_viscosity(temperature)


def sae30_density(temperature: float) -> float:
    oil = fluid_registry("SAE30")
    return oil.density(temperature)


# --- Layer spreading helpers ---


# ---------------------------------------------------------------------------
# M8 CSPI wrappers
# ---------------------------------------------------------------------------


def run_fan_scaling_fit(v_max: float, dp_max: float, p_fan: float, d: float, n: float) -> dict:
    """Return {'k1': k1, 'k2': k2, 'k3': k3} from fan_scaling_fit."""
    from thermal_cli.cspi.formulas import fan_scaling_fit

    k1, k2, k3 = fan_scaling_fit(v_max=v_max, dp_max=dp_max, p_fan=p_fan, d=d, n=n)
    return {"k1": k1, "k2": k2, "k3": k3}


def run_cspi_optimize_aluminum() -> dict:
    from thermal_cli.cspi.optimizer import cspi_optimize

    r = cspi_optimize(lambda_hs=200.0, a_chip=10e-4, c=0.040, p_fan_max=5.0)
    return {"cspi": r.cspi, "rth": r.rth, "n": float(r.n), "s": r.s}


def layer_spreading_isotropic(
    thick: float, k_op: float, a_in: float, a_out: float, h_eff: float
) -> dict[str, float]:
    from thermal_cli.layers import ThermalLayer

    ly = ThermalLayer(thick=thick, k_op=k_op)
    r_th, r_spread, r_through = ly.resistance(a_in=a_in, a_out=a_out, h_eff=h_eff)
    return {"rTh": r_th, "rThSpread": r_spread, "rThThrough": r_through}


# ---------------------------------------------------------------------------
# M9 sweep wrappers
# ---------------------------------------------------------------------------


def run_optimize_fin_basic() -> dict:
    """Regression fixture wrapper: 3x3 grid over fin thickness/wall thickness.

    Matches the toy grid used in ``optimize_fin/basic.yaml``. Returns
    scalar best Rth + argmin coordinates so it can be round-tripped via
    the JSON regression harness.
    """
    from thermal_cli.sweep.optimize_fin import (
        FinGeometrySweepConfig,
        optimize_fin_geometry,
    )

    cfg = FinGeometrySweepConfig(
        axes={
            "thick_heatsink": [0.006, 0.008, 0.010],
            "thick_wall": [0.0006, 0.0008, 0.0010],
        },
        fixed={
            "width_channel": 0.00105,
            "k_sink": 180.0,
            "rho_sink": 2698.9,
            "l_heated": 0.137,
            "a_hot": 16.9e-3 * 13.7e-3,
            "flowrate_lpm": 1.0,
            "fluid_ref": "H2OGly50",
            "num_channel": 18,
        },
    )
    result = optimize_fin_geometry(cfg)
    best = result.argmin()
    return {
        "best_r_th": result.min(),
        "best_thick_heatsink": best["thick_heatsink"],
        "best_thick_wall": best["thick_wall"],
    }


def run_multi_sim_two_scenarios() -> dict:
    """Regression wrapper: 2-scenario baseplate run (Al vs Cu)."""
    from thermal_cli.sweep.multi_sim import MultiSimScenario, run_multi_sim

    def _sc(name: str, k: float) -> MultiSimScenario:
        return MultiSimScenario(
            name=name,
            lx=0.12,
            ly=0.08,
            thickness=0.005,
            conductivity=k,
            r_sa=0.1,
            t_ambient=298.15,
            devices=[
                {"name": "Q1", "x": 0.03, "y": 0.04, "width": 0.02, "height": 0.02, "power": 100.0},
                {"name": "Q2", "x": 0.09, "y": 0.04, "width": 0.02, "height": 0.02, "power": 100.0},
            ],
            nx=21,
            ny=21,
        )

    result = run_multi_sim([_sc("Al", 200.0), _sc("Cu", 385.0)])
    row_al = next((r for r in result.rows if r.name == "Al"), None)
    assert row_al is not None, "Al scenario missing from multi_sim result"
    row_cu = next((r for r in result.rows if r.name == "Cu"), None)
    assert row_cu is not None, "Cu scenario missing from multi_sim result"
    return {
        "al_t_j_max": row_al.t_j_max,
        "cu_t_j_max": row_cu.t_j_max,
    }


# ---------------------------------------------------------------------------
# M10 forced-conv-sim wrappers
# ---------------------------------------------------------------------------


def run_forced_conv_basic() -> dict:
    """Regression wrapper: VH small heatsink, JF0825 fan, 2 sources (push).

    Config in SI (m, K) matching fixtures/forced_conv_sim/basic.yaml description.
    """
    from thermal_cli.forced_conv.workflow import ForcedConvConfig, run_forced_conv_sim

    cfg = ForcedConvConfig(
        hs_profile="VHSmallHeatsink28mm",
        hs_material="all_aluminum",
        length_x_m=0.063,
        length_y_m=0.130,
        copper_plate_thickness_m=0.0,
        fan_model="JF0825-1H-02",
        fan_count=1,
        ventilation="push",
        impinge_gap_m=0.0,
        sources=[
            {
                "name": "Q1",
                "x_m": 0.0165,
                "y_m": 0.011,
                "width_m": 0.013,
                "height_m": 0.013,
                "power_w": 30.0,
            },
            {
                "name": "Q2",
                "x_m": 0.0165,
                "y_m": 0.0355,
                "width_m": 0.013,
                "height_m": 0.013,
                "power_w": 30.0,
            },
        ],
        t_inlet_k=313.15,
        nx=11,
        ny=11,
        n_fourier=10,
    )
    result = run_forced_conv_sim(cfg)
    return {
        "t_base_max_k": result.t_base_max_k,
        "q_operating_m3s": result.q_operating_m3s,
        "rth_fin_kw": result.rth_fin_kw,
    }
