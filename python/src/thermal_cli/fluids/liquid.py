"""Liquid property model with temperature-dependent interpolation.

Ported from ``mfiles/Thermal/Model/LiquidProperty.m``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from thermal_cli.fluids.gas import _find_db_path


@dataclass
class LiquidProperty:
    """Temperature-dependent liquid properties loaded from CSV.

    Uses linear interpolation on tabulated data. Density is NOT
    pressure-corrected (incompressible assumption for liquids).
    """

    fluid_ref: str
    freezing_pt: float = field(repr=False, init=False)
    boiling_pt: float = field(repr=False, init=False)
    _temperature: np.ndarray = field(repr=False, init=False)
    _cp: np.ndarray = field(repr=False, init=False)
    _dyn_visc: np.ndarray = field(repr=False, init=False)
    _therm_cond: np.ndarray = field(repr=False, init=False)
    _density: np.ndarray = field(repr=False, init=False)

    def __post_init__(self) -> None:
        path = _find_db_path(self.fluid_ref)
        data = np.genfromtxt(path, delimiter=",", skip_header=1, filling_values=np.nan)
        self._temperature = data[:, 0]
        self._cp = data[:, 2]
        self._dyn_visc = data[:, 3]
        self._therm_cond = data[:, 4]
        self._density = data[:, 5]
        # Freezing and boiling points from first row (constant properties)
        self.freezing_pt = float(data[0, 6]) if not np.isnan(data[0, 6]) else float("nan")
        self.boiling_pt = float(data[0, 7]) if not np.isnan(data[0, 7]) else float("nan")

    def density(self, temperature: float) -> float:
        """Density [kg/m^3]. No pressure correction for liquids."""
        return float(np.interp(temperature, self._temperature, self._density))

    def dynamic_viscosity(self, temperature: float) -> float:
        """Dynamic viscosity [Pa s]."""
        return float(np.interp(temperature, self._temperature, self._dyn_visc))

    def thermal_conductivity(self, temperature: float) -> float:
        """Thermal conductivity [W/(m K)]."""
        return float(np.interp(temperature, self._temperature, self._therm_cond))

    def specific_heat_cp(self, temperature: float) -> float:
        """Specific heat at constant pressure [J/(kg K)]."""
        return float(np.interp(temperature, self._temperature, self._cp))

    def kinematic_viscosity(self, temperature: float) -> float:
        """Kinematic viscosity [m^2/s] = dynamic_viscosity / density."""
        return self.dynamic_viscosity(temperature) / self.density(temperature)
