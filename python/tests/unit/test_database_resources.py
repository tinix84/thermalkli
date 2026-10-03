"""Tests for installed database CSV resources and source-data parity."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import pytest

DATABASE_CSVS = (
    "fans.csv",
    "fluid_H2OGly50.csv",
    "fluid_SAE30.csv",
    "fluid_airDry.csv",
    "heatsinks_extruded.csv",
    "heatsinks_generic.csv",
    "hs_materials.csv",
    "hs_profiles.csv",
    "tim.csv",
)
SOURCE_DB = Path(__file__).resolve().parents[3] / "db"


@pytest.mark.parametrize("filename", DATABASE_CSVS)
def test_database_resource_matches_root_source(filename: str) -> None:
    resource = files("thermal_cli").joinpath("data", filename)
    source = SOURCE_DB / filename

    assert resource.is_file()
    assert source.is_file()
    assert resource.read_bytes() == source.read_bytes()
