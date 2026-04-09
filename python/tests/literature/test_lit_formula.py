"""Literature-validated tests for formula layer.

These tests use independently verified reference values from textbooks
and published tables, NOT from the implementation itself.
They serve as the permanent authoritative regression floor after Octave is retired.
"""

from __future__ import annotations

import pytest

from thermal_cli.formula.fin import fin_efficiency
from thermal_cli.formula.radiation import parallel_planes

# --- Fin efficiency: Incropera 7th ed, Table 3.5 ---
# Setup: L=1, A=1, Ac=1, k=1 → mL = sqrt(h). eta = tanh(mL)/mL.
# tanh/mL values from standard mathematical tables.


@pytest.mark.parametrize(
    ("h", "mL_expected", "eta_expected"),
    [
        (0.25, 0.5, 0.9242),  # tanh(0.5)/0.5 = 0.92424
        (1.0, 1.0, 0.7616),  # tanh(1.0)/1.0 = 0.76159
        (4.0, 2.0, 0.4820),  # tanh(2.0)/2.0 = 0.48201
        (9.0, 3.0, 0.3317),  # tanh(3.0)/3.0 = 0.33168
    ],
    ids=["mL=0.5", "mL=1.0", "mL=2.0", "mL=3.0"],
)
def test_fin_efficiency_incropera(h: float, mL_expected: float, eta_expected: float) -> None:
    """Verify fin efficiency against Incropera Table 3.5 tabulated values."""
    eta = fin_efficiency(L=1.0, h=h, A=1.0, k=1.0, Ac=1.0)
    assert eta == pytest.approx(eta_expected, abs=1e-3)


def test_fin_efficiency_realistic_aluminum() -> None:
    """Realistic aluminum fin: L=20mm, t=1mm, h=50 W/m^2K, k=200 W/mK.

    Reference: Octave test_formula.m 'fin_efficiency: realistic aluminum fin'.
    mL = sqrt(50*0.04/(200*0.001*0.02))*0.02 = sqrt(500)*0.02 = 0.447.
    eta = tanh(0.447)/0.447 ~ 0.938. Short fin in good conductor → high efficiency.
    """
    L, t, h, k = 0.02, 0.001, 50.0, 200.0
    W = 1.0
    A = 2 * L * W
    Ac = t * W
    eta = fin_efficiency(L=L, h=h, A=A, k=k, Ac=Ac)
    assert eta == pytest.approx(0.938, abs=0.01)


# --- Radiation: Stefan-Boltzmann law ---
# sigma = 5.670367e-8 W/(m^2 K^4) (CODATA 2014)
# Blackbody q = sigma * A * (T1^4 - T2^4) for parallel planes with eps=1


def test_blackbody_radiation_1000K_300K() -> None:
    """Stefan-Boltzmann: Q = sigma * A * (T1^4 - T2^4).

    For T1=1000 K, T2=300 K, A=1 m^2:
    Q = 5.670367e-8 * (1e12 - 8.1e9) = 5.670367e-8 * 9.919e11 = 56244.3 W.

    Reference: direct Stefan-Boltzmann law computation, verified in Incropera.
    """
    q = parallel_planes(T1=1000.0, T2=300.0, A=1.0, eps1=1.0, eps2=1.0)
    assert q == pytest.approx(56244.3, rel=1e-3)
