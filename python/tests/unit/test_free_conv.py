"""Unit tests for thermal_cli.formula.free_conv.

Reference cases:
  - Single vertical face: physics sanity checks (T > ambient, q ≈ P_total)
  - Multi-face box: energy closure
  - Monotonicity: more power → higher temperature
  - Default emissivity: Face without explicit emissivity == Face(emissivity=0.9)
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from thermal_cli.formula.free_conv import Face, FreeConvResult, free_conv_surface_temp

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _single_vertical_face(area: float = 0.01, char_length: float = 0.05) -> list[Face]:
    return [Face(area=area, char_length=char_length, orientation="vertical")]


# ---------------------------------------------------------------------------
# Test: single vertical face, 10 W
# ---------------------------------------------------------------------------


class TestSingleVerticalFace:
    """Single vertical face: 10 W, 0.01 m², char_length=0.05 m, T_amb=300 K."""

    T_AMB = 300.0  # K
    P = 10.0  # W
    FACES = _single_vertical_face(area=0.01, char_length=0.05)

    def test_returns_free_conv_result(self):
        result = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=self.P)
        assert isinstance(result, FreeConvResult)

    def test_surface_temp_above_ambient(self):
        result = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=self.P)
        assert result.t_surface > self.T_AMB

    def test_surface_temp_above_ambient_by_30K(self):
        """10 W on 0.01 m² should require ΔT >> 30 K."""
        result = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=self.P)
        assert result.t_surface > self.T_AMB + 30.0

    def test_energy_closure(self):
        """sum(q_per_face) ≈ p_total within 1%."""
        result = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=self.P)
        assert sum(result.q_per_face) == pytest.approx(self.P, rel=0.01)

    def test_per_face_lists_have_correct_length(self):
        result = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=self.P)
        assert len(result.h_per_face) == 1
        assert len(result.q_per_face) == 1

    def test_h_per_face_positive(self):
        result = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=self.P)
        assert result.h_per_face[0] > 0


# ---------------------------------------------------------------------------
# Test: multi-face box, 5 faces
# ---------------------------------------------------------------------------


class TestMultiFaceBox:
    """5-face box (two vertical pairs + one top), 5 W, T_amb=298.15 K."""

    T_AMB = 298.15
    P = 5.0
    FACES: ClassVar[list[Face]] = [
        Face(area=0.05 * 0.10, char_length=0.10, orientation="vertical"),
        Face(area=0.05 * 0.10, char_length=0.10, orientation="vertical"),
        Face(area=0.08 * 0.10, char_length=0.08, orientation="vertical"),
        Face(area=0.08 * 0.10, char_length=0.08, orientation="vertical"),
        Face(area=0.05 * 0.08, char_length=0.05, orientation="horizontal_top"),
    ]

    def test_energy_closure(self):
        """sum(q_per_face) ≈ p_total within 1%."""
        result = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=self.P)
        assert sum(result.q_per_face) == pytest.approx(self.P, rel=0.01)

    def test_per_face_lists_length(self):
        result = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=self.P)
        assert len(result.h_per_face) == 5
        assert len(result.q_per_face) == 5

    def test_surface_temp_above_ambient(self):
        result = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=self.P)
        assert result.t_surface > self.T_AMB


# ---------------------------------------------------------------------------
# Test: monotonicity — more power → higher temperature
# ---------------------------------------------------------------------------


class TestMonotonicity:
    T_AMB = 300.0
    FACES = _single_vertical_face(area=0.01, char_length=0.1)

    def test_higher_power_gives_higher_temperature(self):
        res_low = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=1.0)
        res_high = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=10.0)
        assert res_high.t_surface > res_low.t_surface

    def test_higher_power_gives_higher_q(self):
        res_low = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=1.0)
        res_high = free_conv_surface_temp(faces=self.FACES, t_ambient=self.T_AMB, p_total=10.0)
        assert sum(res_high.q_per_face) > sum(res_low.q_per_face)


# ---------------------------------------------------------------------------
# Test: default emissivity = 0.9
# ---------------------------------------------------------------------------


class TestDefaultEmissivity:
    T_AMB = 300.0
    P = 5.0

    def test_default_emissivity_equals_explicit_09(self):
        """Face() without emissivity should behave identically to emissivity=0.9."""
        face_default = Face(area=0.02, char_length=0.1, orientation="vertical")
        face_explicit = Face(area=0.02, char_length=0.1, orientation="vertical", emissivity=0.9)

        res_default = free_conv_surface_temp(
            faces=[face_default], t_ambient=self.T_AMB, p_total=self.P
        )
        res_explicit = free_conv_surface_temp(
            faces=[face_explicit], t_ambient=self.T_AMB, p_total=self.P
        )

        assert res_default.t_surface == pytest.approx(res_explicit.t_surface, abs=1e-9)
        assert res_default.h_per_face[0] == pytest.approx(res_explicit.h_per_face[0], rel=1e-9)

    def test_default_emissivity_value_is_09(self):
        face = Face(area=0.01, char_length=0.05, orientation="vertical")
        assert face.emissivity == 0.9


# ---------------------------------------------------------------------------
# Test: keyword-only enforcement
# ---------------------------------------------------------------------------


class TestKeywordOnly:
    def test_keyword_only_raises_on_positional(self):
        with pytest.raises(TypeError):
            free_conv_surface_temp(  # type: ignore[misc]
                [Face(area=0.01, char_length=0.05, orientation="vertical")],
                300.0,
                10.0,
            )
