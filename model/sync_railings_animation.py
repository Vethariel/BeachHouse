#!/usr/bin/env python3
"""Sincroniza fases de animación de barandas (10–11) en catálogo."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.railings.catalog_helpers import RAILING_ANIMATION_PHASES, sync_all_railing_phases

BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def main() -> int:
    updated = sync_all_railing_phases()
    subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
    print("Fases de animación barandas:")
    for spec in RAILING_ANIMATION_PHASES:
        print(f"  {spec['id']} — {spec['label']} ({spec['part_id']})")
    print(f"Piezas railing actualizadas: {updated}")
    print("Modo Animación en el visor → fases 10–11 → ▶ Reproducir")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
