"""Baranda BR-002 — vano P1 delimitado por V1-004, 016, 024, 029, 034 y 040."""

from __future__ import annotations

from model.railings.common import RailingSpec, build_railing

# Cara superior forjado P1 (V1-*)
Z_V1_TOP = 14.0
RAILING_HEIGHT = 15.0  # 1.5 m real

# Borde interior del vano (cara hacia el hueco), según catalog/parts.json
X_WEST_INNER = 0.0
X_EAST_INNER = 24.0
Y_NORTH_INNER = 0.0
Y_SOUTH_INNER = -100.0

NW = (X_WEST_INNER, Y_NORTH_INNER, Z_V1_TOP)
NE = (X_EAST_INNER, Y_NORTH_INNER, Z_V1_TOP)
SW = (X_WEST_INNER, Y_SOUTH_INNER, Z_V1_TOP)
SE = (X_EAST_INNER, Y_SOUTH_INNER, Z_V1_TOP)


def generate_br002() -> RailingSpec:
    """U interior: norte (V1-004), oeste (V1-024/029/034/040), sur (V1-016). Lado este abierto."""
    return build_railing(
        "BR-002",
        [
            [NW, NE],
            [NW, SW],
            [SW, SE],
        ],
        height=RAILING_HEIGHT,
    )
