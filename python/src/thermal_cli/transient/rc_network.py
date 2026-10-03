"""Physical nodal RC and Cauer transient networks.

Temperatures are returned in kelvin; powers are independent nodal heat inputs in watts.
The state equation is C d(theta)/dt + G theta = P, where theta is rise above ambient,
C is diagonal grounded heat capacity, and G is a passive nodal conductance matrix.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import expm


@dataclass(frozen=True)
class ThermalResistor:
    """A resistor between named nodes; node_a=None means ambient reference."""

    node_a: str | None
    node_b: str
    resistance_k_w: float

    def __post_init__(self) -> None:
        if self.node_a == self.node_b:
            raise ValueError("resistor endpoints must differ")
        if not self.node_b:
            raise ValueError("node_b must be named")
        if not math.isfinite(self.resistance_k_w) or self.resistance_k_w <= 0.0:
            raise ValueError("resistance_k_w must be finite and > 0")


@dataclass(frozen=True)
class PowerWaveform:
    """Piecewise-linear independent power values on an explicit time grid."""

    times_s: NDArray[np.float64]
    powers_w: NDArray[np.float64]

    def __post_init__(self) -> None:
        times = np.asarray(self.times_s, dtype=float)
        powers = np.asarray(self.powers_w, dtype=float)
        if times.ndim != 1 or len(times) < 2:
            raise ValueError("waveform times must be a one-dimensional grid with >= 2 samples")
        if powers.ndim != 2 or powers.shape[0] != len(times) or powers.shape[1] < 1:
            raise ValueError("powers must have shape (number of times, number of sources)")
        if not np.all(np.isfinite(times)) or not np.all(np.isfinite(powers)):
            raise ValueError("waveform values must be finite")
        if times[0] < 0.0 or np.any(np.diff(times) <= 0.0):
            raise ValueError("waveform times must start >= 0 and increase strictly")
        if np.any(powers < 0.0):
            raise ValueError("dissipated powers must be nonnegative")
        times, powers = times.copy(), powers.copy()
        times.setflags(write=False)
        powers.setflags(write=False)
        object.__setattr__(self, "times_s", times)
        object.__setattr__(self, "powers_w", powers)

    @property
    def source_count(self) -> int:
        return int(self.powers_w.shape[1])

    @property
    def interval_s(self) -> tuple[float, float]:
        return float(self.times_s[0]), float(self.times_s[-1])

    def shortest_nonzero_pulse_s(self) -> float | None:
        """Return the shortest contiguous nonzero support across independent sources."""
        durations: list[float] = []
        for column in range(self.source_count):
            start: float | None = None
            for index in range(len(self.times_s) - 1):
                t0, t1 = float(self.times_s[index]), float(self.times_s[index + 1])
                p0, p1 = (
                    float(self.powers_w[index, column]),
                    float(self.powers_w[index + 1, column]),
                )
                if start is None and (p0 > 0.0 or p1 > 0.0):
                    start = t0
                if start is not None and p1 == 0.0:
                    durations.append(t1 - start)
                    start = None
            if start is not None:
                durations.append(float(self.times_s[-1]) - start)
        return min(durations) if durations else None


@dataclass(frozen=True)
class TransientResult:
    times_s: np.ndarray
    node_temperatures_k: NDArray[np.float64]
    output_temperatures_k: NDArray[np.float64]
    output_nodes: tuple[str, ...]
    initial_temperatures_k: NDArray[np.float64]
    ambient_k: float
    integration: str = "matrix exponential per linear-power segment"


@dataclass(frozen=True)
class PeriodicResult:
    transient: TransientResult
    converged: bool
    cycles: int
    max_cycle_delta_k: float
    absolute_tolerance_k: float
    relative_tolerance: float


@dataclass(frozen=True, eq=False)
class NodalRCNetwork:
    """Grounded-capacitance network with explicit physical resistor connections.

    ambient_k is the fixed reference temperature of the grounded network. For
    package RC fixtures it can denote the local base/substrate temperature, not
    room ambient.
    """

    node_names: tuple[str, ...]
    capacitances_j_k: NDArray[np.float64]
    resistors: tuple[ThermalResistor, ...]
    output_nodes: tuple[str, ...]
    ambient_k: float = 293.15
    minimum_supported_pulse_s: float | None = None
    fit_reference: str = "user-specified RC network"
    _conductance_w_k: NDArray[np.float64] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        names = tuple(self.node_names)
        if not names or len(set(names)) != len(names) or any(not name for name in names):
            raise ValueError("node_names must be nonempty, unique names")
        caps = np.asarray(self.capacitances_j_k, dtype=float)
        if caps.shape != (len(names),) or not np.all(np.isfinite(caps)) or np.any(caps <= 0.0):
            raise ValueError("each node requires finite positive grounded capacitance")
        if not self.output_nodes or any(name not in names for name in self.output_nodes):
            raise ValueError("output_nodes must name at least one network node")
        if len(set(self.output_nodes)) != len(self.output_nodes):
            raise ValueError("output_nodes must be unique")
        if not math.isfinite(self.ambient_k) or self.ambient_k <= 0.0:
            raise ValueError("ambient_k must be finite and > 0")
        if self.minimum_supported_pulse_s is not None and (
            not math.isfinite(self.minimum_supported_pulse_s)
            or self.minimum_supported_pulse_s <= 0.0
        ):
            raise ValueError("minimum_supported_pulse_s must be finite and > 0")
        if not self.fit_reference.strip():
            raise ValueError("fit_reference must identify the network data")
        index = {name: i for i, name in enumerate(names)}
        conductance: NDArray[np.float64] = np.zeros((len(names), len(names)), dtype=float)
        for resistor in self.resistors:
            if resistor.node_b not in index or (
                resistor.node_a is not None and resistor.node_a not in index
            ):
                raise ValueError("resistor references a node outside node_names")
            i = index[resistor.node_b]
            g = 1.0 / resistor.resistance_k_w
            conductance[i, i] += g
            if resistor.node_a is not None:
                j = index[resistor.node_a]
                conductance[j, j] += g
                conductance[i, j] -= g
                conductance[j, i] -= g
        if np.any(np.diag(conductance) <= 0.0):
            raise ValueError("every node must have a resistive path")
        if np.any(conductance - np.diag(np.diag(conductance)) > 1e-12):
            raise ValueError("conductance off-diagonal entries must be nonpositive")
        try:
            np.linalg.cholesky(conductance)
        except np.linalg.LinAlgError as exc:
            raise ValueError(
                "network must be connected to ambient with positive resistance"
            ) from exc
        caps = caps.copy()
        caps.setflags(write=False)
        conductance.setflags(write=False)
        object.__setattr__(self, "node_names", names)
        object.__setattr__(self, "capacitances_j_k", caps)
        object.__setattr__(self, "resistors", tuple(self.resistors))
        object.__setattr__(self, "output_nodes", tuple(self.output_nodes))
        object.__setattr__(self, "_conductance_w_k", conductance)

    @property
    def conductance_w_k(self) -> NDArray[np.float64]:
        conductance: NDArray[np.float64] = self._conductance_w_k.copy()
        return conductance

    @property
    def shortest_time_constant_s(self) -> float:
        """Smallest modal RC time constant of C d(theta)/dt + G theta = 0."""
        scale = 1.0 / np.sqrt(self.capacitances_j_k)
        symmetric = (scale[:, None] * self._conductance_w_k) * scale[None, :]
        largest_decay_rate = float(np.linalg.eigvalsh(symmetric)[-1])
        return float(1.0 / largest_decay_rate)

    def steady_temperatures_k(self, powers_w: Sequence[float]) -> NDArray[np.float64]:
        """Solve the DC network for one independent power value per node."""
        power = np.asarray(powers_w, dtype=float)
        if power.shape != (len(self.node_names),) or not np.all(np.isfinite(power)):
            raise ValueError("powers_w must contain one finite value per node")
        if np.any(power < 0.0):
            raise ValueError("dissipated powers must be nonnegative")
        rise: NDArray[np.float64] = np.linalg.solve(self._conductance_w_k, power)
        temperatures: NDArray[np.float64] = self.ambient_k + rise
        return temperatures

    def steady_resistance_k_w(self, output_node: str, source_node: str) -> float:
        """Return the source-to-output DC coefficient for unit source power."""
        index = {name: i for i, name in enumerate(self.node_names)}
        if output_node not in index or source_node not in index:
            raise ValueError("unknown source or output node")
        z: NDArray[np.float64] = np.linalg.solve(
            self._conductance_w_k, np.eye(len(index), dtype=float)
        )
        return float(z[index[output_node], index[source_node]])

    def simulate(
        self,
        waveform: PowerWaveform,
        *,
        initial_temperatures_k: Sequence[float] | NDArray[np.float64] | None = None,
    ) -> TransientResult:
        """Integrate all node states on the explicit waveform grid."""
        self._validate_waveform(waveform)
        n = len(self.node_names)
        if initial_temperatures_k is None:
            initial = np.full(n, self.ambient_k)
        else:
            initial = np.asarray(initial_temperatures_k, dtype=float)
            if initial.shape != (n,) or not np.all(np.isfinite(initial)) or np.any(initial <= 0.0):
                raise ValueError(
                    "initial temperatures must be finite positive kelvin, one per node"
                )
            initial = initial.copy()
        transitions = self._piecewise_linear_transitions(waveform)
        return self._simulate_with_transitions(waveform, initial, transitions)

    def _validate_waveform(self, waveform: PowerWaveform) -> None:
        n = len(self.node_names)
        if waveform.source_count != n:
            raise ValueError(f"waveform requires {n} independent nodal power columns")
        shortest_pulse = waveform.shortest_nonzero_pulse_s()
        if (
            self.minimum_supported_pulse_s is not None
            and shortest_pulse is not None
            and shortest_pulse < self.minimum_supported_pulse_s
        ):
            raise ValueError(
                "waveform contains a nonzero pulse shorter than the network's supported minimum "
                f"({self.minimum_supported_pulse_s:g} s)"
            )

    def _piecewise_linear_transitions(
        self, waveform: PowerWaveform
    ) -> tuple[NDArray[np.float64], ...]:
        """Build exact affine state maps for each linearly interpolated power segment."""
        n = len(self.node_names)
        inverse_capacity = 1.0 / self.capacitances_j_k
        dynamics = -inverse_capacity[:, None] * self._conductance_w_k
        transitions: list[NDArray[np.float64]] = []
        for k, dt in enumerate(np.diff(waveform.times_s)):
            start_power = waveform.powers_w[k]
            power_slope = (waveform.powers_w[k + 1] - start_power) / dt
            augmented: NDArray[np.float64] = np.zeros((n + 2, n + 2), dtype=float)
            augmented[:n, :n] = dynamics
            augmented[:n, n] = inverse_capacity * start_power
            augmented[:n, n + 1] = inverse_capacity * power_slope
            augmented[n + 1, n] = 1.0
            transitions.append(expm(augmented * dt))
        return tuple(transitions)

    def _simulate_with_transitions(
        self,
        waveform: PowerWaveform,
        initial: NDArray[np.float64],
        transitions: tuple[NDArray[np.float64], ...],
    ) -> TransientResult:
        n = len(self.node_names)
        theta = initial - self.ambient_k
        temperatures: NDArray[np.float64] = np.empty((len(waveform.times_s), n), dtype=float)
        temperatures[0] = initial
        state: NDArray[np.float64] = np.empty(n + 2, dtype=float)
        state[n] = 1.0
        state[n + 1] = 0.0
        for k, transition in enumerate(transitions):
            state[:n] = theta
            theta = (transition @ state)[:n]
            temperatures[k + 1] = self.ambient_k + theta
        output_index = [self.node_names.index(name) for name in self.output_nodes]
        return TransientResult(
            times_s=waveform.times_s.copy(),
            node_temperatures_k=temperatures,
            output_temperatures_k=temperatures[:, output_index].copy(),
            output_nodes=self.output_nodes,
            initial_temperatures_k=initial,
            ambient_k=self.ambient_k,
        )

    def periodic_steady_state(
        self,
        waveform: PowerWaveform,
        *,
        initial_temperatures_k: Sequence[float] | None = None,
        absolute_tolerance_k: float = 1e-6,
        relative_tolerance: float = 1e-6,
        max_cycles: int = 1000,
    ) -> PeriodicResult:
        """Repeat a periodic waveform until the start-of-cycle state converges."""
        if waveform.times_s[0] != 0.0:
            raise ValueError("periodic waveform must start at t=0")
        if not np.allclose(waveform.powers_w[0], waveform.powers_w[-1], rtol=0.0, atol=1e-12):
            raise ValueError("periodic waveform must have matching start/end power values")
        if not math.isfinite(absolute_tolerance_k) or absolute_tolerance_k <= 0.0:
            raise ValueError("absolute_tolerance_k must be finite and > 0")
        if not math.isfinite(relative_tolerance) or relative_tolerance < 0.0:
            raise ValueError("relative_tolerance must be finite and >= 0")
        if isinstance(max_cycles, bool) or not isinstance(max_cycles, int) or max_cycles < 1:
            raise ValueError("max_cycles must be a positive integer")
        n = len(self.node_names)
        self._validate_waveform(waveform)
        current = (
            np.full(n, self.ambient_k)
            if initial_temperatures_k is None
            else np.asarray(initial_temperatures_k, dtype=float).copy()
        )
        if current.shape != (n,) or not np.all(np.isfinite(current)) or np.any(current <= 0.0):
            raise ValueError("initial temperatures must be finite positive kelvin, one per node")
        last_result: TransientResult | None = None
        delta = math.inf
        converged = False
        cycles = 0
        transitions = self._piecewise_linear_transitions(waveform)
        for _ in range(max_cycles):
            cycles += 1
            last_result = self._simulate_with_transitions(waveform, current, transitions)
            following = last_result.node_temperatures_k[-1]
            delta = float(np.max(np.abs(following - current)))
            scale = max(1.0, float(np.max(np.abs(current))))
            if delta <= absolute_tolerance_k + relative_tolerance * scale:
                converged = True
                break
            current = following.copy()
        assert last_result is not None
        return PeriodicResult(
            last_result, converged, cycles, delta, absolute_tolerance_k, relative_tolerance
        )

    @classmethod
    def cauer_ladder(
        cls,
        resistances_k_w: Sequence[float],
        capacitances_j_k: Sequence[float],
        *,
        ambient_k: float = 293.15,
        minimum_supported_pulse_s: float | None = None,
        fit_reference: str = "user-specified Cauer ladder",
    ) -> NodalRCNetwork:
        """Build a base-to-junction Cauer ladder; each capacitance is grounded."""
        resistance = np.asarray(resistances_k_w, dtype=float)
        capacitance = np.asarray(capacitances_j_k, dtype=float)
        if resistance.ndim != 1 or capacitance.ndim != 1 or len(resistance) != len(capacitance):
            raise ValueError("Cauer R and C arrays must be one-dimensional and the same length")
        if len(resistance) < 1 or not np.all(np.isfinite(resistance)) or np.any(resistance <= 0.0):
            raise ValueError("Cauer resistances must be finite and positive")
        names = tuple(f"node_{i}" for i in range(len(resistance)))
        links = [ThermalResistor(None, names[0], float(resistance[0]))]
        links.extend(
            ThermalResistor(names[i - 1], names[i], float(resistance[i]))
            for i in range(1, len(resistance))
        )
        return cls(
            names,
            capacitance,
            tuple(links),
            (names[-1],),
            ambient_k,
            minimum_supported_pulse_s,
            fit_reference,
        )


def onsemi_and8215_b01_network(*, ambient_k: float = 293.15) -> NodalRCNetwork:
    """Construct the grounded SPICE-compatible R/C graph from onsemi Table 1.

    Junction outputs are MOSFET node "mos" and controller node "cs". The distinct
    dynamic source/load nodes are retained; the two Cauer-like branches are coupled
    through common node "com" and resistor R_R15.
    """
    c_values = {
        "cs": 9.21909e-6,
        "c1": 4.36252e-5,
        "c2": 1.30876e-4,
        "c3": 1.75727e-4,
        "c4": 8.87879e-4,
        "c5": 2.06324e-2,
        "c6": 3.25284e-1,
        "mos": 9.59163e-5,
        "m1": 4.53881e-4,
        "m2": 1.36164e-3,
        "m3": 4.08493e-3,
        "m4": 1.66362e-2,
        "m5": 6.00462e-2,
        "m6": 4.60781e-1,
        "com": 3.03315,
        "u1": 2.51716e1,
    }
    r_values = (
        ("cs", "c1", 3.97030e-2),
        ("c1", "c2", 1.19109e-1),
        ("c2", "c3", 3.57327e-1),
        ("c3", "c4", 2.59622e-1),
        ("c4", "c5", 8.51408),
        ("c5", "c6", 6.55035),
        ("c6", "com", 3.92892e1),
        ("mos", "m1", 3.81609e-3),
        ("m1", "m2", 1.14483e-2),
        ("m2", "m3", 3.43448e-2),
        ("m3", "m4", 1.03035e-1),
        ("m4", "m5", 2.57613e-1),
        ("m5", "m6", 5.90459),
        ("m6", "com", 2.40044e1),
        ("c6", "m6", 5.31662e1),
        ("com", "u1", 1.72692e1),
        (None, "u1", 4.35939),
    )
    names = tuple(c_values)
    resistors = tuple(ThermalResistor(a, b, r) for a, b, r in r_values)
    return NodalRCNetwork(
        names,
        np.array([c_values[name] for name in names]),
        resistors,
        ("mos", "cs"),
        ambient_k=ambient_k,
        minimum_supported_pulse_s=1.0 / 3.34538e6,
        fit_reference="onsemi AND8215/D Rev. 1, Table 1; Table 2 fastest fitted time constant",
    )


def intelec2003_chip8_cauer(*, ambient_k: float = 293.15) -> NodalRCNetwork:
    """INTELEC 2003 chip-8 Cauer ladder, mapped to reference-to-junction order.

    The source table lists R/C elements junction-to-heatsink. The helper's
    convention is reference-to-junction. Here ambient_k is the local package
    base/substrate reference in Fig. 15, not necessarily room ambient.
    """
    return NodalRCNetwork.cauer_ladder(
        (0.297, 0.633, 0.196),
        (0.253, 0.0215, 0.0223),
        ambient_k=ambient_k,
        fit_reference="Drofenik et al., INTELEC 2003, Table 3/Fig. 10, chip 8",
    )
