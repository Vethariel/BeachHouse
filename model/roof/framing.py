"""Roof framing beam generation."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import trimesh
import trimesh.transformations as tf

from model.geom import Solid, Vec3, Volume
from model.roof.plane import X_MAX, X_MIN, roof_z_at

MAT_ROOF_FRAMING = "color_7035299"
MAT_ROOF_JOIST = "color_16768282"
MAT_ROOF_DIAGONAL = "color_16089887"

BEAM_WIDTH = 1.0
BEAM_CANTO = 2.5
JOIST_WIDTH = 0.5
JOIST_CANTO = 1.5
JOIST_SPACING = 4.5
DIAGONAL_WIDTH = 1.0
DIAGONAL_DEPTH = 1.0
# Ajuste de empalme (~4 cm real por extremo; 1 u. modelo = 10 cm)
DIAGONAL_ROOF_INSET = 0.8
DIAGONAL_PILLAR_EXTEND = 0.4

PILLAR_COLUMNS_X = (25.0, 60.0, 77.0, 98.0)
ROOF_ROWS_Y = (0.0, -25.0, -50.0, -75.0, -100.0)

# Mitad del tramo de pilar correspondiente al segundo piso (forjado P2 top → tope original)
Z_P2_FLOOR_TOP = 45.0
Z_P2_STORY_TOP = 73.0
Z_PILLAR_P2_MID = (Z_P2_FLOOR_TOP + Z_P2_STORY_TOP) / 2.0
PILLAR_HALF = 1.0


@dataclass(frozen=True)
class FramingSpec:
    part_id: str
    solid: Solid
    material: str = MAT_ROOF_FRAMING


def _sloped_beam_along_x(x0: float, x1: float, y: float) -> Solid:
    z0 = roof_z_at(x0)
    z1 = roof_z_at(x1)
    half = BEAM_WIDTH / 2
    p0 = Vec3(x0, y + half, z0)
    p1 = Vec3(x1, y + half, z1)
    p2 = Vec3(x1, y - half, z1)
    p3 = Vec3(x0, y - half, z0)
    bottom = [p3, p2, p1, p0]
    top = [Vec3(p.x, p.y, p.z + BEAM_CANTO) for p in bottom]
    return Solid.from_volume(Volume(bottom + top))


def _beam_along_y(
    x: float,
    y0: float,
    y1: float,
    *,
    width: float = BEAM_WIDTH,
    canto: float = BEAM_CANTO,
) -> Solid:
    z = roof_z_at(x)
    half = width / 2
    ya, yb = sorted((y0, y1))
    return Solid.from_volume(
        Volume.from_aabb(x - half, ya, z, x + half, yb, z + canto)
    )


def _beam_between(
    p0: Vec3,
    p1: Vec3,
    *,
    width: float = DIAGONAL_WIDTH,
    depth: float = DIAGONAL_DEPTH,
) -> Solid:
    a = np.array(p0.as_tuple(), dtype=float)
    b = np.array(p1.as_tuple(), dtype=float)
    vec = b - a
    length = float(np.linalg.norm(vec))
    if length < 1e-6:
        raise ValueError("La diagonal requiere dos puntos distintos.")

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


def _joist_x_positions(x0: float, x1: float) -> list[float]:
    span = x1 - x0
    if span < 8:
        return []
    if span <= 22:
        mid = (x0 + x1) / 2.0
        return [mid - 2.25, mid + 2.25]
    positions: list[float] = []
    x = x0 + 3.25
    while x <= x1 - 3.25 + 1e-6:
        positions.append(x)
        x += JOIST_SPACING
    return positions


def _primary_framing_specs(seq: int) -> tuple[list[FramingSpec], int]:
    specs: list[FramingSpec] = []
    x_spans = [
        (X_MIN, PILLAR_COLUMNS_X[0]),
        (PILLAR_COLUMNS_X[0], PILLAR_COLUMNS_X[1]),
        (PILLAR_COLUMNS_X[1], PILLAR_COLUMNS_X[2]),
        (PILLAR_COLUMNS_X[2], PILLAR_COLUMNS_X[3]),
        (PILLAR_COLUMNS_X[3], X_MAX),
    ]

    for y in ROOF_ROWS_Y:
        for x0, x1 in x_spans:
            solid = _sloped_beam_along_x(x0, x1, y)
            specs.append(FramingSpec(f"RF-{seq:03d}", solid, MAT_ROOF_FRAMING))
            seq += 1

    y_spans = list(zip(ROOF_ROWS_Y, ROOF_ROWS_Y[1:]))
    for x in PILLAR_COLUMNS_X:
        for y0, y1 in y_spans:
            solid = _beam_along_y(x, y0, y1)
            specs.append(FramingSpec(f"RF-{seq:03d}", solid, MAT_ROOF_FRAMING))
            seq += 1

    return specs, seq


def _joist_specs(seq: int) -> tuple[list[FramingSpec], int]:
    specs: list[FramingSpec] = []
    x_spans = [
        (X_MIN, PILLAR_COLUMNS_X[0]),
        (PILLAR_COLUMNS_X[0], PILLAR_COLUMNS_X[1]),
        (PILLAR_COLUMNS_X[1], PILLAR_COLUMNS_X[2]),
        (PILLAR_COLUMNS_X[2], PILLAR_COLUMNS_X[3]),
        (PILLAR_COLUMNS_X[3], X_MAX),
    ]
    y_spans = list(zip(ROOF_ROWS_Y, ROOF_ROWS_Y[1:]))

    for y0, y1 in y_spans:
        for x0, x1 in x_spans:
            for x in _joist_x_positions(x0, x1):
                solid = _beam_along_y(
                    x,
                    y0,
                    y1,
                    width=JOIST_WIDTH,
                    canto=JOIST_CANTO,
                )
                specs.append(FramingSpec(f"RJ-{seq:03d}", solid, MAT_ROOF_JOIST))
                seq += 1

    return specs, seq


def _adjust_diagonal_endpoints(p0: Vec3, p1: Vec3) -> tuple[Vec3, Vec3]:
    """Acorta la punta voladizo e introduce la diagonal un poco más en el pilar."""
    a = np.array(p0.as_tuple(), dtype=float)
    b = np.array(p1.as_tuple(), dtype=float)
    direction = b - a
    length = float(np.linalg.norm(direction))
    if length < 1e-6:
        raise ValueError("La diagonal requiere dos puntos distintos.")
    direction /= length
    a_adj = a + direction * DIAGONAL_ROOF_INSET
    b_adj = b + direction * DIAGONAL_PILLAR_EXTEND
    return Vec3(*a_adj), Vec3(*b_adj)


def _voladizo_diagonal_specs(seq: int) -> tuple[list[FramingSpec], int]:
    specs: list[FramingSpec] = []

    for y in ROOF_ROWS_Y:
        z_tip_high = roof_z_at(X_MIN) + BEAM_CANTO
        p0, p1 = _adjust_diagonal_endpoints(
            Vec3(X_MIN, y, z_tip_high),
            Vec3(PILLAR_COLUMNS_X[0], y, Z_PILLAR_P2_MID),
        )
        specs.append(
            FramingSpec(
                f"RD-{seq:03d}",
                _beam_between(p0, p1),
                MAT_ROOF_DIAGONAL,
            )
        )
        seq += 1

        z_tip_low = roof_z_at(X_MAX) + BEAM_CANTO
        p0, p1 = _adjust_diagonal_endpoints(
            Vec3(X_MAX, y, z_tip_low),
            Vec3(PILLAR_COLUMNS_X[3], y, Z_PILLAR_P2_MID),
        )
        specs.append(
            FramingSpec(
                f"RD-{seq:03d}",
                _beam_between(p0, p1),
                MAT_ROOF_DIAGONAL,
            )
        )
        seq += 1

    return specs, seq


def generate_roof_diagonals() -> list[FramingSpec]:
    specs, _ = _voladizo_diagonal_specs(1)
    return specs


def generate_roof_framing() -> list[FramingSpec]:
    specs: list[FramingSpec] = []
    seq = 1

    primary, seq = _primary_framing_specs(seq)
    specs.extend(primary)

    joists, seq = _joist_specs(1)
    specs.extend(joists)

    diagonals, _ = _voladizo_diagonal_specs(1)
    specs.extend(diagonals)

    return specs
