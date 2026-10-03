"""Access the thermal CSV databases in source checkouts and installed wheels."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from typing import TextIO


def _source_database_path(filename: str) -> Path | None:
    """Return the repository-root CSV only when this is the source package."""
    package_dir = Path(__file__).resolve().parent
    python_root = package_dir.parent.parent
    source_package = (python_root / "src" / "thermal_cli").resolve()
    if package_dir != source_package or not (python_root / "pyproject.toml").is_file():
        return None

    candidate = python_root.parent / "db" / filename
    return candidate if candidate.is_file() else None


@contextmanager
def open_database_csv(filename: str) -> Iterator[TextIO]:
    """Open a CSV from the checkout database or bundled package resources.

    Source checkouts continue to read the canonical repository-root ``db/``
    files. Installed distributions read their copy in ``thermal_cli/data`` and
    do not search parent directories for incidental data.
    """
    if Path(filename).name != filename or not filename.endswith(".csv"):
        raise ValueError(f"Expected a CSV filename, got {filename!r}")

    source_path = _source_database_path(filename)
    if source_path is not None:
        with source_path.open("r", newline="", encoding="utf-8") as stream:
            yield stream
        return

    resource = files("thermal_cli").joinpath("data", filename)
    if not resource.is_file():
        raise FileNotFoundError(
            f"Database CSV {filename!r} is missing from the thermal_cli package resources"
        )
    with (
        as_file(resource) as resource_path,
        resource_path.open("r", newline="", encoding="utf-8") as stream,
    ):
        yield stream
