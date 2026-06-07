#!/usr/bin/env python3
"""Fase C: entramado de cubierta (RF-*)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.obj_edit import append_objects, remove_objects
from model.roof.framing import generate_roof_framing
from model.roof.plane import ROOF_SUBTRACT_PART_ID
from model.session import EditSession

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
CATEGORIES_PATH = ROOT / "catalog/categories.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def purge_roof_framing() -> int:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    refs = {p["obj_ref"] for p in data["parts"] if p.get("category") == "roof"}
    if not refs:
        return 0
    remove_objects(OBJ_PATH, refs)
    return len(refs)


def purge_temp_subtract() -> str | None:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    for part in data["parts"]:
        if part.get("id") == ROOF_SUBTRACT_PART_ID:
            ref = part["obj_ref"]
            remove_objects(OBJ_PATH, {ref})
            return ref
    return None


def ensure_phase_8() -> None:
    data = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))
    phases = data.get("phases", [])
    if not any(p.get("id") == 8 for p in phases):
        phases.append(
            {
                "id": 8,
                "label": "Entramado — cubierta",
                "category": "roof",
                "animation": "fall",
                "phase_duration_ms": 3000,
                "fall_height": 120,
            }
        )
        data["phases"] = phases
        CATEGORIES_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def assign_roof_catalog(obj_refs: list[str], specs) -> None:
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
        part["notes"] = spec.part_id.split("-")[0]

    data["summary"] = {
        "parts": len(data["parts"]),
        "with_id": sum(1 for p in data["parts"] if p.get("id")),
        "with_category": sum(1 for p in data["parts"] if p.get("category")),
        "with_phase": sum(1 for p in data["parts"] if p.get("phase") is not None),
        "temporary": sum(1 for p in data["parts"] if p.get("temporary")),
    }
    PARTS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    removed_roof = purge_roof_framing()
    if removed_roof:
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Eliminado entramado previo: {removed_roof} piezas")

    removed_rsv = purge_temp_subtract()
    if removed_rsv:
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Eliminado {ROOF_SUBTRACT_PART_ID} ({removed_rsv})")

    ensure_phase_8()
    specs = generate_roof_framing()
    meshes = [spec.solid.to_mesh(material=spec.material) for spec in specs]
    rf = sum(1 for s in specs if s.part_id.startswith("RF-"))
    rj = sum(1 for s in specs if s.part_id.startswith("RJ-"))
    rd = sum(1 for s in specs if s.part_id.startswith("RD-"))
    print(f"Generando entramado: {rf} correas/vigas, {rj} viguetas, {rd} diagonales…")

    with EditSession("entramado cubierta (fase C)"):
        obj_refs = append_objects(OBJ_PATH, meshes)
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        assign_roof_catalog(obj_refs, specs)

    print("IDs:", ", ".join(spec.part_id for spec in specs[:3]), "…", specs[-1].part_id)
    print(f"Total cubierta: {len(specs)} (RF {rf} · RJ {rj} · RD {rd}) · fase 8 activa")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
