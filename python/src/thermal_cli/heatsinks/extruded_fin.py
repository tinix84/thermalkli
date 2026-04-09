"""Extruded-fin heatsink with channel flow model.

Ported from ``mfiles/Thermal/Model/extrudedFinModel.m``.
Implements channel geometry, Reynolds number, Nusselt correlations
(laminar entry-length + Gnielinski turbulent), and thermal resistance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from thermal_cli.fluids.registry import FluidProperty
from thermal_cli.formula.fin import fin_efficiency


@dataclass
class ExtrudedFin:
    """Extruded-fin heatsink with rectangular channels.

    Parameters
    ----------
    num_channel : int
        Number of parallel channels.
    thick_heatsink : float
        Total heatsink depth (fin direction) [m].
    thick_wall : float
        Wall/fin thickness between channels [m].
    width_channel : float
        Channel width [m].
    k_sink : float
        Thermal conductivity of sink material [W/(m K)].
    rho_sink : float
        Density of sink material [kg/m^3].
    """

    num_channel: int
    thick_heatsink: float
    thick_wall: float
    width_channel: float
    k_sink: float
    rho_sink: float = 2698.9
    heatsink_ref: str = ""

    # Computed geometry (set in __post_init__)
    height: float = field(init=False, repr=False)
    depth_channel: float = field(init=False, repr=False)
    d_hydro: float = field(init=False, repr=False)
    cross_area_fluid: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.height = self.num_channel * (self.thick_wall + self.width_channel) + self.thick_wall
        self.depth_channel = self.thick_heatsink - 2 * self.thick_wall
        w = self.width_channel
        h = self.depth_channel
        self.d_hydro = 2 * w * h / (w + h)
        self.cross_area_fluid = self.num_channel * w * h

    def reynolds(self, fluid: FluidProperty, flowrate: float) -> float:
        """Reynolds number for channel flow.

        Parameters
        ----------
        fluid : FluidProperty
            Fluid with kinematic_viscosity method.
        flowrate : float
            Volumetric flow rate [m^3/s].

        Returns
        -------
        float
            Reynolds number (dimensionless).
        """
        v = flowrate / self.cross_area_fluid
        t_mean = 300.0  # default estimation; refine in iterative solve
        nu = fluid.kinematic_viscosity(t_mean)  # type: ignore[call-arg]
        return v * self.d_hydro / nu

    def nusselt(
        self,
        re: float,
        pr: float,
        l_heated: float,
    ) -> float:
        """Nusselt number for rectangular channel flow.

        Laminar (Re <= 2300): entry-length corrected.
        Turbulent (Re > 2300): Gnielinski correlation.

        Parameters
        ----------
        re : float
            Reynolds number.
        pr : float
            Prandtl number.
        l_heated : float
            Heated length [m].

        Returns
        -------
        float
            Local Nusselt number.
        """
        if re <= 2300:
            return self._nusselt_laminar(re, pr, l_heated)
        return self._nusselt_gnielinski(re, pr, l_heated)

    def _nusselt_laminar(self, re: float, pr: float, l_heated: float) -> float:
        """Laminar Nusselt with entry-length correction.

        Fully-developed Nu depends on aspect ratio; for a square channel Nu_fd ≈ 3.61.
        Entry-length effect: Nu_entry ~ (Re Pr dH/L)^(1/3).
        """
        # Aspect ratio of channel
        aspect = self.width_channel / self.depth_channel
        # Fully-developed Nu for rectangular channel (approximate table lookup)
        nu_fd = _nu_fully_developed_rect(aspect)

        # Entry length correction (Sidle et al.)
        gz = re * pr * self.d_hydro / l_heated if l_heated > 0 else 0.0
        if gz > 0:
            nu_entry = 1.302 * gz ** (1.0 / 3.0)
            # Combined (cube-root blend)
            nu = (nu_fd**3 + 1.0 + (max(nu_entry - 1.0, 0.0)) ** 3) ** (1.0 / 3.0)
        else:
            nu = nu_fd

        return max(nu, nu_fd)

    def _nusselt_gnielinski(self, re: float, pr: float, l_heated: float) -> float:
        """Gnielinski turbulent Nusselt correlation.

        Nu = (f/8)(Re-1000)Pr / [1 + 12.7 sqrt(f/8)(Pr^(2/3)-1)]
             * [1 + 1/3 (dH/L)^(2/3)]
        """
        f = (0.79 * math.log(re) - 1.64) ** (-2)
        f8 = f / 8.0
        nu = f8 * (re - 1000.0) * pr / (1.0 + 12.7 * math.sqrt(f8) * (pr ** (2.0 / 3.0) - 1.0))
        # Entry-length correction
        if l_heated > 0:
            nu *= 1.0 + (1.0 / 3.0) * (self.d_hydro / l_heated) ** (2.0 / 3.0)
        return nu

    def heat_transfer_coefficient(
        self,
        fluid: FluidProperty,
        flowrate: float,
        l_heated: float,
        pr: float = 0.71,
    ) -> float:
        """Compute convective heat transfer coefficient [W/(m^2 K)].

        Parameters
        ----------
        fluid : FluidProperty
            Cooling fluid.
        flowrate : float
            Volumetric flow rate [m^3/s].
        l_heated : float
            Heated length [m].
        pr : float
            Prandtl number (default: 0.71 for air).

        Returns
        -------
        float
            Heat transfer coefficient h [W/(m^2 K)].
        """
        re = self.reynolds(fluid, flowrate)
        nu = self.nusselt(re, pr, l_heated)
        t_mean = 300.0  # default estimation
        k_fluid = fluid.thermal_conductivity(t_mean)
        return nu * k_fluid / self.d_hydro

    def thermal_resistance(
        self,
        fluid: FluidProperty,
        flowrate: float,
        l_heated: float,
        a_hot: float,
        pr: float = 0.71,
        num_heated_sides: int = 1,
    ) -> dict[str, float]:
        """Compute thermal resistance decomposition.

        Returns
        -------
        dict
            Keys: 'r_th_total', 'r_th_conv', 'r_th_fluid', 'h_eff', 're', 'nu'.
        """
        re = self.reynolds(fluid, flowrate)
        nu = self.nusselt(re, pr, l_heated)
        t_mean = 300.0
        k_fluid = fluid.thermal_conductivity(t_mean)
        h = nu * k_fluid / self.d_hydro

        # Fin efficiency
        fin_depth = self.depth_channel
        fin_thick = self.thick_wall
        a_fin_per_channel = 2 * fin_depth * l_heated  # both sides of one fin
        ac_fin = fin_thick * l_heated
        eta = fin_efficiency(L=fin_depth, h=h, A=a_fin_per_channel, k=self.k_sink, Ac=ac_fin)

        # Base and fin areas per channel
        a_base = self.width_channel * l_heated
        a_fin = a_fin_per_channel

        # Effective area per channel
        a_eff = a_base + eta * a_fin
        # Total effective area (all channels)
        a_eff_total = self.num_channel * a_eff

        r_th_conv = 1.0 / (h * a_eff_total) if a_eff_total > 0 else float("inf")

        # Fluid temperature rise
        rho_fluid = fluid.density(t_mean) if hasattr(fluid, "density") else 1.18  # type: ignore[call-arg]
        cp_fluid = fluid.specific_heat_cp(t_mean)
        r_th_fluid = 1.0 / (rho_fluid * cp_fluid * flowrate) if flowrate > 0 else float("inf")

        r_th_total = r_th_conv + r_th_fluid

        return {
            "r_th_total": r_th_total,
            "r_th_conv": r_th_conv,
            "r_th_fluid": r_th_fluid,
            "h_eff": h,
            "re": re,
            "nu": nu,
            "eta_fin": eta,
        }


def _nu_fully_developed_rect(aspect: float) -> float:
    """Fully-developed laminar Nusselt for rectangular channel (uniform heat flux).

    Interpolation from Incropera Table 8.1 (aspect ratio → Nu_fd).
    """
    # Table: aspect_ratio → Nu (uniform heat flux, UHF)
    table = [
        (0.0, 8.23),  # parallel plates (infinite aspect)
        (0.25, 5.33),
        (0.5, 4.56),
        (1.0, 3.61),
        (2.0, 4.56),
        (4.0, 5.33),
    ]
    # Normalize aspect to <= 1 (symmetric)
    if aspect > 1.0:
        aspect = 1.0 / aspect

    # Linear interpolation
    for i in range(len(table) - 1):
        a0, n0 = table[i]
        a1, n1 = table[i + 1]
        if a0 <= aspect <= a1:
            t = (aspect - a0) / (a1 - a0) if a1 != a0 else 0.0
            return n0 + t * (n1 - n0)

    # Fallback: square channel
    return 3.61
