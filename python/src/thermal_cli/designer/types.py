"""Input/output data types for ThermalModelSemi.

Ported from ThermalModelSemiInput.m and ThermalModelSemiOutput.m.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LayerDef:
    """A single layer definition: thickness [m] and conductivity [W/(m K)]."""

    thickness: float
    conductivity: float


@dataclass
class SemiInput:
    """Input specification for the semiconductor-on-PCB thermal model.

    All units SI (meters, Kelvin, Watts).
    """

    # --- Junction ---
    p_loss_junction: float = 0.0  # [W]
    temp_junction_max: float = 448.15  # [K] (175°C default)

    # --- Bottom path ---
    include_bottom: bool = True
    r_th_jc_bottom: float = 0.0  # [K/W] junction-to-case (bottom)
    area_contact: float = 0.0  # [m²] semiconductor contact area
    th_ins_contact_pad_pcb: float = 0.0  # [K m²/W] thermal insulance (gap pad)
    pcb_layer_stack: list[LayerDef] = field(default_factory=list)
    area_single_via: float = 0.0  # [m²] cross-section of one via
    k_via: float = 385.0  # [W/(m K)] via material conductivity (copper default)
    pcb_num_via: int = 0
    pcb_via_spacing: float = 0.0  # [m]
    th_ins_contact_pcb_sink: float = 0.0  # [K m²/W] PCB-to-sink insulance
    sink_layer_stack: list[LayerDef] = field(default_factory=list)
    area_diss_bottom: float = 0.0  # [m²] bottom dissipation area
    h_fluid_bottom: float = 0.0  # [W/(m² K)] convection coefficient
    temp_fluid_bottom: float = 300.0  # [K]

    # --- Top path ---
    include_top: bool = False
    r_th_jc_top: float = 0.0  # [K/W] junction-to-case (top)
    area_case_top: float = 0.0  # [m²]
    area_diss_top: float = 0.0  # [m²]
    h_fluid_top: float = 0.0  # [W/(m² K)]
    temp_fluid_top: float = 300.0  # [K]


@dataclass
class SemiOutput:
    """Output from the semiconductor-on-PCB thermal model."""

    path_case: int = 0
    r_th_junction_fluid_bottom: float = 0.0  # [K/W]
    r_th_case_top_ambient: float = 0.0  # [K/W]
    t_junction: float = 0.0  # [K]
    pcb_num_via: int = 0
    p_loss_max: float = 0.0  # [W]
