"""Baranda BR-001 — vano P2 delimitado por V2-031, V2-033, V2-034, V2-035."""

from __future__ import annotations

from model.railings.common import RailingSpec, build_railing

# Cara superior forjado P2 (V2-*)
Z_V2_TOP = 45.0
RAILING_HEIGHT = 15.0  # 1.5 m real

# Borde interior del vano (cara hacia el hueco), según catalog/parts.json
X_WEST_INNER = 11.0
X_EAST_INNER = 24.0
Y_NORTH_INNER = 0.0
Y_SOUTH_INNER = -49.5

NW = (X_WEST_INNER, Y_NORTH_INNER, Z_V2_TOP)
NE = (X_EAST_INNER, Y_NORTH_INNER, Z_V2_TOP)
SW = (X_WEST_INNER, Y_SOUTH_INNER, Z_V2_TOP)
SE = (X_EAST_INNER, Y_SOUTH_INNER, Z_V2_TOP)


def generate_br001() -> RailingSpec:
    """U interior: norte (V2-031), oeste (V2-034/035), sur (V2-033). Lado este abierto."""
    return build_railing(
        "BR-001",
        [
            [NW, NE],
            [NW, SW],
            [SW, SE],
        ],
        height=RAILING_HEIGHT,
    )
