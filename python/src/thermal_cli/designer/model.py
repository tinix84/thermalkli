"""Semiconductor-on-PCB thermal model with 5 heat-path cases.

Ported from ``mfiles/Thermal/Designer/ThermalModelSemi.m``.
Builds a thermal resistance network from junction through PCB/vias/spreader to fluid.
"""

from __future__ import annotations

from thermal_cli.designer.pcb import ThermalPcb
from thermal_cli.designer.types import SemiInput, SemiOutput
from thermal_cli.layers import ThermalLayer, ThermalLayerStack


class ThermalModelSemi:
    """Builds and evaluates a thermal resistance network for semiconductor-on-PCB.

    The 5 heat-path cases:
      1. Bottom path with vias
      2. Bottom path without vias
      3. Bottom + top paths with vias
      4. Bottom + top paths without vias
      5. Top path only
    """

    def __init__(self, inp: SemiInput) -> None:
        self.inp = inp
        self.output = SemiOutput()

    def solve(self) -> SemiOutput:
        """Determine the heat-path case and compute junction temperature."""
        inp = self.inp
        case = self._determine_case()
        self.output.path_case = case

        if case in (1, 2):
            r_th_bot = self._bottom_resistance(use_vias=(case == 1))
            self.output.r_th_junction_fluid_bottom = r_th_bot
            self.output.t_junction = inp.temp_fluid_bottom + r_th_bot * inp.p_loss_junction

        elif case in (3, 4):
            r_th_bot = self._bottom_resistance(use_vias=(case == 3))
            r_th_top = self._top_resistance()
            # Parallel combination: P splits proportionally
            if r_th_bot > 0 and r_th_top > 0:
                r_th_parallel = 1.0 / (1.0 / r_th_bot + 1.0 / r_th_top)
            elif r_th_bot > 0:
                r_th_parallel = r_th_bot
            else:
                r_th_parallel = r_th_top
            self.output.r_th_junction_fluid_bottom = r_th_bot
            self.output.r_th_case_top_ambient = r_th_top
            # Use the lower fluid temperature for junction calculation
            t_fluid_ref = min(inp.temp_fluid_bottom, inp.temp_fluid_top)
            self.output.t_junction = t_fluid_ref + r_th_parallel * inp.p_loss_junction

        elif case == 5:
            r_th_top = self._top_resistance()
            self.output.r_th_case_top_ambient = r_th_top
            self.output.t_junction = inp.temp_fluid_top + r_th_top * inp.p_loss_junction

        # Compute max power at junction temp limit
        if self.output.t_junction > 0 and inp.p_loss_junction > 0:
            r_th_eff = (self.output.t_junction - inp.temp_fluid_bottom) / inp.p_loss_junction
            if r_th_eff > 0:
                self.output.p_loss_max = (inp.temp_junction_max - inp.temp_fluid_bottom) / r_th_eff

        self.output.pcb_num_via = inp.pcb_num_via
        return self.output

    def _determine_case(self) -> int:
        inp = self.inp
        has_bottom = inp.include_bottom and inp.h_fluid_bottom > 0
        has_top = inp.include_top and inp.h_fluid_top > 0
        has_vias = inp.pcb_num_via > 0

        if has_bottom and has_top and has_vias:
            return 3
        if has_bottom and has_top and not has_vias:
            return 4
        if has_bottom and has_vias:
            return 1
        if has_bottom:
            return 2
        return 5

    def _bottom_resistance(self, *, use_vias: bool) -> float:
        """Total thermal resistance from junction to bottom fluid."""
        inp = self.inp
        r_total = inp.r_th_jc_bottom

        # Contact pad insulance → resistance
        if inp.area_contact > 0 and inp.th_ins_contact_pad_pcb > 0:
            r_total += inp.th_ins_contact_pad_pcb / inp.area_contact

        # PCB layer stack (with or without vias)
        if inp.pcb_layer_stack:
            pcb = ThermalPcb(
                layer_stack=inp.pcb_layer_stack,
                area_contact=inp.area_contact,
                num_via=inp.pcb_num_via if use_vias else 0,
                area_single_via=inp.area_single_via,
                k_via=inp.k_via,
            )
            pcb_stack = pcb.to_thermal_layer_stack()
            a_in = inp.area_contact
            a_out = inp.area_diss_bottom if inp.area_diss_bottom > 0 else inp.area_contact
            h_eff = inp.h_fluid_bottom
            r_pcb, _, _ = pcb_stack.resistance(a_in=a_in, a_out=a_out, h_eff=h_eff)
            r_total += r_pcb

        # PCB-to-sink insulance
        if inp.area_diss_bottom > 0 and inp.th_ins_contact_pcb_sink > 0:
            r_total += inp.th_ins_contact_pcb_sink / inp.area_diss_bottom

        # Sink layer stack
        if inp.sink_layer_stack:
            sink_stack = ThermalLayerStack()
            for ly_def in inp.sink_layer_stack:
                sink_stack.add_layer(ThermalLayer(thick=ly_def.thickness, k_op=ly_def.conductivity))
            a_in = inp.area_diss_bottom if inp.area_diss_bottom > 0 else inp.area_contact
            r_sink, _, _ = sink_stack.resistance(a_in=a_in)
            r_total += r_sink

        # Convection
        if inp.h_fluid_bottom > 0 and inp.area_diss_bottom > 0:
            r_total += 1.0 / (inp.h_fluid_bottom * inp.area_diss_bottom)

        return r_total

    def _top_resistance(self) -> float:
        """Total thermal resistance from junction to top fluid."""
        inp = self.inp
        r_total = inp.r_th_jc_top

        # Convection at top
        if inp.h_fluid_top > 0 and inp.area_diss_top > 0:
            r_total += 1.0 / (inp.h_fluid_top * inp.area_diss_top)

        return r_total
