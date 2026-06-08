#!/usr/bin/env python3
"""Sincroniza fase de animación de la escalera (9) en catálogo."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.stairs.catalog_helpers import STAIR_ANIMATION_PHASES, sync_all_stair_phases

BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def main() -> int:
    updated = sync_all_stair_phases()
    subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
    print("Fases de animación escalera:")
    for spec in STAIR_ANIMATION_PHASES:
        print(f"  {spec['id']} — {spec['label']}")
    print(f"Piezas stair actualizadas: {updated}")
    print("Modo Animación en el visor → fase 9 → ▶ Reproducir")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
