"""Conservative 2.5D baseplate solver using vertex-centered control volumes.

The grid retains nx-by-ny temperature unknowns at coordinates including each
plate edge. Dual control volumes at edge nodes have half-width/height. Lateral
face conductances and distributed vertical extraction are integrated over
those exact control-volume measures; the perimeter is adiabatic.
"""

from __future__ import annotations

import math
from itertools import pairwise
from typing import Any

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from thermal_cli.baseplate.types import BaseplateConfig, BaseplateResult, Device, DeviceResult


def _require_finite_number(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(f"{name} must be a finite number")
    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        raise ValueError(f"{name} must be a finite number")
    return numeric_value


def _control_volume_bounds(points: np.ndarray, extent: float) -> np.ndarray:
    """Return dual-cell bounds for point samples that include both plate edges."""
    bounds: np.ndarray = np.empty(points.size + 1, dtype=float)
    bounds[0] = 0.0
    bounds[-1] = extent
    bounds[1:-1] = 0.5 * (points[:-1] + points[1:])
    return bounds


def _overlap_lengths(bounds: np.ndarray, center: float, extent: float) -> np.ndarray:
    """Intersect a centered interval with cells without subtracting close endpoints."""
    half_extent = extent / 2.0
    interval_min = center - half_extent
    interval_max = center + half_extent
    overlaps: np.ndarray = np.zeros(bounds.size - 1, dtype=float)

    for index, (cell_min, cell_max) in enumerate(pairwise(bounds)):
        if interval_max <= cell_min or interval_min >= cell_max:
            continue
        if cell_min <= interval_min and interval_max <= cell_max:
            # Preserve the declared interval measure when one cell contains it.
            overlap = extent
        elif interval_min <= cell_min and cell_max <= interval_max:
            overlap = cell_max - cell_min
        elif interval_min < cell_min:
            # The interval starts before this cell and ends inside it.
            overlap = half_extent + (center - cell_min)
        else:
            # The interval starts inside this cell and ends beyond it.
            overlap = half_extent + (cell_max - center)
        overlaps[index] = overlap

    return overlaps


def _device_footprint(
    device: Device, lx: float, ly: float
) -> tuple[float, float, float, float, float]:
    x = _require_finite_number(f"device {device.name!r} x", device.x)
    y = _require_finite_number(f"device {device.name!r} y", device.y)
    width = _require_finite_number(f"device {device.name!r} width", device.width)
    height = _require_finite_number(f"device {device.name!r} height", device.height)
    power = _require_finite_number(f"device {device.name!r} power", device.power)
    r_jc = _require_finite_number(f"device {device.name!r} r_jc", device.r_jc)
    r_interface = _require_finite_number(f"device {device.name!r} r_interface", device.r_interface)
    if width <= 0.0 or height <= 0.0:
        raise ValueError(f"device {device.name!r} footprint dimensions must be positive")
    if power < 0.0 or r_jc < 0.0 or r_interface < 0.0:
        raise ValueError(f"device {device.name!r} power and resistances must be nonnegative")

    x_min = x - width / 2.0
    x_max = x + width / 2.0
    y_min = y - height / 2.0
    y_max = y + height / 2.0
    if x_min < 0.0 or y_min < 0.0 or x_max > lx or y_max > ly:
        raise ValueError(
            f"device {device.name!r} footprint must be fully inside the baseplate; "
            "footprints are not clipped or renormalized"
        )
    return x_min, x_max, y_min, y_max, width * height


def _map_fdm_sources(
    config: BaseplateConfig,
    *,
    lx: float,
    ly: float,
    x_bounds: np.ndarray,
    y_bounds: np.ndarray,
) -> tuple[np.ndarray, float, float]:
    """Distribute complete device power over the vertex-centered dual cells."""
    nx, ny = int(config.nx), int(config.ny)
    source_power: np.ndarray = np.zeros((ny, nx), dtype=float)
    requested_power = math.fsum(
        _require_finite_number(f"device {device.name!r} power", device.power)
        for device in config.devices
    )
    for device in config.devices:
        _, _, _, _, footprint_area = _device_footprint(device, lx, ly)
        overlap_x = _overlap_lengths(x_bounds, device.x, device.width)
        overlap_y = _overlap_lengths(y_bounds, device.y, device.height)
        intersection_areas = np.outer(overlap_y, overlap_x)
        source_power += float(device.power) * intersection_areas / footprint_area

    heat_input = float(np.sum(source_power, dtype=np.float64))
    epsilon = float(np.finfo(float).eps)
    smallest_positive = float(np.finfo(float).tiny)
    source_tolerance = 64.0 * epsilon * max(abs(requested_power), smallest_positive)
    if abs(heat_input - requested_power) > source_tolerance:
        raise RuntimeError("control-volume source mapping did not conserve device power")
    return source_power, heat_input, requested_power


def _assemble_fdm_matrix(
    *,
    nx: int,
    ny: int,
    sheet_conductance: float,
    x_widths: np.ndarray,
    y_widths: np.ndarray,
    dx: float,
    dy: float,
    sink_conductance: np.ndarray,
) -> Any:
    """Assemble the conservative sparse conductance matrix, excluding the solve."""
    node_count = nx * ny
    diagonal = sink_conductance.ravel().copy()
    x_face_conductance = sheet_conductance * y_widths / dx
    y_face_conductance = sheet_conductance * x_widths / dy
    node_grid = np.arange(node_count).reshape((ny, nx))
    x_first = node_grid[:, :-1].ravel()
    x_second = node_grid[:, 1:].ravel()
    x_values = np.broadcast_to(x_face_conductance[:, None], (ny, nx - 1)).ravel()
    y_first = node_grid[:-1, :].ravel()
    y_second = node_grid[1:, :].ravel()
    y_values = np.broadcast_to(y_face_conductance[None, :], (ny - 1, nx)).ravel()

    np.add.at(diagonal, x_first, x_values)
    np.add.at(diagonal, x_second, x_values)
    np.add.at(diagonal, y_first, y_values)
    np.add.at(diagonal, y_second, y_values)
    all_nodes = np.arange(node_count)
    rows = np.concatenate((x_first, x_second, y_first, y_second, all_nodes))
    columns = np.concatenate((x_second, x_first, y_second, y_first, all_nodes))
    values = np.concatenate((-x_values, -x_values, -y_values, -y_values, diagonal))
    return coo_matrix(
        (values, (rows, columns)), shape=(node_count, node_count), dtype=float
    ).tocsr()


def solve_fdm(config: BaseplateConfig) -> BaseplateResult:
    """Solve the steady 2.5D baseplate model with conservative finite volumes.

    nx and ny remain the number of vertex-centered unknowns, including nodes
    on the plate perimeter. Boundary nodes own half-width/half-height dual
    control volumes. Device base temperatures are area-weighted over their
    complete thermal footprints; t_max is the maximum grid-point temperature.
    """
    lx = _require_finite_number("lx", config.lx)
    ly = _require_finite_number("ly", config.ly)
    thickness = _require_finite_number("thickness", config.thickness)
    conductivity = _require_finite_number("conductivity", config.conductivity)
    r_sa = _require_finite_number("r_sa", config.r_sa)
    t_reference = _require_finite_number("t_ambient", config.t_ambient)
    if t_reference < 0.0:
        raise ValueError("t_ambient must be an absolute temperature in Kelvin")
    if min(lx, ly, thickness, conductivity, r_sa) <= 0.0:
        raise ValueError("plate dimensions, thickness, conductivity, and r_sa must be positive")
    if (
        isinstance(config.nx, bool)
        or not isinstance(config.nx, (int, np.integer))
        or isinstance(config.ny, bool)
        or not isinstance(config.ny, (int, np.integer))
        or config.nx < 2
        or config.ny < 2
    ):
        raise ValueError("nx and ny must be integers of at least 2")

    nx, ny = int(config.nx), int(config.ny)
    x_grid = np.linspace(0.0, lx, nx)
    y_grid = np.linspace(0.0, ly, ny)
    dx = lx / (nx - 1)
    dy = ly / (ny - 1)

    x_bounds = _control_volume_bounds(x_grid, lx)
    y_bounds = _control_volume_bounds(y_grid, ly)
    x_widths = np.diff(x_bounds)
    y_widths = np.diff(y_bounds)
    cell_areas = np.outer(y_widths, x_widths)
    baseplate_area = lx * ly
    if not math.isfinite(baseplate_area) or baseplate_area <= 0.0:
        raise ValueError("baseplate area must be finite and positive")
    sheet_conductance = conductivity * thickness
    if not math.isfinite(sheet_conductance) or sheet_conductance <= 0.0:
        raise ValueError("conductivity times thickness must be finite and positive")

    source_power, heat_input, _ = _map_fdm_sources(
        config,
        lx=lx,
        ly=ly,
        x_bounds=x_bounds,
        y_bounds=y_bounds,
    )

    r_area = r_sa * baseplate_area
    if not math.isfinite(r_area) or r_area <= 0.0:
        raise ValueError("R_area = r_sa * baseplate area must be finite and positive")
    sink_conductance = cell_areas / r_area

    matrix = _assemble_fdm_matrix(
        nx=nx,
        ny=ny,
        sheet_conductance=sheet_conductance,
        x_widths=x_widths,
        y_widths=y_widths,
        dx=dx,
        dy=dy,
        sink_conductance=sink_conductance,
    )
    right_hand_side = source_power.ravel()
    temperature_rise_flat = np.asarray(spsolve(matrix, right_hand_side), dtype=float)
    if not np.all(np.isfinite(temperature_rise_flat)):
        raise RuntimeError("baseplate solve produced a nonfinite temperature rise")
    temperature_rise = temperature_rise_flat.reshape((ny, nx))
    temperature = t_reference + temperature_rise

    residual = matrix @ temperature_rise_flat - right_hand_side
    residual_inf = float(np.linalg.norm(residual, ord=np.inf))
    matrix_inf = float(np.max(np.asarray(abs(matrix).sum(axis=1)).ravel()))
    rise_inf = float(np.linalg.norm(temperature_rise_flat, ord=np.inf))
    rhs_inf = float(np.linalg.norm(right_hand_side, ord=np.inf))
    residual_scale = matrix_inf * rise_inf + rhs_inf
    linear_residual_norm = residual_inf / residual_scale if residual_scale else residual_inf

    heat_rejected = float(np.sum(temperature_rise * sink_conductance, dtype=np.float64))
    heat_scale = max(abs(heat_input), abs(heat_rejected))
    heat_balance_relative_error = (
        abs(heat_input - heat_rejected) / heat_scale if heat_scale else 0.0
    )
    device_results = []
    for device in config.devices:
        _, _, _, _, footprint_area = _device_footprint(device, lx, ly)
        overlap_x = _overlap_lengths(x_bounds, device.x, device.width)
        overlap_y = _overlap_lengths(y_bounds, device.y, device.height)
        footprint_areas = np.outer(overlap_y, overlap_x)
        t_base = float(np.sum(temperature * footprint_areas) / footprint_area)
        t_case = t_base + float(device.power) * float(device.r_interface)
        t_junction = t_case + float(device.power) * float(device.r_jc)
        device_results.append(
            DeviceResult(
                name=device.name,
                t_base=t_base,
                t_case=t_case,
                t_junction=t_junction,
            )
        )

    junction_temperatures = [device.t_junction for device in device_results]
    return BaseplateResult(
        t_field=temperature,
        x_grid=x_grid,
        y_grid=y_grid,
        devices=device_results,
        t_max=float(np.max(temperature)),
        t_mean=float(np.sum(temperature * cell_areas) / baseplate_area),
        t_j_max=max(junction_temperatures) if junction_temperatures else 0.0,
        t_j_mean=(
            sum(junction_temperatures) / len(junction_temperatures)
            if junction_temperatures
            else 0.0
        ),
        t_j_spread=(
            max(junction_temperatures) - min(junction_temperatures)
            if len(junction_temperatures) > 1
            else 0.0
        ),
        heat_input_W=heat_input,
        heat_rejected_W=heat_rejected,
        heat_balance_relative_error=heat_balance_relative_error,
        linear_residual_norm=linear_residual_norm,
    )
