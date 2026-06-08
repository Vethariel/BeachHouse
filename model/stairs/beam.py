"""Viga de medio de escalera (EM-*)."""

from __future__ import annotations

from dataclasses import dataclass

from model.geom import Solid, Volume
from model.stairs.envelope import (
    MID_BEAM_HALF_Y,
    X_EAST,
    X_WEST,
    Y_MID_BEAM,
    Z_EM_TOP,
    Z_LANDING_TOP,
)

MAT_STAIR = "color_stair"
MID_BEAM_WIDTH_Y = MID_BEAM_HALF_Y * 2.0
MID_BEAM_CANTO_Z = Z_EM_TOP - Z_LANDING_TOP


@dataclass(frozen=True)
class StairBeamSpec:
    part_id: str
    solid: Solid
    material: str = MAT_STAIR


def mid_beam_solid() -> Solid:
    """EM-001: viga entre PIL-008 y PIL-009 (misma sección que V1-007)."""
    return Solid.from_volume(
        Volume.from_aabb(
            X_WEST,
            Y_MID_BEAM - MID_BEAM_HALF_Y,
            Z_LANDING_TOP,
            X_EAST,
            Y_MID_BEAM + MID_BEAM_HALF_Y,
            Z_EM_TOP,
        )
    )


def generate_mid_beam() -> list[StairBeamSpec]:
    return [StairBeamSpec("EM-001", mid_beam_solid())]
