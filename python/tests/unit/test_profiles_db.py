"""Tests for thermal_cli.heatsinks.profiles_db — profiles, materials, fans lookup.

TDD: written before implementation.
"""

from __future__ import annotations

import pytest
import numpy as np

from thermal_cli.heatsinks.profiles_db import (
    lookup_hs_profile,
    lookup_hs_material,
    lookup_fan,
    HsProfile,
    HsMaterial,
    FanCurve,
)


# ---------------------------------------------------------------------------
# HsProfile
# ---------------------------------------------------------------------------


def test_lookup_hs_profile_i117() -> None:
    """I117 profile: tb=15, hf=102, tf=1.7, bch=4.3 (all mm)."""
    p = lookup_hs_profile("I117")
    assert isinstance(p, HsProfile)
    assert p.name == "I117"
    assert p.tb_mm == pytest.approx(15.0)
    assert p.hf_mm == pytest.approx(102.0)
    assert p.tf_mm == pytest.approx(1.7)
    assert p.bch_mm == pytest.approx(4.3)


def test_lookup_hs_profile_pada_sf() -> None:
    """'Pada SF' has a space in the name — check quoting round-trips."""
    p = lookup_hs_profile("Pada SF")
    assert p.tb_mm == pytest.approx(15.0)
    assert p.hf_mm == pytest.approx(100.0)
    assert p.tf_mm == pytest.approx(2.0)
    assert p.bch_mm == pytest.approx(3.0)


def test_lookup_hs_profile_unknown_raises() -> None:
    with pytest.raises(ValueError, match="not found"):
        lookup_hs_profile("DOES_NOT_EXIST")


# ---------------------------------------------------------------------------
# HsMaterial
# ---------------------------------------------------------------------------


def test_lookup_hs_material_all_aluminum() -> None:
    m = lookup_hs_material("all_aluminum")
    assert isinstance(m, HsMaterial)
    assert m.name == "all_aluminum"
    assert m.k_fin == pytest.approx(200.0)
    assert m.k_plate == pytest.approx(200.0)


def test_lookup_hs_material_all_copper() -> None:
    m = lookup_hs_material("all_copper")
    assert m.k_fin == pytest.approx(350.0)
    assert m.k_plate == pytest.approx(350.0)


def test_lookup_hs_material_unknown_raises() -> None:
    with pytest.raises(ValueError, match="not found"):
        lookup_hs_material("DOES_NOT_EXIST")


# ---------------------------------------------------------------------------
# FanCurve
# ---------------------------------------------------------------------------


def test_lookup_fan_ebmw2e200_lengths() -> None:
    """EBMW2E200_axial_AC_50Hz: 9 data points."""
    fc = lookup_fan("EBMW2E200_axial_AC_50Hz")
    assert isinstance(fc, FanCurve)
    assert fc.name == "EBMW2E200_axial_AC_50Hz"
    assert len(fc.qv) == 9
    assert len(fc.hv) == 9


def test_lookup_fan_ebmw2e200_boundary_values() -> None:
    """Qv[0]=0, Hv[-1]=0 for EBMW2E200_axial_AC_50Hz."""
    fc = lookup_fan("EBMW2E200_axial_AC_50Hz")
    assert fc.qv[0] == pytest.approx(0.0)
    assert fc.hv[-1] == pytest.approx(0.0)


def test_lookup_fan_ebmw2e200_qv_values() -> None:
    """Check a few Qv values (m3/s): 150/3600 ≈ 0.041667, 915/3600 ≈ 0.254167."""
    fc = lookup_fan("EBMW2E200_axial_AC_50Hz")
    assert fc.qv[1] == pytest.approx(150 / 3600, rel=1e-4)
    assert fc.qv[-1] == pytest.approx(915 / 3600, rel=1e-4)


def test_lookup_fan_returns_numpy_arrays() -> None:
    fc = lookup_fan("EBMW2E200_axial_AC_50Hz")
    assert isinstance(fc.qv, np.ndarray)
    assert isinstance(fc.hv, np.ndarray)


def test_lookup_fan_jf0825_fan13() -> None:
    """Fan 13 was stored in m3/h in Octave; CSV must have m3/s."""
    fc = lookup_fan("JF0825-1H-02")
    assert len(fc.qv) == 25
    # qv[0] = 0 / 3600 = 0
    assert fc.qv[0] == pytest.approx(0.0)
    # last Qv: 64.9622 / 3600 ≈ 0.018045
    assert fc.qv[-1] == pytest.approx(64.9622 / 3600, rel=1e-4)
    # hv[-1] = 0.224 (not exactly 0 for this fan)
    assert fc.hv[-1] == pytest.approx(0.224)


def test_lookup_fan_unknown_raises() -> None:
    with pytest.raises(ValueError, match="not found"):
        lookup_fan("DOES_NOT_EXIST")
