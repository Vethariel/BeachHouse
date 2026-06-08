#!/usr/bin/env python3
"""Baranda BR-001 — vano P2 (V2-031, V2-033, V2-034, V2-035)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.obj_edit import append_objects, remove_objects
from model.railings.catalog_helpers import assign_railing_parts, ensure_railing_catalog_meta
from model.railings.v2_opening_west import (
    NE,
    NW,
    RAILING_HEIGHT,
    SE,
    SW,
    generate_br001,
)
from model.session import EditSession

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def purge_railing(part_id: str) -> int:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    refs = {p["obj_ref"] for p in data["parts"] if p.get("id") == part_id}
    if not refs:
        return 0
    remove_objects(OBJ_PATH, refs)
    return len(refs)


def main() -> int:
    removed = purge_railing("BR-001")
    if removed:
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Reemplazada baranda previa: {removed} pieza(s)")

    ensure_railing_catalog_meta()
    spec = generate_br001()
    mesh = spec.solid.to_mesh(material=spec.material, validate=False)

    print("BR-001 — vano P2 (V2-031/033/034/035):")
    print(f"  Altura {RAILING_HEIGHT} u (1.5 m) sobre forjado Z=45")
    print(f"  Norte  {NW} → {NE}")
    print(f"  Oeste  {NW} → {SW}")
    print(f"  Sur    {SW} → {SE}  (este del vano sin baranda)")

    with EditSession("baranda BR-001 vano P2 V2-031/033/034/035"):
        obj_refs = append_objects(OBJ_PATH, [mesh])
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        assign_railing_parts(obj_refs, [spec])

    print(f"Listo: {spec.part_id} → {obj_refs[0]} · categoría railing · fase 13")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
