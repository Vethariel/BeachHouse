from __future__ import annotations

from model.geom.boolean import union_volumes
from model.geom.solid import Solid
from model.geom.types import Vec3
from model.geom.volume import Volume


def volume_from_part(part: dict) -> Volume:
    """Reconstruye un Volume axis-aligned desde bounds del catálogo."""
    bounds = part.get("bounds")
    if not bounds:
        center = part["center"]
        size = part["size"]
        half = Vec3(size[0] / 2, size[1] / 2, size[2] / 2)
        center_v = Vec3(center[0], center[1], center[2])
        lo = center_v - half
        hi = center_v + half
        return Volume.from_aabb(lo.x, lo.y, lo.z, hi.x, hi.y, hi.z)

    lo = bounds["min"]
    hi = bounds["max"]
    return Volume.from_aabb(lo[0], lo[1], lo[2], hi[0], hi[1], hi[2])


def _extension_piece(volume: Volume, direction: str, length: float) -> Volume:
    if length <= 0:
        raise ValueError("La extensión debe ser mayor que cero.")

    x0, y0, z0, x1, y1, z1 = volume.bounds()
    direction = direction.lower()

    if direction == "+x":
        return Volume.from_aabb(x1, y0, z0, x1 + length, y1, z1)
    if direction == "-x":
        return Volume.from_aabb(x0 - length, y0, z0, x0, y1, z1)
    if direction == "+y":
        return Volume.from_aabb(x0, y1, z0, x1, y1 + length, z1)
    if direction == "-y":
        return Volume.from_aabb(x0, y0 - length, z0, x1, y0, z1)
    if direction == "+z":
        return Volume.from_aabb(x0, y0, z1, x1, y1, z1 + length)
    if direction == "-z":
        return Volume.from_aabb(x0, y0, z0 - length, x1, y1, z0)

    raise ValueError(f"Dirección de extensión inválida: {direction!r}")


def extend_volume(volume: Volume, *, direction: str = "+z", length: float) -> Solid:
    """Extiende un volumen existente y devuelve un único sólido unificado.

    Equivalente a extruir la cara del extremo en `direction` y unirla al original.
    Por ahora requiere volumen alineado a ejes (pilares, vigas, etc.).
    """
    if not volume.is_axis_aligned():
        raise ValueError("extend_volume requiere un volumen alineado a ejes.")

    piece = _extension_piece(volume, direction, length)
    return union_volumes(volume, piece)[0]


def extend_volume_to(
    volume: Volume,
    *,
    x: float | None = None,
    y: float | None = None,
    z: float | None = None,
) -> Solid:
    """Extiende el volumen hacia +X, +Y o +Z hasta alcanzar la coordenada indicada."""
    if not volume.is_axis_aligned():
        raise ValueError("extend_volume_to requiere un volumen alineado a ejes.")

    solid = Solid.from_volume(volume)
    bounds = solid.bounds()

    if x is not None and x > bounds[3]:
        solid = extend_volume(Volume.from_aabb(*bounds), direction="+x", length=x - bounds[3])
        bounds = solid.bounds()
    if y is not None and y > bounds[4]:
        solid = extend_volume(Volume.from_aabb(*bounds), direction="+y", length=y - bounds[4])
        bounds = solid.bounds()
    if z is not None and z > bounds[5]:
        solid = extend_volume(Volume.from_aabb(*bounds), direction="+z", length=z - bounds[5])

    return solid
