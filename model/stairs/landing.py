"""Descanso de escalera (ED-*)."""

from __future__ import annotations

from dataclasses import dataclass

from model.geom import Solid, Volume
from model.stairs.beam import MAT_STAIR
from model.stairs.envelope import (
    TREAD_THICK,
    X_EAST,
    X_WEST,
    Y_LANDING_NORTH,
    Y_LANDING_SOUTH,
    Z_LANDING_TREAD_TOP,
)

LANDING_CANTO_Z = TREAD_THICK


@dataclass(frozen=True)
class StairLandingSpec:
    part_id: str
    solid: Solid
    material: str = MAT_STAIR


def landing_solid() -> Solid:
    """ED-001: rellano de giro; cara superior alineada con EH-008."""
    return Solid.from_volume(
        Volume.from_aabb(
            X_WEST,
            Y_LANDING_SOUTH,
            Z_LANDING_TREAD_TOP - TREAD_THICK,
            X_EAST,
            Y_LANDING_NORTH,
            Z_LANDING_TREAD_TOP,
        )
    )


def generate_landing() -> list[StairLandingSpec]:
    return [StairLandingSpec("ED-001", landing_solid())]
