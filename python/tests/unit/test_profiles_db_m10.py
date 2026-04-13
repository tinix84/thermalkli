"""Tests for M10 extensions to profiles_db (HsMaterial extra fields)."""

from __future__ import annotations

from thermal_cli.heatsinks.profiles_db import lookup_hs_material


class TestHsMaterialM10Fields:
    def test_all_aluminum_no_piastra(self):
        mat = lookup_hs_material("all_aluminum")
        assert mat.has_piastra is False
        assert mat.k_piastra == 0.0

    def test_all_alum_piastra_rame_has_piastra(self):
        mat = lookup_hs_material("all_alum_piastra_rame")
        assert mat.has_piastra is True
        assert mat.k_piastra == 350.0

    def test_all_copper_no_piastra(self):
        mat = lookup_hs_material("all_copper")
        assert mat.has_piastra is False
