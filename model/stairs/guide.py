"""Geometría temporal Fase A — contorno, descanso, viga medio, patinillos."""

from __future__ import annotations

import math

import numpy as np
import trimesh
import trimesh.transformations as tf

from model.geom import Solid, Vec3, Volume
from model.stairs.envelope import (
    EP001_P0,
    EP001_P1,
    EP001_P2,
    EP002_P0,
    EP002_P1,
    EP002_P2,
    EP002_P3,
    GUIDE_LINE_WIDTH,
    MAT_STAIRS_GUIDE,
    MAT_STAIRS_GUIDE_VOLUME,
    MID_BEAM_HALF_Y,
    RISER,
    RISERS_PER_FLIGHT,
    TREAD_THICK,
    X_EAST,
    X_WEST,
    Y_LANDING_NORTH,
    Y_LANDING_SOUTH,
    Y_MID_BEAM,
    Y_NORTH,
    Y_SOUTH,
    Z_EM_TOP,
    Z_LANDING_TREAD_TOP,
    Z_LANDING_TOP,
    Z_P1_TOP,
    Z_P2_TOP,
)


def _beam_between(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    *,
    width: float = GUIDE_LINE_WIDTH,
    depth: float = GUIDE_LINE_WIDTH,
) -> Solid:
    a = np.array(p0, dtype=float)
    b = np.array(p1, dtype=float)
    vec = b - a
    length = float(np.linalg.norm(vec))
    if length < 1e-6:
        raise ValueError("Segmento de guía degenerado.")

    direction = vec / length
    mesh = trimesh.creation.box(extents=[width, depth, length])
    z_axis = np.array([0.0, 0.0, 1.0])
    cross = np.cross(z_axis, direction)
    if float(np.linalg.norm(cross)) < 1e-6:
        cross = np.array([1.0, 0.0, 0.0])
    angle = math.acos(float(np.clip(np.dot(z_axis, direction), -1.0, 1.0)))
    matrix = tf.rotation_matrix(angle, cross)
    mesh.apply_transform(matrix)
    mesh.apply_translation((a + b) / 2.0)
    return Solid.from_trimesh(mesh)


def _box_solid(x0: float, y0: float, z0: float, x1: float, y1: float, z1: float) -> Solid:
    return Solid.from_volume(Volume.from_aabb(x0, y0, z0, x1, y1, z1))


def _perimeter_edges(x0: float, y0: float, x1: float, y1: float, z: float) -> list[Solid]:
    corners = [
        (x0, y0, z),
        (x1, y0, z),
        (x1, y1, z),
        (x0, y1, z),
    ]
    solids: list[Solid] = []
    for start, end in zip(corners, corners[1:] + corners[:1]):
        solids.append(_beam_between(start, end))
    return solids


def _vertical_edge(x: float, y: float, z0: float, z1: float) -> Solid:
    return _beam_between((x, y, z0), (x, y, z1))


def _riser_markers_on_oblique(
    x: float,
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    *,
    count: int,
) -> list[Solid]:
    """Marcas en cada contrahuella a lo largo del tramo oblicuo del patinillo."""
    _, y0, z0 = p0
    _, y1, z1 = p1
    solids: list[Solid] = []
    for step in range(1, count + 1):
        t = step / count
        y = y0 + (y1 - y0) * t
        z = z0 + (z1 - z0) * t
        solids.append(
            _box_solid(
                x - 0.35,
                y - 0.1,
                z - 0.05,
                x + 0.35,
                y + 0.1,
                z + 0.05,
            )
        )
    return solids


def _riser_markers(
    x: float,
    y0: float,
    y1: float,
    z0: float,
    *,
    count: int,
) -> list[Solid]:
    """Compat: contrahuellas uniformes en Z sobre un tramo recto en Y."""
    z1 = z0 + RISER * count
    return _riser_markers_on_oblique(x, (x, y0, z0), (x, y1, z1), count=count)


def _polyline_stringer(*points: tuple[float, float, float]) -> list[Solid]:
    return [
        _beam_between(points[i], points[i + 1]) for i in range(len(points) - 1)
    ]


def build_stair_guide_solids() -> tuple[list[Solid], list[Solid]]:
    lines: list[Solid] = []
    volumes: list[Solid] = []

    lines.extend(_perimeter_edges(X_WEST, Y_SOUTH, X_EAST, Y_NORTH, Z_P1_TOP))
    lines.extend(_perimeter_edges(X_WEST, Y_SOUTH, X_EAST, Y_NORTH, Z_P2_TOP))

    for x, y in (
        (X_WEST, Y_SOUTH),
        (X_EAST, Y_SOUTH),
        (X_EAST, Y_NORTH),
        (X_WEST, Y_NORTH),
    ):
        lines.append(_vertical_edge(x, y, Z_P1_TOP, Z_P2_TOP))

    volumes.append(
        _box_solid(
            X_WEST,
            Y_LANDING_SOUTH,
            Z_LANDING_TREAD_TOP - TREAD_THICK,
            X_EAST,
            Y_LANDING_NORTH,
            Z_LANDING_TREAD_TOP,
        )
    )
    volumes.append(
        _box_solid(
            X_WEST,
            Y_MID_BEAM - MID_BEAM_HALF_Y,
            Z_LANDING_TOP,
            X_EAST,
            Y_MID_BEAM + MID_BEAM_HALF_Y,
            Z_EM_TOP,
        )
    )

    lines.extend(_polyline_stringer(EP001_P0, EP001_P1, EP001_P2))
    lines.extend(_polyline_stringer(EP002_P0, EP002_P1))
    lines.extend(_polyline_stringer(EP002_P0, EP002_P2, EP002_P3))
    lines.extend(
        _riser_markers_on_oblique(
            X_WEST, EP001_P0, EP001_P1, count=RISERS_PER_FLIGHT
        )
    )
    lines.extend(
        _riser_markers_on_oblique(
            X_EAST, EP002_P0, EP002_P2, count=RISERS_PER_FLIGHT
        )
    )

    return lines, volumes


def build_stair_guide_meshes() -> list[dict]:
    line_parts, volume_parts = build_stair_guide_solids()
    meshes: list[dict] = []
    if line_parts:
        meshes.append(_merge_solids(line_parts, MAT_STAIRS_GUIDE))
    if volume_parts:
        meshes.append(_merge_solids(volume_parts, MAT_STAIRS_GUIDE_VOLUME))
    return meshes


def _merge_solids(solids: list[Solid], material: str) -> dict:
    combined = trimesh.util.concatenate([item.to_trimesh(strict=False) for item in solids])
    return Solid.from_trimesh_relaxed(combined).to_mesh(material=material, validate=False)
