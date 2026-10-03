"""Temperature-dependent liquid properties loaded from package data."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from thermal_cli.database import open_database_csv


@dataclass
class LiquidProperty:
    """Linearly interpolated liquid data with explicit validity bounds.

    Density is not pressure-corrected (incompressible assumption). Values outside
    the tabulated temperature range are rejected rather than silently clamped.
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
        with open_database_csv(f"fluid_{self.fluid_ref}.csv") as stream:
            data = np.genfromtxt(stream, delimiter=",", skip_header=1, filling_values=np.nan)
        if data.ndim != 2 or data.shape[1] < 8 or data.shape[0] < 2:
            raise ValueError(
                f"fluid table {self.fluid_ref!r} must contain at least two complete rows"
            )
        self._temperature = data[:, 0]
        self._cp = data[:, 2]
        self._dyn_visc = data[:, 3]
        self._therm_cond = data[:, 4]
        self._density = data[:, 5]
        for name, values in (
            ("temperature", self._temperature),
            ("dynamic viscosity", self._dyn_visc),
            ("density", self._density),
        ):
            if not np.all(np.isfinite(values)):
                raise ValueError(f"fluid table {self.fluid_ref!r} has non-finite {name}")
        if np.any(np.diff(self._temperature) <= 0.0):
            raise ValueError(f"fluid table {self.fluid_ref!r} temperatures must increase")
        for name, values in (
            ("specific heat cp", self._cp),
            ("thermal conductivity", self._therm_cond),
        ):
            finite = np.isfinite(values)
            if not np.any(finite):
                continue
            if not np.all(finite):
                raise ValueError(f"fluid table {self.fluid_ref!r} has incomplete {name} data")
            if np.any(values <= 0.0):
                raise ValueError(f"fluid table {self.fluid_ref!r} has non-positive {name}")
        for name, values in (
            ("dynamic viscosity", self._dyn_visc),
            ("density", self._density),
        ):
            if np.any(values <= 0.0):
                raise ValueError(f"fluid table {self.fluid_ref!r} has non-positive {name}")
        self.freezing_pt = float(data[0, 6]) if not np.isnan(data[0, 6]) else float("nan")
        self.boiling_pt = float(data[0, 7]) if not np.isnan(data[0, 7]) else float("nan")

    @property
    def temperature_range_k(self) -> tuple[float, float]:
        return float(self._temperature[0]), float(self._temperature[-1])

    def _interpolate(self, temperature: float, values: np.ndarray, name: str) -> float:
        temp = float(temperature)
        if not math.isfinite(temp):
            raise ValueError("temperature must be finite")
        if not np.any(np.isfinite(values)):
            raise ValueError(f"fluid table {self.fluid_ref!r} does not provide {name}")
        lo, hi = self.temperature_range_k
        if temp < lo or temp > hi:
            raise ValueError(
                f"temperature {temp:g} K is outside {self.fluid_ref} table range [{lo:g}, {hi:g}] K"
            )
        return float(np.interp(temp, self._temperature, values))

    def density(self, temperature: float) -> float:
        """Density [kg/m^3], without pressure correction."""
        return self._interpolate(temperature, self._density, "density")

    def dynamic_viscosity(self, temperature: float) -> float:
        """Dynamic viscosity [Pa s]."""
        return self._interpolate(temperature, self._dyn_visc, "dynamic viscosity")

    def thermal_conductivity(self, temperature: float) -> float:
        """Thermal conductivity [W/(m K)]."""
        return self._interpolate(temperature, self._therm_cond, "thermal conductivity")

    def specific_heat_cp(self, temperature: float) -> float:
        """Specific heat at constant pressure [J/(kg K)]."""
        return self._interpolate(temperature, self._cp, "specific heat cp")

    def kinematic_viscosity(self, temperature: float) -> float:
        """Kinematic viscosity [m^2/s] = dynamic_viscosity / density."""
        return self.dynamic_viscosity(temperature) / self.density(temperature)
