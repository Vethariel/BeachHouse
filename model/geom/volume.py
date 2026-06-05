from __future__ import annotations

from model.geom.mesh import validate_closed_mesh, volume_mesh
from model.geom.types import Vec3


class Volume:
    """Paralelepípedo definido por 8 esquinas.

    Orden esperado (base inferior, sentido horario, luego superior):
      0-3: z baja · 4-7: z alta
      0:(x0,y0,z0) 1:(x1,y0,z0) 2:(x1,y1,z0) 3:(x0,y1,z0)
      4-7: mismas x,y con z alta
    """

    def __init__(self, corners: list[Vec3]):
        if len(corners) != 8:
            raise ValueError("Un volumen requiere exactamente 8 vértices.")
        self.corners = corners
        self._validate()

    @classmethod
    def from_aabb(
        cls,
        x0: float,
        y0: float,
        z0: float,
        x1: float,
        y1: float,
        z1: float,
    ) -> Volume:
        xa, xb = sorted((x0, x1))
        ya, yb = sorted((y0, y1))
        za, zb = sorted((z0, z1))
        return cls(
            [
                Vec3(xa, ya, za),
                Vec3(xb, ya, za),
                Vec3(xb, yb, za),
                Vec3(xa, yb, za),
                Vec3(xa, ya, zb),
                Vec3(xb, ya, zb),
                Vec3(xb, yb, zb),
                Vec3(xa, yb, zb),
            ]
        )

    def bounds(self) -> tuple[float, float, float, float, float, float]:
        xs = [p.x for p in self.corners]
        ys = [p.y for p in self.corners]
        zs = [p.z for p in self.corners]
        return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)

    def is_axis_aligned(self, tol: float = 1e-4) -> bool:
        c = self.corners
        edges = [
            c[1] - c[0],
            c[2] - c[1],
            c[4] - c[0],
        ]
        for edge in edges:
            nonzero = sum(abs(v) > tol for v in edge.as_tuple())
            if nonzero != 1:
                return False
        return True

    def as_aabb(self) -> Volume:
        x0, y0, z0, x1, y1, z1 = self.bounds()
        return Volume.from_aabb(x0, y0, z0, x1, y1, z1)

    def _validate(self) -> None:
        c = self.corners
        edges = [
            (c[0], c[1]),
            (c[1], c[2]),
            (c[2], c[3]),
            (c[3], c[0]),
            (c[4], c[5]),
            (c[5], c[6]),
            (c[6], c[7]),
            (c[7], c[4]),
            (c[0], c[4]),
            (c[1], c[5]),
            (c[2], c[6]),
            (c[3], c[7]),
        ]
        lengths = [(b - a).length() for a, b in edges[:4]]
        if min(lengths) < 1e-6:
            raise ValueError("Volumen degenerado: base con arista nula.")
        for i in range(4):
            vertical = c[i + 4] - c[i]
            if vertical.length() < 1e-6:
                raise ValueError("Volumen degenerado: altura nula.")

    def to_mesh(self, *, material: str) -> dict:
        mesh = volume_mesh(self.corners, material=material)
        validate_closed_mesh(self.corners, mesh["faces_local"])
        return mesh

    def translated(self, offset: Vec3) -> Volume:
        return Volume([point + offset for point in self.corners])
