"""Composite thermal layer stack with spreading optimization.

Ported from ``mfiles/Thermal/Designer/ThermalLayerStack.m``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from thermal_cli.layers.layer import ThermalLayer


@dataclass
class ThermalLayerStack:
    """A stack of :class:`ThermalLayer` objects computed in series.

    When spreading is requested (a_in != a_out), the stack optimizes
    which layer acts as the spreading medium by evaluating each layer
    individually and selecting the configuration with minimum total resistance.
    """

    layers: list[ThermalLayer] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.layers)

    @property
    def thick(self) -> float:
        return sum(ly.thick for ly in self.layers)

    @property
    def k_op(self) -> float:
        """Equivalent out-of-plane conductivity (series model)."""
        if not self.layers:
            return 0.0
        total_thick = self.thick
        r_sum = sum(ly.thick / ly.k_op for ly in self.layers)
        return total_thick / r_sum

    @property
    def k_ip(self) -> float:
        """Weighted-average in-plane conductivity."""
        if not self.layers:
            return 0.0
        total_thick = self.thick
        return sum(ly.thick * (ly.k_ip or ly.k_op) for ly in self.layers) / total_thick

    def add_layer(self, layer: ThermalLayer) -> None:
        self.layers.append(layer)

    def resistance(
        self,
        a_in: float,
        a_out: float | None = None,
        h_eff: float | None = None,
    ) -> tuple[float, float, float]:
        """Compute total stack resistance, optionally with spreading.

        When a_in != a_out, evaluates spreading in each layer individually
        and picks the configuration with the lowest total resistance.

        Parameters
        ----------
        a_in : float
            Heat source area [m^2].
        a_out : float | None
            Heat sink area [m^2]. Defaults to a_in.
        h_eff : float | None
            Effective heat transfer coefficient at bottom [W/(m^2 K)].

        Returns
        -------
        tuple[r_th, r_th_spread, r_th_through]
        """
        if not self.layers:
            return 0.0, 0.0, 0.0

        if a_out is None:
            a_out = a_in

        # Pure series (no spreading)
        if a_in == a_out or h_eff is None:
            r_through = sum(ly.thick / ly.k_op for ly in self.layers) / a_in
            return r_through, 0.0, r_through

        # With spreading: try each layer as spreading medium,
        # remaining layers are pure through-plane at a_out
        best_total = float("inf")
        best_spread = 0.0
        best_through = 0.0

        for i, spread_layer in enumerate(self.layers):
            # Non-spreading layers at full area
            r_other = sum(
                ly.thick / (ly.k_op * a_out) for j, ly in enumerate(self.layers) if j != i
            )
            # Spreading layer
            r_th, r_sp, r_thr = spread_layer.resistance(a_in, a_out, h_eff)
            total = r_other + r_th

            if total < best_total:
                best_total = total
                best_spread = r_sp
                best_through = r_other + r_thr

        return best_total, best_spread, best_through
