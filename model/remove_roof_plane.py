#!/usr/bin/env python3
"""Elimina el plano guía temporal de cubierta (TMP-RPL)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.build_roof_plane import purge_roof_plane
from model.roof.plane import ROOF_PART_ID
from model.session import EditSession

BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def main() -> int:
    with EditSession("eliminar plano guía cubierta (TMP-RPL)"):
        removed = purge_roof_plane()
        if not removed:
            print(f"{ROOF_PART_ID} no estaba en el modelo.")
            return 0
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Eliminado {ROOF_PART_ID} ({removed})")

    print("Fase 8 (cubierta) lista para animar en el visor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
