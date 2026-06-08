"""Peldaños de escalera (EH-*)."""

from __future__ import annotations

from dataclasses import dataclass

from model.geom import Solid, Volume
from model.stairs.beam import MAT_STAIR
from model.stairs.envelope import (
    EP001_P0,
    EP001_P1,
    EP002_P0,
    EP002_P2,
    RISER,
    RISERS_PER_FLIGHT,
    TREAD_FLIGHT1_X_EAST,
    TREAD_FLIGHT1_X_WEST,
    TREAD_FLIGHT2_X_EAST,
    TREAD_FLIGHT2_X_WEST,
    TREAD_THICK,
    Z_LANDING_TREAD_TOP,
    Z_P1_TOP,
    Z_P2_TOP,
)


@dataclass(frozen=True)
class StairTreadSpec:
    part_id: str
    solid: Solid
    material: str = MAT_STAIR


def _tread_depth_y(y0: float, y1: float, *, count: int = RISERS_PER_FLIGHT) -> float:
    return abs(y1 - y0) / count


def _tread_solid(
    *,
    x_west: float,
    x_east: float,
    y_front: float,
    y_back: float,
    z_top: float,
) -> Solid:
    y0, y1 = sorted((y_front, y_back))
    return Solid.from_volume(
        Volume.from_aabb(
            x_west,
            y0,
            z_top - TREAD_THICK,
            x_east,
            y1,
            z_top,
        )
    )


def _flight1_treads() -> list[StairTreadSpec]:
    _, y0, _ = EP001_P0
    _, y1, _ = EP001_P1
    depth = _tread_depth_y(y0, y1)
    specs: list[StairTreadSpec] = []
    for k in range(1, RISERS_PER_FLIGHT + 1):
        y_front = y0 + (y1 - y0) * (k / RISERS_PER_FLIGHT)
        z_top = Z_P1_TOP + k * RISER
        specs.append(
            StairTreadSpec(
                f"EH-{k:03d}",
                _tread_solid(
                    x_west=TREAD_FLIGHT1_X_WEST,
                    x_east=TREAD_FLIGHT1_X_EAST,
                    y_front=y_front,
                    y_back=y_front - depth,
                    z_top=z_top,
                ),
            )
        )
    return specs


def _flight2_treads() -> list[StairTreadSpec]:
    _, y0, _ = EP002_P0
    _, y1, _ = EP002_P2
    depth = _tread_depth_y(y0, y1)
    offset = RISERS_PER_FLIGHT
    specs: list[StairTreadSpec] = []
    for k in range(1, RISERS_PER_FLIGHT + 1):
        y_front = y0 + (y1 - y0) * (k / RISERS_PER_FLIGHT)
        z_top = Z_LANDING_TREAD_TOP + (k - 1) * RISER
        if k == RISERS_PER_FLIGHT:
            z_top = Z_P2_TOP
        specs.append(
            StairTreadSpec(
                f"EH-{offset + k:03d}",
                _tread_solid(
                    x_west=TREAD_FLIGHT2_X_WEST,
                    x_east=TREAD_FLIGHT2_X_EAST,
                    y_front=y_front,
                    y_back=y_front + depth,
                    z_top=z_top,
                ),
            )
        )
    return specs


def generate_treads() -> list[StairTreadSpec]:
    return _flight1_treads() + _flight2_treads()
