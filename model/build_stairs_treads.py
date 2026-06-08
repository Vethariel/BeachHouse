#!/usr/bin/env python3
"""Fase E: peldaños de escalera (EH-001 … EH-014)."""

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
    RISERS_PER_FLIGHT,
    TREAD_FLIGHT1_X_EAST,
    TREAD_FLIGHT1_X_WEST,
    TREAD_FLIGHT2_X_EAST,
    TREAD_FLIGHT2_X_WEST,
    TREAD_HALF_WIDTH,
    TREAD_THICK,
)
from model.stairs.treads import generate_treads

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def purge_treads() -> int:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    refs = {
        p["obj_ref"]
        for p in data["parts"]
        if str(p.get("id", "")).startswith("EH-")
    }
    if not refs:
        return 0
    remove_objects(OBJ_PATH, refs)
    return len(refs)


def print_validation() -> None:
    print(
        f"EH-* — {RISERS_PER_FLIGHT * 2} peldaños · media luz X ({TREAD_HALF_WIDTH} u) · "
        f"canto {TREAD_THICK} u"
    )
    print(
        f"  Tramo 1 (oeste): X {TREAD_FLIGHT1_X_WEST}…{TREAD_FLIGHT1_X_EAST} · "
        "EH-001…007 (pegado a EP-001)"
    )
    print(
        f"  Tramo 2 (este):  X {TREAD_FLIGHT2_X_WEST}…{TREAD_FLIGHT2_X_EAST} · "
        "EH-008…014 (pegado a EP-002)"
    )


def main() -> int:
    removed = purge_treads()
    if removed:
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Reemplazados peldaños previos: {removed} pieza(s)")

    ensure_stair_catalog_meta()
    specs = generate_treads()
    meshes = [spec.solid.to_mesh(material=spec.material) for spec in specs]
    print_validation()

    with EditSession("peldaños escalera EH-001…014 (fase E)"):
        obj_refs = append_objects(OBJ_PATH, meshes)
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        assign_stair_parts(obj_refs, specs)

    print(
        "Listo:",
        f"{specs[0].part_id}…{specs[-1].part_id} → {obj_refs[0]}…{obj_refs[-1]}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
