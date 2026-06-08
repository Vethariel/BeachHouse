#!/usr/bin/env python3
"""Recorta diagonales existentes restando copias temporales de correa y pilar."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.obj_edit import replace_objects
from model.roof.diagonal_cuts import clip_diagonals_in_obj, diagonal_links
from model.session import EditSession

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def main() -> int:
    links = diagonal_links()
    print(f"Recortando {len(links)} diagonales (copia temporal RF + pilar → sustracción en RD)…")

    replacements = clip_diagonals_in_obj(OBJ_PATH, PARTS_PATH)

    with EditSession("recorte diagonales voladizo"):
        updated = replace_objects(OBJ_PATH, replacements)
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)

    print("Diagonales actualizadas:", ", ".join(rd_id for rd_id, _, _ in links))
    print(f"Objetos reemplazados: {len(updated)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
