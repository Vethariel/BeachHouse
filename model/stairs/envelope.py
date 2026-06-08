"""Hueco de escalera y cotas — docs/plan-escaleras.md."""

from __future__ import annotations

STAIR_GUIDE_PART_ID = "TMP-ESC"
STAIR_GUIDE_NOTES = "demo:stairs-guide"
MAT_STAIRS_GUIDE = "color_temp_plane"
MAT_STAIRS_GUIDE_VOLUME = "color_temp_volume"

# Interior entre caras de pilares 8, 9, 13, 14
X_WEST = 61.0
X_EAST = 76.0
Y_NORTH = -26.0
Y_SOUTH = -49.0

# Descanso (1.0 m); borde norte pegado al interior del hueco / viga de medio
Y_LANDING_SOUTH = -36.0
Y_LANDING_NORTH = Y_NORTH  # −26.0 — contacto con zona EM-001

# Viga de medio (EM-001)
Y_MID_BEAM = -25.0
MID_BEAM_HALF_Y = 0.5

# Cotas verticales
Z_P1_TOP = 17.5
Z_P2_TOP = 45.0
Z_LANDING_TOP = 31.25  # huella EH-007 (fin tramo 1)

# Métricas de comodidad
RISERS_PER_FLIGHT = 7
RISER = 13.75 / RISERS_PER_FLIGHT  # ≈ 1.964 u

# Cotas descanso / rellano (cara superior = EH-008, mismo grosor que peldaño)
Z_LANDING_TREAD_TOP = Z_LANDING_TOP + RISER
Z_LANDING_SLAB_TOP = Z_LANDING_TREAD_TOP
Z_EM_TOP = Z_LANDING_SLAB_TOP

# Patinillos guía (EP-001, EP-002)
EP_WEST_X = X_WEST
EP_EAST_X = X_EAST

# EP-002 — bifurcación en borde sur del descanso (P0), espejo de EP-001 en P1
EP002_P0 = (EP_EAST_X, Y_LANDING_SOUTH, Z_LANDING_SLAB_TOP)  # horiz. + oblicuo
EP002_P1 = (EP_EAST_X, Y_LANDING_NORTH, Z_LANDING_SLAB_TOP)  # fin recto descanso
EP002_P2 = (EP_EAST_X, Y_SOUTH, Z_P2_TOP - 0.01)  # fin oblicuo
EP002_P3 = (EP_EAST_X, Y_SOUTH, Z_P2_TOP)  # empalme V2-014

EP001_P0 = (EP_WEST_X, Y_SOUTH, Z_P1_TOP)

EP001_P1 = (EP_WEST_X, Y_LANDING_SOUTH, Z_LANDING_SLAB_TOP)
EP001_P2 = (EP_WEST_X, Y_LANDING_NORTH, Z_LANDING_SLAB_TOP)

# Peldaños (EH-*) — media luz del hueco, pegados al patinillo de cada tramo
STRINGER_WIDTH = 1.0
TREAD_HALF_WIDTH = (X_EAST - X_WEST) / 2.0
TREAD_FLIGHT1_X_WEST = X_WEST
TREAD_FLIGHT1_X_EAST = X_WEST + TREAD_HALF_WIDTH
TREAD_FLIGHT2_X_WEST = X_WEST + TREAD_HALF_WIDTH
TREAD_FLIGHT2_X_EAST = X_EAST
TREAD_THICK = 0.25

GUIDE_LINE_WIDTH = 0.2
