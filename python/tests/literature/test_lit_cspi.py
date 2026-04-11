"""Literature-validated tests for CSPI formulas.
Reference: Drofenik & Kolar, CIPS 2006.
"""

from __future__ import annotations

import pytest

from thermal_cli.cspi.formulas import cspi_calc, fan_scaling_fit


class TestCspiLiterature:
    def test_eq41_definition(self):
        """CSPI = 1/(Rth * Vol) — eq. 41. Rth=0.2, Vol=1 -> CSPI=5."""
        assert cspi_calc(rth=0.2, vol_cs=1.0) == pytest.approx(5.0)

    def test_cspi_units_consistency(self):
        """Rth=1 K/W, Vol=1 liter -> CSPI=1 W/(K*liter)."""
        assert cspi_calc(rth=1.0, vol_cs=1.0) == pytest.approx(1.0)


class TestFanScalingLiterature:
    def test_drofenik_eq29_31_roundtrip(self):
        """Fan scaling roundtrip: fit k then reconstruct original values."""
        v_max, dp_max, p_fan = 0.06, 80.0, 4.0
        d, n = 0.10, 3000.0
        k1, k2, k3 = fan_scaling_fit(v_max=v_max, dp_max=dp_max, p_fan=p_fan, d=d, n=n)
        assert k1 * n * d**3 == pytest.approx(v_max, rel=1e-10)
        assert k2 * n**2 * d**2 == pytest.approx(dp_max, rel=1e-10)
        assert k3 * n**3 * d**5 == pytest.approx(p_fan, rel=1e-10)
