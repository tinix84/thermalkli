"""PCB thermal model with via array conductivity.

Ported from ``mfiles/Thermal/Designer/ThermalPcb.m``.
"""

from __future__ import annotations

from dataclasses import dataclass

from thermal_cli.designer.types import LayerDef
from thermal_cli.layers import ThermalLayer, ThermalLayerStack


@dataclass
class ThermalPcb:
    """PCB model that computes effective through-plane conductivity with vias.

    Vias act as parallel thermal paths through the PCB laminate. The effective
    conductivity is a parallel combination of via paths and bypass (laminate) paths.
    """

    layer_stack: list[LayerDef]
    area_contact: float  # [m²]
    num_via: int = 0
    area_single_via: float = 0.0  # [m²]
    k_via: float = 385.0  # [W/(m K)] copper

    @property
    def total_thickness(self) -> float:
        return sum(ly.thickness for ly in self.layer_stack)

    def to_thermal_layer_stack(self) -> ThermalLayerStack:
        """Build a ThermalLayerStack with effective via-enhanced conductivity.

        Each PCB layer gets its out-of-plane conductivity enhanced by the
        parallel via contribution.
        """
        stack = ThermalLayerStack()
        for layer_def in self.layer_stack:
            k_eff = self._effective_k_op(layer_def)
            stack.add_layer(ThermalLayer(thick=layer_def.thickness, k_op=k_eff, k_ip=k_eff))
        return stack

    def _effective_k_op(self, layer_def: LayerDef) -> float:
        """Effective out-of-plane conductivity with via contribution.

        k_eff = k_laminate * (1 - via_fraction) + k_via * via_fraction

        where via_fraction = (num_via * area_single_via) / area_contact.
        """
        if self.num_via == 0 or self.area_single_via == 0 or self.area_contact == 0:
            return layer_def.conductivity

        via_fraction = min(self.num_via * self.area_single_via / self.area_contact, 1.0)
        return layer_def.conductivity * (1 - via_fraction) + self.k_via * via_fraction
