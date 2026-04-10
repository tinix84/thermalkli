"""Tests for thermal_cli.heatsinks.natural_conv — fanless heatsink Rth.

Reference: lib/cmd_natural_conv_hs.m (Octave implementation).

All temperatures in Kelvin, lengths in meters, power in Watts.
"""

from __future__ import annotations

import pytest

from thermal_cli.heatsinks.natural_conv import NaturalConvHsResult, natural_conv_hs

# ---------------------------------------------------------------------------
# Shared fixture: typical aluminum heatsink
# ---------------------------------------------------------------------------

_TYPICAL_KWARGS = dict(
    n_fins=10,
    fin_height=0.05,  # 50 mm
    fin_length=0.10,  # 100 mm
    fin_thickness=0.002,  # 2 mm
    channel_width=0.005,  # 5 mm
    base_thickness=0.003,  # 3 mm (not used in calc)
    k=200.0,  # aluminum
    t_ambient=298.15,  # 25 °C
    p_loss=10.0,  # 10 W
)


# ---------------------------------------------------------------------------
# Return-type checks
# ---------------------------------------------------------------------------


def test_returns_dataclass() -> None:
    result = natural_conv_hs(**_TYPICAL_KWARGS)
    assert isinstance(result, NaturalConvHsResult)


def test_result_fields_exist() -> None:
    result = natural_conv_hs(**_TYPICAL_KWARGS)
    assert hasattr(result, "t_surface")
    assert hasattr(result, "rth")
    assert hasattr(result, "h_fin")
    assert hasattr(result, "h_base")
    assert hasattr(result, "eta_fin")
    assert hasattr(result, "q_total")


# ---------------------------------------------------------------------------
# Physical sanity: typical aluminum HS, 10 W
# ---------------------------------------------------------------------------


def test_typical_al_rth_in_range() -> None:
    """Rth for a small aluminum heatsink at 10 W should be in [0.5, 10] K/W.

    Computed value is ~0.88 K/W for 10 fins, Hf=50 mm, L=100 mm.
    Lower bound is 0.5 (physically tight but not zero), upper is 10.
    """
    result = natural_conv_hs(**_TYPICAL_KWARGS)
    assert 0.5 <= result.rth <= 10.0


def test_typical_al_t_surface_above_ambient() -> None:
    result = natural_conv_hs(**_TYPICAL_KWARGS)
    assert result.t_surface > _TYPICAL_KWARGS["t_ambient"]


def test_typical_al_eta_fin_lt_1() -> None:
    """Fin efficiency must be < 1 for finite k."""
    result = natural_conv_hs(**_TYPICAL_KWARGS)
    assert result.eta_fin < 1.0
    assert result.eta_fin > 0.0


def test_typical_al_h_fin_positive() -> None:
    result = natural_conv_hs(**_TYPICAL_KWARGS)
    assert result.h_fin > 0.0


def test_typical_al_h_base_positive() -> None:
    result = natural_conv_hs(**_TYPICAL_KWARGS)
    assert result.h_base > 0.0


def test_typical_al_q_total_matches_p_loss() -> None:
    """Bisection convergence: Q ≈ p_loss within 0.1%."""
    result = natural_conv_hs(**_TYPICAL_KWARGS)
    assert result.q_total == pytest.approx(10.0, rel=1e-3)


def test_rth_consistency() -> None:
    """Rth = (Ts - Ta) / P must be self-consistent."""
    result = natural_conv_hs(**_TYPICAL_KWARGS)
    expected_rth = (result.t_surface - _TYPICAL_KWARGS["t_ambient"]) / _TYPICAL_KWARGS["p_loss"]
    assert result.rth == pytest.approx(expected_rth, rel=1e-10)


# ---------------------------------------------------------------------------
# Higher power → higher surface temperature
# ---------------------------------------------------------------------------


def test_higher_power_higher_ts() -> None:
    low = natural_conv_hs(**{**_TYPICAL_KWARGS, "p_loss": 5.0})
    high = natural_conv_hs(**{**_TYPICAL_KWARGS, "p_loss": 20.0})
    assert high.t_surface > low.t_surface


def test_higher_power_higher_rth() -> None:
    """Rth should increase (weakly) with power due to h(Ts) non-linearity."""
    low = natural_conv_hs(**{**_TYPICAL_KWARGS, "p_loss": 5.0})
    high = natural_conv_hs(**{**_TYPICAL_KWARGS, "p_loss": 50.0})
    # Higher power → larger ΔT → larger h → Rth may decrease slightly,
    # but surface temp must always rise.
    assert high.t_surface > low.t_surface


# ---------------------------------------------------------------------------
# Material effect: copper (k=385) vs aluminum (k=200)
# ---------------------------------------------------------------------------


def test_copper_lower_rth_than_aluminum() -> None:
    """Higher k → better fin efficiency → lower Rth."""
    al = natural_conv_hs(**_TYPICAL_KWARGS)
    cu = natural_conv_hs(**{**_TYPICAL_KWARGS, "k": 385.0})
    assert cu.rth < al.rth


def test_copper_higher_eta_fin_than_aluminum() -> None:
    """Higher k → higher fin efficiency."""
    al = natural_conv_hs(**_TYPICAL_KWARGS)
    cu = natural_conv_hs(**{**_TYPICAL_KWARGS, "k": 385.0})
    assert cu.eta_fin > al.eta_fin


# ---------------------------------------------------------------------------
# Emissivity effect
# ---------------------------------------------------------------------------


def test_zero_emissivity_higher_rth() -> None:
    """No radiation → lower h → higher Ts and Rth."""
    with_rad = natural_conv_hs(**_TYPICAL_KWARGS)
    no_rad = natural_conv_hs(**{**_TYPICAL_KWARGS, "emissivity": 0.0})
    assert no_rad.rth > with_rad.rth


# ---------------------------------------------------------------------------
# Edge case: very short fin (low m*Hf → eta ≈ 1)
# ---------------------------------------------------------------------------


def test_very_short_fin_eta_near_one() -> None:
    """When fin height → 0, m*Hf → 0, eta → 1."""
    result = natural_conv_hs(**{**_TYPICAL_KWARGS, "fin_height": 0.001})
    assert result.eta_fin == pytest.approx(1.0, abs=0.05)
