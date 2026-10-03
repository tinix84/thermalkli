# M8: pump-limited liquid cooling

Run the liquid-cooler API from `thermal_cli.liquid_cooling` or the
`thermal liquid-cooler --config FILE` command. YAML geometry, flow, pressure,
power, volume, and resistance values use SI units; temperature is kelvin.

The pump curve is available pressure over a bounded total-flow domain. It is
not extrapolated. Circular and slot channels use equal parallel branch flow;
each branch reports its flow and pressure losses. The model does not represent
maldistributed manifolds. Slot and circular channels use separate laminar
relations and a continuous laminar-to-turbulent friction transition.

Liquid properties are interpolated inside the fluid table's temperature range.
The energy result is marked `invalid_temperature` if either the inlet or
computed outlet is outside that range. A zero-flow, positive-heat condition is
reported as `invalid_flow`, and the CLI exits unsuccessfully for invalid
thermal states. Fluid tables without heat-capacity data remain usable for
hydraulics and report `invalid_properties` for energy calculations.

For slot channels, the ideal convection resistance is evaluated per branch
and combined in parallel across equal channels. The plate-to-inlet result adds
the total-loop bulk coolant rise. An optional whole-plate inlet/outlet-area
resistance is combined in parallel with the slot path; it can be supplied
directly as `flow_area_rth_k_w` or selected with
`flow_area_calibration: pesc2004_b05`. The latter uses the published rough CFD
fit of 1.0 K/W for slot gaps through 1.2 mm and 0.4 K/W above 1.2 mm. The
PESC port-loss fit is a separate hydraulic correction and applies only when
the original inlet/outlet geometry is unchanged.

The flow-area approximation is from [Drofenik et al., PESC 2004,
Section 2.4.2](https://www.ams-publications.ee.ethz.ch/uploads/tx_ethpublications/drofenik_PESC04.pdf).

The ideal-slot Nusselt calculation is an engineering flat-plate estimate; it
does not claim exact reproduction of PESC 2004 Eq. 7. B05 source parity remains
pending. The B06 measured observation is retained, but its model reproduction
is unresolved because matching geometry and boundary/contact data are absent.

Cold-plate, pump, pipe, and heat-exchanger volumes are separate values. The
complete-loop volume is their sum. Results remain referenced to bulk coolant;
they are not converted to room-air resistance.

Run the illustrative input with:

```sh
thermal liquid-cooler --config examples/liquid_cooler.yaml
```
