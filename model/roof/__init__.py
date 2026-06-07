"""Roof modeling helpers (plane, framing, pillar targets)."""

from model.roof.framing import MAT_ROOF_FRAMING, generate_roof_framing
from model.roof.plane import (
    MAT_ROOF_PLANE,
    MAT_ROOF_SUBTRACT,
    ROOF_NOTES,
    ROOF_PART_ID,
    ROOF_SUBTRACT_NOTES,
    ROOF_SUBTRACT_PART_ID,
    Z_CUT_TOP,
    Z_EXTEND_MARGIN,
    build_roof_above_volume,
    build_roof_plane_guide,
    pillar_extend_z,
    roof_plane_max_z,
    roof_z_at,
)

__all__ = [
    "MAT_ROOF_PLANE",
    "MAT_ROOF_SUBTRACT",
    "ROOF_NOTES",
    "ROOF_PART_ID",
    "ROOF_SUBTRACT_NOTES",
    "ROOF_SUBTRACT_PART_ID",
    "Z_CUT_TOP",
    "Z_EXTEND_MARGIN",
    "build_roof_above_volume",
    "build_roof_plane_guide",
    "pillar_extend_z",
    "roof_plane_max_z",
    "roof_z_at",
]
