"""Water-cooling energy balance calculator.

Computes coolant temperature rise, outlet temperature, and junction temperature
for a liquid-cooled power-electronics assembly using the bulk energy balance.

Typical coolant for power modules: 50 % water / 50 % ethylene-glycol mixture.
Default properties (cp=3483 J/(kg K), rho=1064 kg/m³) correspond to this mix
at approximately 65 °C.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WaterCoolingResult:
    """Results of the water-cooling energy balance.

    Attributes
    ----------
    dt_coolant : float
        Coolant temperature rise across the cold-plate [K].
    t_outlet : float
        Coolant outlet temperature [K].
    t_junction : float
        Semiconductor junction temperature [K].
    m_dot : float
        Coolant mass flow rate [kg/s].
    p_per_device : float
        Power dissipated per device [W].
    """

    dt_coolant: float
    t_outlet: float
    t_junction: float
    m_dot: float
    p_per_device: float


def water_cooling(
    *,
    p_loss: float,
    flow_lpm: float,
    t_inlet: float,
    rth_jc: float,
    n_devices: int,
    cp: float = 3483.0,
    rho: float = 1064.0,
    rth_cl: float = 0.0,
) -> WaterCoolingResult:
    """Compute water-cooling energy balance for a liquid-cooled assembly.

    All arguments are keyword-only.

    Parameters
    ----------
    p_loss : float
        Total power loss dissipated into the coolant [W].
    flow_lpm : float
        Coolant volumetric flow rate [l/min].
    t_inlet : float
        Coolant inlet temperature [K].
    rth_jc : float
        Junction-to-case thermal resistance per device [K/W].
    n_devices : int
        Number of parallel devices sharing the total loss.
    cp : float, optional
        Coolant specific heat capacity [J/(kg K)].
        Default 3483 J/(kg K) — 50/50 water/ethylene-glycol at ~65 °C.
    rho : float, optional
        Coolant density [kg/m³].
        Default 1064 kg/m³ — 50/50 water/ethylene-glycol at ~65 °C.
    rth_cl : float, optional
        Case-to-liquid (spreading/TIM) thermal resistance per device [K/W].
        Default 0.0 (neglected).

    Returns
    -------
    WaterCoolingResult
        Dataclass with dt_coolant, t_outlet, t_junction, m_dot, p_per_device.

    Notes
    -----
    Physics:

    .. math::

        \\dot{q} = \\frac{\\text{flow\\_lpm}}{1000 \\cdot 60}  \\quad [\\text{m}^3/\\text{s}]

        \\dot{m} = \\rho \\, \\dot{q}

        \\Delta T = \\frac{P_{\\text{loss}}}{c_p \\, \\dot{m}}

        T_{\\text{out}} = T_{\\text{in}} + \\Delta T

        P_{\\text{dev}} = \\frac{P_{\\text{loss}}}{N}

        T_j = T_{\\text{out}} + P_{\\text{dev}} \\left( R_{\\text{jc}} + R_{\\text{cl}} \\right)
    """
    # Volumetric flow rate [m³/s]
    q_m3s = flow_lpm / 1000.0 / 60.0

    # Mass flow rate [kg/s]
    m_dot = rho * q_m3s

    # Coolant temperature rise [K]
    dt_coolant = p_loss / (cp * m_dot)

    # Outlet temperature [K]
    t_outlet = t_inlet + dt_coolant

    # Power per device [W]
    p_per_device = p_loss / n_devices

    # Junction temperature [K] — worst-case device sees outlet temperature
    t_junction = t_outlet + p_per_device * (rth_jc + rth_cl)

    return WaterCoolingResult(
        dt_coolant=dt_coolant,
        t_outlet=t_outlet,
        t_junction=t_junction,
        m_dot=m_dot,
        p_per_device=p_per_device,
    )
