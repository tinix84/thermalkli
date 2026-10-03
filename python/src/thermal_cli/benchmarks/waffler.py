"""Waffler §4.4.2 B03 periodic solid-conduction fixture.

Geometry and flux are transcribed from Fig. 4.46 (printed p. 271, local PDF
p. 293). The 10 mm extrusion depth is the channel length used around eq. 4.154.
The 363.15 K fixed channel-wall temperature is an explicit reference boundary
chosen from the 90 °C property table; the source figure reports temperature
rise, so this absolute offset does not change the conduction rise.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class WafflerB03Fixture:
    """Single channel-pitch metal section with the source's stated loading."""

    channel_pitch_m: float = 0.006
    plate_height_m: float = 0.004
    channel_diameter_m: float = 0.002
    extrusion_depth_m: float = 0.010
    top_heat_flux_W_m2: float = 40_000.0
    aluminum_conductivity_W_m_K: float = 160.0
    channel_wall_temperature_K: float = 363.15
    top_sample_offset_m: float = 0.0001

    @property
    def channel_center_xy_m(self) -> tuple[float, float]:
        return (self.channel_pitch_m / 2.0, self.plate_height_m / 2.0)

    @property
    def top_sample_points_xy_m(self) -> tuple[tuple[float, float], ...]:
        y = self.plate_height_m - self.top_sample_offset_m
        return ((0.0005, y), (self.channel_pitch_m / 2.0, y), (self.channel_pitch_m - 0.0005, y))

    @property
    def applied_power_W(self) -> float:
        """Top flux times planar line length times extrusion depth."""
        return self.top_heat_flux_W_m2 * self.channel_pitch_m * self.extrusion_depth_m

    @property
    def effective_metal_path_m(self) -> float:
        """Waffler eq. 4.154 effective path, with ``f_hs=s_t/h_CP``."""
        f_hs = self.channel_pitch_m / self.plate_height_m
        return self.plate_height_m / 4.0 * (
            math.sqrt(f_hs**2 + 1.0)
            + math.log(f_hs + math.sqrt(f_hs**2 + 1.0)) / f_hs
        ) - self.channel_diameter_m / 2.0

    @property
    def analytic_metal_temperature_rise_K(self) -> float:
        """Eq. 4.152/4.154 one-dimensional path estimate; not an FEA result."""
        return (
            self.top_heat_flux_W_m2
            * self.effective_metal_path_m
            / self.aluminum_conductivity_W_m_K
        )


WAFFLER_B03 = WafflerB03Fixture()

__all__ = ["WAFFLER_B03", "WafflerB03Fixture"]