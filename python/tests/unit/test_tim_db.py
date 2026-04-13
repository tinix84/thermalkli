"""Tests for thermal_cli.tim.tim_db."""

from __future__ import annotations

import pytest

from thermal_cli.tim.tim_db import load_tim_db, search_tim


class TestLoadTimDb:
    def test_returns_38_entries(self):
        entries = load_tim_db()
        assert len(entries) == 38

    def test_first_entry_is_tgard_tnc4(self):
        entries = load_tim_db()
        e = entries[0]
        assert e.manufacturer == "LairdTech"
        assert e.type == "Tgard TNC-4"
        assert e.active is True

    def test_active_flag_false_for_kerafol(self):
        entries = load_tim_db()
        kerafol = next(e for e in entries if e.manufacturer == "Kerafol")
        assert kerafol.active is False

    def test_numeric_field_none_for_missing(self):
        """Ceramic Si3N4 has no thickness — must be None, not a string."""
        entries = load_tim_db()
        si3n4 = next(e for e in entries if "Si3N4" in e.description)
        assert si3n4.thickness_mm is None

    def test_k_wm1k1_kerafol_u90(self):
        entries = load_tim_db()
        u90 = next(e for e in entries if e.type == "Keratherm U90")
        assert u90.k_wm1k1 == pytest.approx(6.0)


class TestSearchTim:
    def test_search_kerafol_returns_4(self):
        results = search_tim("kerafol")
        assert len(results) == 4
        assert all(e.manufacturer == "Kerafol" for e in results)

    def test_search_case_insensitive(self):
        lower = search_tim("kerafol")
        upper = search_tim("KERAFOL")
        assert len(lower) == len(upper)

    def test_search_no_match_returns_empty(self):
        assert search_tim("xyzzy_does_not_exist") == []

    def test_search_matches_description(self):
        results = search_tim("gapfiller")
        assert len(results) >= 4  # pads + pastes with "Gapfiller" in description

    def test_search_paste_matches_wacker_and_electrolube(self):
        results = search_tim("paste")
        manufacturers = {e.manufacturer for e in results}
        assert "Wacker" in manufacturers
        assert "Electrolube" in manufacturers
