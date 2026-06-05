from __future__ import annotations

from model.geom.mesh import plane_mesh, validate_closed_mesh
from model.geom.types import Vec3


class PlaneGuide:
    """Plano temporal de construcción definido por 4 puntos."""

    def __init__(self, p0: Vec3, p1: Vec3, p2: Vec3, p3: Vec3, *, label: str = ""):
        self.points = (p0, p1, p2, p3)
        self.label = label
        self._validate()

    def _validate(self) -> None:
        pts = self.points
        if len({p.as_tuple() for p in pts}) < 4:
            raise ValueError("Un plano requiere 4 puntos distintos.")
        normal = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        if normal.length() < 1e-6:
            raise ValueError("Los 4 puntos del plano son colineales o degenerados.")
        for p in pts[3:]:
            if abs((p - pts[0]).dot(normal.normalized())) > 1e-3:
                raise ValueError("Los 4 puntos no son coplanares.")

    def to_mesh(self, *, material: str) -> dict:
        return plane_mesh(list(self.points), material=material)
