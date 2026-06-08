#!/usr/bin/env python3
"""Fase A escalera: guía temporal TMP-ESC."""

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
from model.stairs.envelope import (
    EP001_P0,
    EP001_P1,
    EP001_P2,
    EP002_P0,
    EP002_P1,
    EP002_P2,
    RISER,
    RISERS_PER_FLIGHT,
    STAIR_GUIDE_NOTES,
    STAIR_GUIDE_PART_ID,
    X_EAST,
    X_WEST,
    Y_LANDING_NORTH,
    Y_LANDING_SOUTH,
    Y_NORTH,
    Y_SOUTH,
    Z_LANDING_TOP,
    Z_P1_TOP,
    Z_P2_TOP,
)
from model.stairs.guide import build_stair_guide_meshes

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def purge_stairs_guide() -> list[str]:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    refs = [
        part["obj_ref"]
        for part in data["parts"]
        if part.get("id") == STAIR_GUIDE_PART_ID
        or part.get("notes") == STAIR_GUIDE_NOTES
    ]
    if not refs:
        return []
    remove_objects(OBJ_PATH, set(refs))
    return refs


def assign_stairs_guide_catalog(obj_refs: list[str]) -> None:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    primary = obj_refs[0]

    for part in data["parts"]:
        if part["obj_ref"] not in obj_refs:
            continue
        part["category"] = "__temp__"
        part["phase"] = None
        part["temporary"] = True
        part["visible"] = True
        part["notes"] = STAIR_GUIDE_NOTES
        part["id"] = STAIR_GUIDE_PART_ID if part["obj_ref"] == primary else None

    data["summary"] = {
        "parts": len(data["parts"]),
        "with_id": sum(1 for p in data["parts"] if p.get("id")),
        "with_category": sum(1 for p in data["parts"] if p.get("category")),
        "with_phase": sum(1 for p in data["parts"] if p.get("phase") is not None),
        "temporary": sum(1 for p in data["parts"] if p.get("temporary")),
    }
    PARTS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def print_validation() -> None:
    print("Hueco interior (planta):")
    print(f"  X {X_WEST} … {X_EAST}   Y {Y_SOUTH} … {Y_NORTH}")
    print()
    print("Descanso ED-001:")
    print(f"  Y {Y_LANDING_SOUTH} … {Y_LANDING_NORTH}   Z top {Z_LANDING_TOP}")
    print()
    print("Patinillos guía:")
    print(f"  EP-001  {EP001_P0} → {EP001_P1} → {EP001_P2}")
    print(f"  EP-002  {EP002_P0} → {EP002_P1} → {EP002_P2}")
    print()
    print(f"Contrahuella R = {RISER:.3f} u ({RISER * 10:.1f} cm) × {RISERS_PER_FLIGHT} por tramo")
    print(f"  P1 Z={Z_P1_TOP}  →  descanso Z={Z_LANDING_TOP}  →  P2 Z={Z_P2_TOP}")


def main() -> int:
    removed = purge_stairs_guide()
    if removed:
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Reemplazada guía previa: {', '.join(removed)}")

    meshes = build_stair_guide_meshes()
    print_validation()

    with EditSession("guía escalera (fase A)"):
        obj_refs = append_objects(OBJ_PATH, meshes)
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        assign_stairs_guide_catalog(obj_refs)

    print(f"\nListo: {STAIR_GUIDE_PART_ID} ({STAIR_GUIDE_NOTES}) → {', '.join(obj_refs)}")
    print("Validar en el visor: Temporales o buscar TMP-ESC.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
