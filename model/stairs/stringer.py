"""Patinillos de escalera (EP-*)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import trimesh
import trimesh.transformations as tf

from model.geom import Solid
from model.stairs.beam import MAT_STAIR
from model.stairs.envelope import (
    EP001_P0,
    EP001_P1,
    EP001_P2,
    EP002_P0,
    EP002_P1,
    EP002_P2,
    EP002_P3,
)

STRINGER_WIDTH = 1.0
STRINGER_DEPTH = 1.0


@dataclass(frozen=True)
class StairStringerSpec:
    part_id: str
    solid: Solid
    material: str = MAT_STAIR


def _beam_between(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    *,
    width: float = STRINGER_WIDTH,
    depth: float = STRINGER_DEPTH,
) -> Solid:
    a = np.array(p0, dtype=float)
    b = np.array(p1, dtype=float)
    vec = b - a
    length = float(np.linalg.norm(vec))
    if length < 1e-6:
        raise ValueError("Segmento de patinillo degenerado.")

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


def _stringer_solid(*points: tuple[float, float, float]) -> Solid:
    segments = [_beam_between(points[i], points[i + 1]) for i in range(len(points) - 1)]
    combined = trimesh.util.concatenate(
        [segment.to_trimesh(strict=False) for segment in segments]
    )
    return Solid.from_trimesh_relaxed(combined)


def _stringer_from_polylines(*polylines: tuple[tuple[float, float, float], ...]) -> Solid:
    segments: list[Solid] = []
    for polyline in polylines:
        segments.extend(
            _beam_between(polyline[i], polyline[i + 1])
            for i in range(len(polyline) - 1)
        )
    combined = trimesh.util.concatenate(
        [segment.to_trimesh(strict=False) for segment in segments]
    )
    return Solid.from_trimesh_relaxed(combined)


def generate_stringers() -> list[StairStringerSpec]:
    return [
        StairStringerSpec("EP-001", _stringer_solid(EP001_P0, EP001_P1, EP001_P2)),
        StairStringerSpec(
            "EP-002",
            _stringer_from_polylines(
                (EP002_P0, EP002_P1),
                (EP002_P0, EP002_P2, EP002_P3),
            ),
        ),
    ]
