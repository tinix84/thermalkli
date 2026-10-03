"""Data types for baseplate thermal analysis.

Unified types absorbing thermal-layout-analyzer's domain + TLA's device model.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Device:
    """A heat source on the baseplate.

    Parameters
    ----------
    name : str
        Device identifier.
    x, y : float
        Center position on baseplate [m].
    width, height : float
        Footprint dimensions [m].
    power : float
        Dissipated power [W].
    r_jc : float
        Junction-to-case thermal resistance [K/W].
    r_interface : float
        Interface (TIM) thermal resistance [K/W].
    """

    name: str
    x: float
    y: float
    width: float
    height: float
    power: float
    r_jc: float = 0.0
    r_interface: float = 0.0


@dataclass
class BaseplateConfig:
    """Baseplate geometry, material, and cooling parameters.

    Parameters
    ----------
    lx, ly : float
        Baseplate dimensions [m].
    thickness : float
        Baseplate thickness [m].
    conductivity : float
        Thermal conductivity [W/(m K)].
    r_sa : float
        Heatsink-to-ambient thermal resistance [K/W].
    t_ambient : float
        Ambient temperature [K].
    devices : list[Device]
        Heat sources on the baseplate.
    nx, ny : int
        Number of vertex-centered unknowns including plate-edge points. Boundary dual cells
        span half the spacing between adjacent grid coordinates.
    """

    lx: float
    ly: float
    thickness: float
    conductivity: float
    r_sa: float
    t_ambient: float
    devices: list[Device] = field(default_factory=list)
    nx: int = 41
    ny: int = 41


@dataclass
class DeviceResult:
    """Thermal result for a single device."""

    name: str
    t_base: float  # [K] area-weighted mean over the device thermal footprint
    t_case: float  # [K] case temperature (t_base + P * r_interface)
    t_junction: float  # [K] junction temperature (t_case + P * r_jc)


@dataclass
class BaseplateResult:
    """Complete result from a baseplate solve."""

    t_field: object  # numpy 2D array [K], shape (ny, nx)
    x_grid: object  # numpy 1D array [m]
    y_grid: object  # numpy 1D array [m]
    devices: list[DeviceResult] = field(default_factory=list)
    t_max: float = 0.0  # [K], maximum grid-point temperature
    t_mean: float = 0.0  # [K], control-volume area-weighted mean
    t_j_max: float = 0.0  # [K]
    t_j_mean: float = 0.0  # [K]
    t_j_spread: float = 0.0  # [K]
    heat_input_W: float = 0.0  # [W], integrated control-volume source power
    heat_rejected_W: float = 0.0  # [W], integrated distributed-sink power
    heat_balance_relative_error: float = 0.0
    linear_residual_norm: float = 0.0  # normalized residual of A * delta_T = source_power
