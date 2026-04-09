"""Tests for the .m → .yaml config converter."""

from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from thermal_cli.cli.main import app
from thermal_cli.io.convert_m_to_yaml import parse_m_config

runner = CliRunner()


def test_parse_scalar_float() -> None:
    text = "function cfg = test()\n    cfg.x = 1.5;\nend"
    result = parse_m_config(text)
    assert result == {"x": 1.5}


def test_parse_scientific_notation() -> None:
    text = "function cfg = test()\n    cfg.k = 5e-3;\nend"
    result = parse_m_config(text)
    assert result == {"k": 5e-3}


def test_parse_string() -> None:
    text = "function cfg = test()\n    cfg.name = 'hello';\nend"
    result = parse_m_config(text)
    assert result == {"name": "hello"}


def test_parse_array() -> None:
    text = "function cfg = test()\n    cfg.v = [1 2 3];\nend"
    result = parse_m_config(text)
    assert result == {"v": [1, 2, 3]}


def test_parse_array_with_commas() -> None:
    text = "function cfg = test()\n    cfg.v = [1, 2, 3];\nend"
    result = parse_m_config(text)
    assert result == {"v": [1, 2, 3]}


def test_parse_nested_struct() -> None:
    text = (
        "function cfg = test()\n"
        "    cfg.heatsink.width = 0.063;\n"
        "    cfg.heatsink.length = 0.130;\n"
        "end"
    )
    result = parse_m_config(text)
    assert result == {"heatsink": {"width": 0.063, "length": 0.130}}


def test_parse_mixed_types() -> None:
    text = (
        "function cfg = test()\n"
        "    cfg.fluid.type = 'H2OGly50';\n"
        "    cfg.fluid.flowrate = 1.0;\n"
        "    cfg.fluid.tInlet = 343.15;\n"
        "end"
    )
    result = parse_m_config(text)
    assert result == {"fluid": {"type": "H2OGly50", "flowrate": 1.0, "tInlet": 343.15}}


def test_parse_ignores_comments() -> None:
    text = "function cfg = test()\n    % This is a comment\n    cfg.x = 1;  % inline comment\nend"
    result = parse_m_config(text)
    assert result == {"x": 1}


def test_parse_real_config() -> None:
    """Parse the actual example_cspi_sweep.m from the repo."""
    text = (
        "function cfg = example_cspi_sweep()\n"
        "    cfg.a_chip = 32e-4;\n"
        "    cfg.p_fan_max = 20;\n"
        "    cfg.lambda = [210 380];\n"
        "    cfg.c = [0.02 0.04 0.06 0.08 0.12];\n"
        "    cfg.t_min = 0.5e-3;\n"
        "end"
    )
    result = parse_m_config(text)
    assert result["a_chip"] == 32e-4
    assert result["p_fan_max"] == 20
    assert result["lambda"] == [210, 380]
    assert len(result["c"]) == 5
    assert result["t_min"] == 0.5e-3


def test_cli_convert_config(tmp_path: Path) -> None:
    """Test the CLI convert-config command end-to-end."""
    m_file = tmp_path / "test.m"
    yaml_file = tmp_path / "test.yaml"
    m_file.write_text(
        "function cfg = test()\n"
        "    cfg.heatsink.width = 0.063;\n"
        "    cfg.fluid.type = 'airDry';\n"
        "end"
    )
    result = runner.invoke(app, ["convert-config", str(m_file), str(yaml_file)])
    assert result.exit_code == 0
    assert "Converted" in result.stdout

    parsed = yaml.safe_load(yaml_file.read_text())
    assert parsed == {"heatsink": {"width": 0.063}, "fluid": {"type": "airDry"}}


def test_cli_convert_config_missing_file(tmp_path: Path) -> None:
    """Nonexistent .m file should fail with exit code 1."""
    result = runner.invoke(app, ["convert-config", str(tmp_path / "nope.m"), "out.yaml"])
    assert result.exit_code == 1
    assert "not found" in result.stdout
