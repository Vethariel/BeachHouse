#!/usr/bin/env python3
"""Fase B1: volumen temporal de sustracción sobre el plano (TMP-RSV)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.obj_edit import append_objects, remove_objects
from model.roof.plane import (
    MAT_ROOF_SUBTRACT,
    ROOF_SUBTRACT_NOTES,
    ROOF_SUBTRACT_PART_ID,
    Z_CUT_TOP,
    build_roof_above_volume,
    build_roof_plane_guide,
    pillar_extend_z,
    roof_plane_max_z,
)
from model.session import EditSession

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def purge_roof_subtract_volume() -> str | None:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    for part in data["parts"]:
        if part.get("id") == ROOF_SUBTRACT_PART_ID:
            ref = part["obj_ref"]
            remove_objects(OBJ_PATH, {ref})
            return ref
    return None


def assign_roof_subtract_catalog(obj_ref: str) -> None:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    for part in data["parts"]:
        if part["obj_ref"] != obj_ref:
            continue
        part["id"] = ROOF_SUBTRACT_PART_ID
        part["category"] = "__temp__"
        part["phase"] = None
        part["temporary"] = True
        part["visible"] = True
        part["notes"] = ROOF_SUBTRACT_NOTES
        break
    else:
        raise RuntimeError(f"obj_ref no encontrado tras rebuild: {obj_ref}")

    data["summary"] = {
        "parts": len(data["parts"]),
        "with_id": sum(1 for p in data["parts"] if p.get("id")),
        "with_category": sum(1 for p in data["parts"] if p.get("category")),
        "with_phase": sum(1 for p in data["parts"] if p.get("phase") is not None),
        "temporary": sum(1 for p in data["parts"] if p.get("temporary")),
    }
    PARTS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def print_validation(solid) -> None:
    plane = build_roof_plane_guide()
    print("Plano base (TMP-RPL) — vértices:")
    for i, p in enumerate(plane.points):
        print(f"  P{i} = ({p.x:.2f}, {p.y:.2f}, {p.z:.2f})")
    print()
    print("Volumen de sustracción:")
    print(f"  Tope Z = {Z_CUT_TOP:.1f} u")
    print(f"  z máximo plano = {roof_plane_max_z():.2f} u")
    print(f"  z extensión pilares (B2) = {pillar_extend_z():.2f} u")
    bounds = solid.bounds()
    print(f"  Bounds Z = [{bounds[2]:.2f}, {bounds[5]:.2f}]")


def main() -> int:
    removed = purge_roof_subtract_volume()
    if removed:
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Reemplazado {ROOF_SUBTRACT_PART_ID} previo ({removed})")

    solid = build_roof_above_volume()
    mesh = solid.to_mesh(material=MAT_ROOF_SUBTRACT)
    print_validation(solid)

    with EditSession("volumen sustracción cubierta (fase B1)"):
        obj_refs = append_objects(OBJ_PATH, [mesh])
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        assign_roof_subtract_catalog(obj_refs[0])

    print(f"\nListo: {ROOF_SUBTRACT_PART_ID} ({ROOF_SUBTRACT_NOTES}) → {obj_refs[0]}")
    print("Validar en el visor junto a TMP-RPL (Temporales).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
