"""Gas property model with temperature-dependent interpolation.

Ported from ``mfiles/Thermal/Model/GasProperty.m``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from thermal_cli.database import open_database_csv


@dataclass
class GasProperty:
    """Temperature-dependent gas properties loaded from CSV.

    Uses linear interpolation on tabulated data. Density supports pressure
    correction via the ideal gas law.
    """

    fluid_ref: str
    _temperature: np.ndarray = field(repr=False, init=False)
    _cp: np.ndarray = field(repr=False, init=False)
    _dyn_visc: np.ndarray = field(repr=False, init=False)
    _therm_cond: np.ndarray = field(repr=False, init=False)
    _density: np.ndarray = field(repr=False, init=False)
    _pressure_ref: float = field(repr=False, init=False)

    def __post_init__(self) -> None:
        with open_database_csv(f"fluid_{self.fluid_ref}.csv") as stream:
            data = np.genfromtxt(stream, delimiter=",", skip_header=1, filling_values=np.nan)
        self._temperature = data[:, 0]
        self._pressure_ref = float(data[0, 1])
        self._cp = data[:, 2]
        self._dyn_visc = data[:, 4]
        self._therm_cond = data[:, 5]
        self._density = data[:, 7]

    def density(self, temperature: float, pressure: float = 101325.0) -> float:
        """Density [kg/m^3] with ideal gas pressure correction."""
        rho_ref = float(np.interp(temperature, self._temperature, self._density))
        t_ref_idx = int(np.argmin(np.abs(self._temperature - temperature)))
        t_ref = float(self._temperature[t_ref_idx])
        return rho_ref * (pressure / self._pressure_ref) * (t_ref / temperature)

    def dynamic_viscosity(self, temperature: float) -> float:
        """Dynamic viscosity [Pa s]."""
        return float(np.interp(temperature, self._temperature, self._dyn_visc))

    def thermal_conductivity(self, temperature: float) -> float:
        """Thermal conductivity [W/(m K)]."""
        return float(np.interp(temperature, self._temperature, self._therm_cond))

    def specific_heat_cp(self, temperature: float) -> float:
        """Specific heat at constant pressure [J/(kg K)]."""
        return float(np.interp(temperature, self._temperature, self._cp))

    def kinematic_viscosity(self, temperature: float, pressure: float = 101325.0) -> float:
        """Kinematic viscosity [m^2/s] = dynamic_viscosity / density."""
        return self.dynamic_viscosity(temperature) / self.density(temperature, pressure)
