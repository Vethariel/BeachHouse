"""Roof reference plane per docs/plan-cubierta.md."""

from __future__ import annotations

from model.geom import PlaneGuide, Solid, Vec3, Volume

ROOF_PART_ID = "TMP-RPL"
ROOF_NOTES = "demo:roof-plane"
MAT_ROOF_PLANE = "color_temp_plane"

ROOF_SUBTRACT_PART_ID = "TMP-RSV"
ROOF_SUBTRACT_NOTES = "demo:roof-subtract"
MAT_ROOF_SUBTRACT = "color_temp_subtract"

# Extensión de pilares (§5): margen sobre el punto más alto del plano
Z_EXTEND_MARGIN = 5.0
Z_CUT_TOP = 120.0

# Reference columns (PIL-021 high, PIL-024 low)
X_HIGH = 25.0
X_LOW = 98.0
Z_AT_HIGH = 85.0
Z_AT_LOW = 70.0

# Voladizos: 2 m real = 20 u (ambos extremos en X)
OVERHANG = 20.0
X_MIN = X_HIGH - OVERHANG
X_MAX = X_LOW + OVERHANG
# Planta Y: filas de pilares en centros 0 … −100; sección 2×2 → ±1 u al borde
PILLAR_HALF_Y = 1.0
Y_ROW_MAX = 0.0
Y_ROW_MIN = -100.0
Y_MAX = Y_ROW_MAX + PILLAR_HALF_Y
Y_MIN = Y_ROW_MIN - PILLAR_HALF_Y

RISE = Z_AT_HIGH - Z_AT_LOW
RUN = X_LOW - X_HIGH


def roof_z_at(x: float) -> float:
    """Cota Z del plano de cubierta en la coordenada X dada."""
    return Z_AT_LOW + RISE * (X_LOW - x) / RUN


def build_roof_plane_guide() -> PlaneGuide:
    """Cuadrilátero coplanar CCW visto desde +Z (con voladizos en X)."""
    z0 = roof_z_at(X_MIN)
    z1 = roof_z_at(X_MAX)
    return PlaneGuide(
        Vec3(X_MIN, Y_MAX, z0),
        Vec3(X_MAX, Y_MAX, z1),
        Vec3(X_MAX, Y_MIN, z1),
        Vec3(X_MIN, Y_MIN, z0),
        label="plano cubierta",
    )


def roof_plane_max_z() -> float:
    return max(point.z for point in build_roof_plane_guide().points)


def pillar_extend_z() -> float:
    """Cota común +Z para extender pilares antes del corte (Fase B2)."""
    return roof_plane_max_z() + Z_EXTEND_MARGIN


def build_roof_above_volume(*, z_top: float = Z_CUT_TOP) -> Solid:
    """Prisma sobre el plano de cubierta: material por encima de TMP-RPL hasta z_top."""
    p0, p1, p2, p3 = build_roof_plane_guide().points
    # Orden Volume: 0-3 base (y0→y1), 4-7 tapa; mapeo P3,P2,P1,P0 desde CCW del plano
    bottom = [p3, p2, p1, p0]
    top = [Vec3(p.x, p.y, z_top) for p in bottom]
    return Solid.from_volume(Volume(bottom + top))
