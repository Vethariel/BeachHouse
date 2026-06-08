#!/usr/bin/env python3
"""Fase D: descanso de escalera (ED-001)."""

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
from model.stairs.envelope import (
    TREAD_THICK,
    X_EAST,
    X_WEST,
    Y_LANDING_NORTH,
    Y_LANDING_SOUTH,
    Z_LANDING_TREAD_TOP,
)
from model.stairs.landing import LANDING_CANTO_Z, generate_landing

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def purge_landings() -> int:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    refs = {
        p["obj_ref"]
        for p in data["parts"]
        if str(p.get("id", "")).startswith("ED-")
    }
    if not refs:
        return 0
    remove_objects(OBJ_PATH, refs)
    return len(refs)


def print_validation() -> None:
    depth = Y_LANDING_NORTH - Y_LANDING_SOUTH
    width = X_EAST - X_WEST
    print("ED-001 — descanso:")
    print(f"  X {X_WEST} … {X_EAST}  ({width} u)")
    print(f"  Y {Y_LANDING_SOUTH} … {Y_LANDING_NORTH}  ({depth} u)")
    print(
        f"  Z {Z_LANDING_TREAD_TOP - TREAD_THICK} … {Z_LANDING_TREAD_TOP}  "
        f"(canto {TREAD_THICK} u · cara superior = EH-008 · borde norte pegado a EM-001)"
    )


def main() -> int:
    removed = purge_landings()
    if removed:
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Reemplazado descanso previo: {removed} pieza(s)")

    ensure_stair_catalog_meta()
    specs = generate_landing()
    meshes = [spec.solid.to_mesh(material=spec.material) for spec in specs]
    print_validation()

    with EditSession("descanso escalera ED-001 (fase D)"):
        obj_refs = append_objects(OBJ_PATH, meshes)
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        assign_stair_parts(obj_refs, specs)

    print(f"Listo: {specs[0].part_id} → {obj_refs[0]} · categoría stair · fase 9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
