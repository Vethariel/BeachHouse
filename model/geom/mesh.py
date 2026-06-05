from __future__ import annotations

import math
from collections import defaultdict

from model.geom.types import Vec3


def _format_vertex(point: Vec3) -> str:
    return f"{point.x:.4f} \t\t{point.y:.4f} \t\t{point.z:.4f}"


def _face_indices() -> list[list[int]]:
    return [
        [0, 1, 2],
        [0, 2, 3],
        [4, 5, 6],
        [4, 6, 7],
        [0, 1, 5],
        [0, 5, 4],
        [1, 2, 6],
        [1, 6, 5],
        [2, 3, 7],
        [2, 7, 6],
        [0, 3, 7],
        [0, 7, 4],
    ]


def mesh_to_obj_dict(
    vertices: list[Vec3],
    faces: list[list[int]],
    *,
    material: str,
) -> dict:
    return {
        "verts": [_format_vertex(v) for v in vertices],
        "faces_local": faces,
        "material": material,
    }


def volume_mesh(corners: list[Vec3], *, material: str) -> dict:
    if len(corners) != 8:
        raise ValueError("Un volumen requiere exactamente 8 vértices.")
    return mesh_to_obj_dict(corners, _face_indices(), material=material)


def plane_mesh(corners: list[Vec3], *, material: str) -> dict:
    if len(corners) != 4:
        raise ValueError("Un plano requiere exactamente 4 vértices.")
    faces = [[0, 1, 2], [0, 2, 3]]
    return mesh_to_obj_dict(corners, faces, material=material)


def validate_closed_mesh(vertices: list[Vec3], faces: list[list[int]]) -> None:
    edge_use: dict[tuple[int, int], int] = defaultdict(int)
    for face in faces:
        if len(face) < 3:
            raise ValueError("Cara inválida: menos de 3 vértices.")
        for i in range(len(face)):
            a = face[i]
            b = face[(i + 1) % len(face)]
            if a < 0 or b < 0 or a >= len(vertices) or b >= len(vertices):
                raise ValueError("Cara referencia un índice de vértice inexistente.")
            edge = (a, b) if a < b else (b, a)
            edge_use[edge] += 1

    bad = [edge for edge, count in edge_use.items() if count != 2]
    if bad:
        raise ValueError(
            f"Malla no cerrada: {len(bad)} aristas no compartidas por exactamente 2 caras."
        )

    for idx, point in enumerate(vertices):
        if any(math.isnan(c) for c in point.as_tuple()):
            raise ValueError(f"Vértice {idx} contiene NaN.")

    # Rechazar geometría degenerada (area ~0)
    for face in faces:
        a, b, c = (vertices[i] for i in face[:3])
        normal = (b - a).cross(c - a)
        if normal.length() < 1e-6:
            raise ValueError("Cara degenerada detectada en malla de volumen.")

