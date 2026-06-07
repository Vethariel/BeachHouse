#!/usr/bin/env python3
"""Regenera solo las diagonales de voladizo (RD-*)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.obj_edit import append_objects, remove_objects
from model.roof.framing import (
    DIAGONAL_PILLAR_EXTEND,
    DIAGONAL_ROOF_INSET,
    generate_roof_diagonals,
)
from model.session import EditSession

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def purge_roof_diagonals() -> int:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    refs = {
        p["obj_ref"]
        for p in data["parts"]
        if str(p.get("id", "")).startswith("RD-")
    }
    if not refs:
        return 0
    remove_objects(OBJ_PATH, refs)
    return len(refs)


def assign_diagonal_catalog(obj_refs: list[str], specs) -> None:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    meta = {ref: spec for ref, spec in zip(obj_refs, specs)}

    for part in data["parts"]:
        spec = meta.get(part["obj_ref"])
        if not spec:
            continue
        part["id"] = spec.part_id
        part["category"] = "roof"
        part["phase"] = 8
        part["temporary"] = False
        part["visible"] = True
        part["notes"] = "RD"

    data["summary"] = {
        "parts": len(data["parts"]),
        "with_id": sum(1 for p in data["parts"] if p.get("id")),
        "with_category": sum(1 for p in data["parts"] if p.get("category")),
        "with_phase": sum(1 for p in data["parts"] if p.get("phase") is not None),
        "temporary": sum(1 for p in data["parts"] if p.get("temporary")),
    }
    PARTS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    removed = purge_roof_diagonals()
    if removed:
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Eliminadas {removed} diagonales previas")

    specs = generate_roof_diagonals()
    meshes = [spec.solid.to_mesh(material=spec.material) for spec in specs]
    print(
        f"Generando {len(specs)} diagonales "
        f"(inset voladizo {DIAGONAL_ROOF_INSET} u., extensión pilar {DIAGONAL_PILLAR_EXTEND} u.)…"
    )

    with EditSession("diagonales voladizo regeneradas"):
        obj_refs = append_objects(OBJ_PATH, meshes)
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        assign_diagonal_catalog(obj_refs, specs)

    print("IDs:", ", ".join(spec.part_id for spec in specs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
