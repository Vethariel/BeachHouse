from __future__ import annotations

import numpy as np
import trimesh

from model.geom.mesh import mesh_to_obj_dict, validate_closed_mesh
from model.geom.types import Vec3
from model.geom.volume import Volume


def volume_to_trimesh(volume: Volume) -> trimesh.Trimesh:
    if volume.is_axis_aligned():
        x0, y0, z0, x1, y1, z1 = volume.bounds()
        extents = [x1 - x0, y1 - y0, z1 - z0]
        center = [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]
        mesh = trimesh.creation.box(extents=extents)
        mesh.apply_translation(center)
        return mesh

    vertices = np.array([point.as_tuple() for point in volume.corners], dtype=float)
    center = vertices.mean(axis=0)
    quads = [
        [0, 1, 2, 3],
        [4, 7, 6, 5],
        [0, 4, 5, 1],
        [2, 6, 7, 3],
        [1, 5, 6, 2],
        [0, 3, 7, 4],
    ]
    triangles: list[list[int]] = []
    for quad in quads:
        for tri_local in ((0, 1, 2), (0, 2, 3)):
            idx = [quad[i] for i in tri_local]
            tri_pts = vertices[idx]
            normal = np.cross(tri_pts[1] - tri_pts[0], tri_pts[2] - tri_pts[0])
            outward = vertices[quad].mean(axis=0) - center
            if np.dot(normal, outward) < 0:
                idx = idx[::-1]
            triangles.append(idx)

    mesh = trimesh.Trimesh(vertices=vertices, faces=np.array(triangles), process=False)
    if not mesh.is_volume:
        raise ValueError("No se pudo construir un volumen cerrado desde 8 esquinas.")
    return mesh


class Solid:
    """Volumen cerrado arbitrario (malla triangular)."""

    def __init__(self, vertices: list[Vec3], faces: list[list[int]]):
        if not vertices or not faces:
            raise ValueError("Un sólido requiere vértices y caras.")
        self.vertices = vertices
        self.faces = faces
        self.validate()

    @classmethod
    def from_volume(cls, volume: Volume) -> Solid:
        mesh = volume_to_trimesh(volume)
        return cls.from_trimesh(mesh)

    @classmethod
    def from_trimesh(cls, mesh: trimesh.Trimesh) -> Solid:
        vertices = [Vec3(float(x), float(y), float(z)) for x, y, z in mesh.vertices]
        faces = mesh.faces.tolist()
        return cls(vertices, faces)

    @classmethod
    def from_trimesh_relaxed(cls, mesh: trimesh.Trimesh) -> Solid:
        """Desde malla booleana sin exigir validación estricta previa."""
        mesh = mesh.copy()
        mesh.merge_vertices()
        mesh.update_faces(mesh.nondegenerate_faces())
        mesh.remove_infinite_values()
        if mesh.is_empty:
            raise ValueError("La malla booleana quedó vacía.")
        obj = cls.__new__(cls)
        obj.vertices = [Vec3(float(x), float(y), float(z)) for x, y, z in mesh.vertices]
        obj.faces = mesh.faces.tolist()
        return obj

    def validate(self) -> None:
        validate_closed_mesh(self.vertices, self.faces)

    def to_mesh(self, *, material: str, validate: bool = True) -> dict:
        if validate:
            self.validate()
        return mesh_to_obj_dict(self.vertices, self.faces, material=material)

    def to_trimesh(self, *, strict: bool = True) -> trimesh.Trimesh:
        mesh = trimesh.Trimesh(
            vertices=np.array([point.as_tuple() for point in self.vertices], dtype=float),
            faces=np.array(self.faces, dtype=int),
            process=False,
        )
        if strict and not mesh.is_volume:
            raise ValueError("El sólido no es un volumen cerrado válido para booleanos.")
        return mesh

    def bounds(self) -> tuple[float, float, float, float, float, float]:
        xs = [p.x for p in self.vertices]
        ys = [p.y for p in self.vertices]
        zs = [p.z for p in self.vertices]
        return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)
