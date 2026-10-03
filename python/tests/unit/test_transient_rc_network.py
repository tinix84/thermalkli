"""M9 acceptance coverage for physical RC transient networks."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from thermal_cli.cli.main import app
from thermal_cli.transient.rc_network import (
    NodalRCNetwork,
    PowerWaveform,
    ThermalResistor,
    intelec2003_chip8_cauer,
    onsemi_and8215_b01_network,
)

runner = CliRunner()


def test_b01_steady_self_and_mutual_coefficients_match_onsemi_table() -> None:
    network = onsemi_and8215_b01_network()

    assert network.steady_resistance_k_w("mos", "mos") == pytest.approx(47.0001, abs=1e-4)
    assert network.steady_resistance_k_w("cs", "cs") == pytest.approx(63.5032, abs=1e-4)
    assert network.steady_resistance_k_w("mos", "cs") == pytest.approx(29.7268, abs=1e-4)
    assert network.steady_resistance_k_w("cs", "mos") == pytest.approx(29.7268, abs=1e-4)


def test_b01_independent_nodal_sources_superpose_dynamically() -> None:
    network = onsemi_and8215_b01_network()
    node = {name: index for index, name in enumerate(network.node_names)}
    times = np.array([0.0, 1e-6, 1e-4, 1e-3])
    mos = np.zeros((len(times), len(node)))
    controller = np.zeros_like(mos)
    combined = np.zeros_like(mos)
    mos[:, node["mos"]] = 1.0
    controller[:, node["cs"]] = 1.0
    combined[:, node["mos"]] = 1.0
    combined[:, node["cs"]] = 1.0

    mos_result = network.simulate(PowerWaveform(times, mos))
    controller_result = network.simulate(PowerWaveform(times, controller))
    combined_result = network.simulate(PowerWaveform(times, combined))

    np.testing.assert_allclose(
        combined_result.node_temperatures_k,
        mos_result.node_temperatures_k + controller_result.node_temperatures_k - network.ambient_k,
        atol=1e-11,
    )


def test_b02_fixture_maps_source_ladder_from_junction_to_reference_order() -> None:
    network = intelec2003_chip8_cauer()

    assert network.capacitances_j_k.tolist() == pytest.approx([0.253, 0.0215, 0.0223])
    assert [(link.node_a, link.node_b, link.resistance_k_w) for link in network.resistors] == [
        (None, "node_0", 0.297),
        ("node_0", "node_1", 0.633),
        ("node_1", "node_2", 0.196),
    ]
    assert network.output_nodes == ("node_2",)
    assert network.steady_resistance_k_w("node_2", "node_2") == pytest.approx(1.126)

    times = np.array([0.0, 0.01])
    power = np.zeros((2, 3))
    power[:, -1] = 1.0
    result = network.simulate(PowerWaveform(times, power))
    rise = result.output_temperatures_k[-1, 0] - network.ambient_k
    assert rise == pytest.approx(0.26043605, abs=1e-7)


def test_exact_piecewise_linear_solution_matches_single_node_analytic_step() -> None:
    network = NodalRCNetwork.cauer_ladder((1.0,), (1.0,), ambient_k=293.15)
    times = np.array([0.0, 100.0, 200.0])
    power = np.full((len(times), 1), 10.0)

    result = network.simulate(PowerWaveform(times, power))
    expected = network.ambient_k + 10.0 * (1.0 - np.exp(-times))

    np.testing.assert_allclose(result.output_temperatures_k[:, 0], expected, atol=1e-12)
    assert np.all(np.diff(result.output_temperatures_k[:, 0]) >= 0.0)


def test_refining_samples_of_same_linear_power_waveform_preserves_solution() -> None:
    network = NodalRCNetwork.cauer_ladder((2.0,), (3.0,), ambient_k=300.0)
    coarse_times = np.array([0.0, 1.0, 3.0])
    coarse_power = np.array([[0.0], [4.0], [4.0]])
    fine_times = np.array([0.0, 0.5, 1.0, 2.0, 3.0])
    fine_power = np.array([[0.0], [2.0], [4.0], [4.0], [4.0]])

    coarse = network.simulate(PowerWaveform(coarse_times, coarse_power))
    fine = network.simulate(PowerWaveform(fine_times, fine_power))

    np.testing.assert_allclose(
        coarse.output_temperatures_k[:, 0],
        fine.output_temperatures_k[[0, 2, 4], 0],
        atol=1e-12,
    )


def test_initial_temperature_and_fitted_short_pulse_validation() -> None:
    network = NodalRCNetwork.cauer_ladder(
        (1.0,),
        (1.0,),
        ambient_k=300.0,
        minimum_supported_pulse_s=1.0,
        fit_reference="test fixture",
    )
    decay = network.simulate(
        PowerWaveform(np.array([0.0, 10.0]), np.zeros((2, 1))),
        initial_temperatures_k=[310.0],
    )
    assert decay.output_temperatures_k[0, 0] == 310.0
    assert decay.output_temperatures_k[-1, 0] == pytest.approx(300.0 + 10.0 * np.exp(-10.0))

    short = PowerWaveform(np.array([0.0, 0.1, 0.2]), np.array([[0.0], [1.0], [0.0]]))
    with pytest.raises(ValueError, match="shorter than"):
        network.simulate(short)


def test_periodic_state_converges_and_reports_exhausted_iteration_limit() -> None:
    network = NodalRCNetwork.cauer_ladder((1.0,), (1.0,), ambient_k=300.0)
    waveform = PowerWaveform(
        np.array([0.0, 0.5, 1.0, 1.5, 2.0]),
        np.array([[0.0], [1.0], [1.0], [0.0], [0.0]]),
    )

    converged = network.periodic_steady_state(waveform, max_cycles=100)
    one_cycle = network.periodic_steady_state(
        waveform,
        absolute_tolerance_k=1e-12,
        relative_tolerance=0.0,
        max_cycles=1,
    )

    assert converged.converged
    assert converged.cycles > 1
    assert not one_cycle.converged
    assert one_cycle.cycles == 1


def test_network_is_immutable_so_cached_conductance_stays_valid() -> None:
    network = NodalRCNetwork.cauer_ladder((1.0,), (1.0,))

    with pytest.raises(FrozenInstanceError):
        network.resistors = (ThermalResistor(None, "node_0", 10.0),)


def test_transient_cli_is_registered_and_runs_chip8_example() -> None:
    config = Path(__file__).resolve().parents[3] / "examples" / "transient_chip8.yaml"
    result = runner.invoke(app, ["transient-sim", "--config", str(config)])

    assert result.exit_code == 0, result.output
    assert "time_s\tnode_2" in result.output
    assert "1\t294.52785" in result.output


def test_transient_cli_rejects_fractional_periodic_cycle_limit(tmp_path) -> None:
    config = tmp_path / "fractional_cycles.yaml"
    config.write_text(
        "network:\n"
        "  kind: cauer_ladder\n"
        "  resistances_k_w: [1.0]\n"
        "  capacitances_j_k: [1.0]\n"
        "waveform:\n"
        "  times_s: [0.0, 1.0, 2.0]\n"
        "  powers_w: [[0.0], [1.0], [0.0]]\n"
        "periodic: true\n"
        "max_cycles: 1.5\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["transient-sim", "--config", str(config)])

    assert result.exit_code == 2
    assert "max_cycles must be a positive integer" in result.output
