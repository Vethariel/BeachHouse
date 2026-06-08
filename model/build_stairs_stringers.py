#!/usr/bin/env python3
"""Fase B2: patinillos de escalera (EP-001, EP-002)."""

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
    EP001_P0,
    EP001_P1,
    EP001_P2,
    EP002_P0,
    EP002_P1,
    EP002_P2,
    EP002_P3,
)
from model.stairs.stringer import STRINGER_DEPTH, STRINGER_WIDTH, generate_stringers

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def purge_stringers() -> int:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    refs = {
        p["obj_ref"]
        for p in data["parts"]
        if str(p.get("id", "")).startswith("EP-")
    }
    if not refs:
        return 0
    remove_objects(OBJ_PATH, refs)
    return len(refs)


def print_validation() -> None:
    print(f"Patinillos {STRINGER_WIDTH}×{STRINGER_DEPTH} u. (oblicuo + recto por pieza):")
    print(f"  EP-001  {EP001_P0} → {EP001_P1} → {EP001_P2}")
    print(f"  EP-002  recto {EP002_P0} → {EP002_P1}")
    print(f"          oblicuo {EP002_P0} → {EP002_P2} → {EP002_P3}")


def main() -> int:
    removed = purge_stringers()
    if removed:
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Reemplazados patinillos previos: {removed} pieza(s)")

    ensure_stair_catalog_meta()
    specs = generate_stringers()
    meshes = [spec.solid.to_mesh(material=spec.material) for spec in specs]
    print_validation()

    with EditSession("patinillos escalera EP-001/002 (fase B2)"):
        obj_refs = append_objects(OBJ_PATH, meshes)
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        assign_stair_parts(obj_refs, specs)

    print("Listo:", ", ".join(f"{spec.part_id} → {ref}" for spec, ref in zip(specs, obj_refs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
