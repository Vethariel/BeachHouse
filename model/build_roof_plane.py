#!/usr/bin/env python3
"""Fase A: plano guía temporal de cubierta (TMP-RPL)."""

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
    MAT_ROOF_PLANE,
    ROOF_NOTES,
    ROOF_PART_ID,
    X_HIGH,
    X_LOW,
    X_MAX,
    X_MIN,
    Z_AT_HIGH,
    Z_AT_LOW,
    build_roof_plane_guide,
    roof_z_at,
)
from model.session import EditSession

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def purge_roof_plane() -> str | None:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    for part in data["parts"]:
        if part.get("id") == ROOF_PART_ID:
            ref = part["obj_ref"]
            remove_objects(OBJ_PATH, {ref})
            return ref
    return None


def assign_roof_plane_catalog(obj_ref: str) -> None:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    for part in data["parts"]:
        if part["obj_ref"] != obj_ref:
            continue
        part["id"] = ROOF_PART_ID
        part["category"] = "__temp__"
        part["phase"] = None
        part["temporary"] = True
        part["visible"] = True
        part["notes"] = ROOF_NOTES
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


def print_validation(plane) -> None:
    pts = plane.points
    print("Vértices del plano (CCW desde +Z):")
    for i, p in enumerate(pts):
        print(f"  P{i} = ({p.x:.2f}, {p.y:.2f}, {p.z:.2f})")
    print()
    print("Cotas de referencia:")
    print(f"  PIL-021  x={X_HIGH:.0f}  z={roof_z_at(X_HIGH):.2f}  (objetivo {Z_AT_HIGH})")
    print(f"  PIL-024  x={X_LOW:.0f}  z={roof_z_at(X_LOW):.2f}  (objetivo {Z_AT_LOW})")
    print(f"  Voladizo x={X_MIN:.0f}  z={roof_z_at(X_MIN):.2f}")
    print(f"  Voladizo x={X_MAX:.0f}  z={roof_z_at(X_MAX):.2f}")


def main() -> int:
    removed = purge_roof_plane()
    if removed:
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Reemplazado {ROOF_PART_ID} previo ({removed})")

    plane = build_roof_plane_guide()
    mesh = plane.to_mesh(material=MAT_ROOF_PLANE)
    print_validation(plane)

    with EditSession("plano guía cubierta (fase A)"):
        obj_refs = append_objects(OBJ_PATH, [mesh])
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        assign_roof_plane_catalog(obj_refs[0])

    print(f"\nListo: {ROOF_PART_ID} ({ROOF_NOTES}) → {obj_refs[0]}")
    print("Validar en el visor: filtro Temporales o buscar TMP-RPL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
