#!/usr/bin/env python3
"""Fase B1: viga de medio de escalera (EM-001)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.obj_edit import append_objects, remove_objects
from model.session import EditSession
from model.stairs.catalog_helpers import assign_stair_parts, ensure_stair_catalog_meta
from model.stairs.beam import generate_mid_beam
from model.stairs.envelope import (
    X_EAST,
    X_WEST,
    Y_MID_BEAM,
    Z_EM_TOP,
    Z_LANDING_TOP,
)

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def purge_mid_beams() -> int:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    refs = {
        p["obj_ref"]
        for p in data["parts"]
        if str(p.get("id", "")).startswith("EM-")
    }
    if not refs:
        return 0
    remove_objects(OBJ_PATH, refs)
    return len(refs)


def print_validation() -> None:
    print("EM-001 — viga de medio:")
    print(f"  X {X_WEST} … {X_EAST}  (15 u)")
    print(f"  Y {Y_MID_BEAM - 0.5} … {Y_MID_BEAM + 0.5}  (1 u)")
    print(f"  Z {Z_LANDING_TOP} … {Z_EM_TOP}  (canto {Z_EM_TOP - Z_LANDING_TOP} u)")


def main() -> int:
    removed = purge_mid_beams()
    if removed:
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Reemplazada viga previa: {removed} pieza(s)")

    ensure_stair_catalog_meta()
    specs = generate_mid_beam()
    meshes = [spec.solid.to_mesh(material=spec.material) for spec in specs]
    print_validation()

    with EditSession("viga medio escalera EM-001 (fase B1)"):
        obj_refs = append_objects(OBJ_PATH, meshes)
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        assign_stair_parts(obj_refs, specs)

    print(f"Listo: {specs[0].part_id} → {obj_refs[0]} · categoría stair · fase 9")
    print("TMP-ESC sigue visible como referencia; ocultá Temporales para ver solo EM-001.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
