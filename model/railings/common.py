"""Geometría común de barandas (postes + travesaño)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import trimesh
import trimesh.transformations as tf

from model.geom import Solid, Volume

MAT_RAILING = "color_railing"

# Sección madera (1 u = 0,1 m): poste ~9 cm, travesaño ~7×5 cm
POST_SIZE = 0.9
RAIL_WIDTH = 0.7
RAIL_DEPTH = 0.5
DEFAULT_POST_SPACING = 5.0  # 0,5 m entre ejes de postes
POST_HALF = POST_SIZE / 2.0


@dataclass(frozen=True)
class RailingSpec:
    part_id: str
    solid: Solid
    material: str = MAT_RAILING


def _beam_between(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    *,
    width: float,
    depth: float,
) -> Solid:
    a = np.array(p0, dtype=float)
    b = np.array(p1, dtype=float)
    vec = b - a
    length = float(np.linalg.norm(vec))
    if length < 1e-6:
        raise ValueError("Segmento de baranda degenerado.")

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


def _merge_solids(solids: list[Solid]) -> Solid:
    combined = trimesh.util.concatenate(
        [solid.to_trimesh(strict=False) for solid in solids]
    )
    return Solid.from_trimesh_relaxed(combined)


def _post_at(x: float, y: float, z_floor: float, *, height: float) -> Solid:
    return Solid.from_volume(
        Volume.from_aabb(
            x - POST_HALF,
            y - POST_HALF,
            z_floor,
            x + POST_HALF,
            y + POST_HALF,
            z_floor + height,
        )
    )


def _rail_between(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    *,
    height: float,
) -> Solid:
    q0 = (p0[0], p0[1], p0[2] + height)
    q1 = (p1[0], p1[1], p1[2] + height)
    return _beam_between(q0, q1, width=RAIL_WIDTH, depth=RAIL_DEPTH)


def _sample_path(
    points: list[tuple[float, float, float]],
    spacing: float,
) -> list[tuple[float, float, float]]:
    if not points:
        return []
    if len(points) == 1:
        return [points[0]]

    samples: list[tuple[float, float, float]] = [points[0]]
    for i in range(len(points) - 1):
        start = np.array(points[i], dtype=float)
        end = np.array(points[i + 1], dtype=float)
        seg = end - start
        length = float(np.linalg.norm(seg))
        if length < 1e-6:
            continue
        direction = seg / length
        walked = spacing
        while walked < length - 1e-6:
            samples.append(tuple(start + direction * walked))
            walked += spacing
    if samples[-1] != points[-1]:
        samples.append(points[-1])
    return samples


def build_railing(
    part_id: str,
    polylines: list[list[tuple[float, float, float]]],
    *,
    height: float,
    spacing: float = DEFAULT_POST_SPACING,
) -> RailingSpec:
    parts: list[Solid] = []
    seen_posts: set[tuple[float, float, float]] = set()

    for polyline in polylines:
        if len(polyline) < 2:
            continue
        samples = _sample_path(polyline, spacing)
        for point in samples:
            key = (round(point[0], 4), round(point[1], 4), round(point[2], 4))
            if key in seen_posts:
                continue
            seen_posts.add(key)
            parts.append(_post_at(point[0], point[1], point[2], height=height))
        parts.extend(
            _rail_between(polyline[i], polyline[i + 1], height=height)
            for i in range(len(polyline) - 1)
        )

    return RailingSpec(part_id, _merge_solids(parts))
