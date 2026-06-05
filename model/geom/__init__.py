"""Geometry primitives: temporary planes and solid volumes."""

from model.geom.boolean import (
    ensure_closed_solids,
    ensure_closed_volumes,
    intersect_volumes,
    subtract_volumes,
    union_volumes,
)
from model.geom.extend import extend_volume, extend_volume_to, volume_from_part
from model.geom.mesh import mesh_to_obj_dict, validate_closed_mesh
from model.geom.plane import PlaneGuide
from model.geom.solid import Solid
from model.geom.types import Vec3
from model.geom.volume import Volume

__all__ = [
    "Vec3",
    "PlaneGuide",
    "Volume",
    "Solid",
    "mesh_to_obj_dict",
    "validate_closed_mesh",
    "union_volumes",
    "subtract_volumes",
    "intersect_volumes",
    "ensure_closed_solids",
    "ensure_closed_volumes",
    "extend_volume",
    "extend_volume_to",
    "volume_from_part",
]
