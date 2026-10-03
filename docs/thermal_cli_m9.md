# M9 transient thermal networks

The transient module models a passive grounded-capacitance network as

\[
C\,\dot{\theta}+G\theta=P(t),
\]

where each node has a positive grounded heat capacity, resistor connections form
the conductance matrix, and the waveform supplies an independent nonnegative
power input to every node. Waveform samples define a piecewise-linear power
input on an explicit time grid. The linear RC state is propagated exactly on
each segment with a matrix exponential; adding samples along the same linear
waveform does not change the result apart from floating-point roundoff.

The generic Cauer helper accepts R/C arrays in reference-to-junction order.
The INTELEC chip-8 fixture maps the published junction-to-heatsink order into
that convention: source R values 0.196, 0.633, 0.297 K/W and C values 22.3,
21.5, 253 mJ/K become reference-to-junction arrays 0.297, 0.633, 0.196 K/W
and 253, 21.5, 22.3 mJ/K. The output node is the junction. The fixture's
reference temperature is the local substrate/base boundary from Fig. 15(b);
it is not necessarily room ambient. The network's R sum is 1.126 K/W.

The onsemi B01 network preserves the grounded Table 1 graph, independent MOS
and controller source nodes, and the Table 2 fastest fitted pulse limit.
The transient-sim command reads an explicit network and waveform from YAML and
emits temperatures at the requested times. Periodic mode repeats the waveform
until the start-of-cycle state meets absolute/relative convergence tolerances
or the cycle limit is reached.

Source fixtures: [onsemi AND8215/D](https://www.onsemi.com/download/application-notes/pdf/and8215-d.pdf)
Tables 1-2 and [Drofenik et al., INTELEC 2003](https://www.ams-publications.ee.ethz.ch/uploads/tx_ethpublications/drofenik_INTELEC03.pdf)
Table 3 and Figs. 10, 15(b).

## Evidence limits

B01's reported self and mutual steady coefficients are checked against the
published values. B02's chip-8 R/C ordering, junction step response, and DC
resistance are checked. Digitized B01/B02 transient curve comparisons remain
pending; the solver does not claim source-curve parity. Thermal resistance
offsets from the package/module approximation are not treated as numerical
integration error.
