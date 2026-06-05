#!/usr/bin/env python3
"""Generate temporary demo geometries to validate planes, volumes and booleans."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.geom import (
    PlaneGuide,
    Solid,
    Vec3,
    Volume,
    ensure_closed_solids,
    extend_volume,
    intersect_volumes,
    subtract_volumes,
    union_volumes,
    volume_from_part,
)
from model.obj_edit import append_objects, remove_objects
from model.session import EditSession

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"

MAT_PLANE = "color_temp_plane"
MAT_VOLUME = "color_temp_volume"
MAT_RESULT = "color_temp_result"

ORIGIN = Vec3(115.0, 15.0, 50.0)
LANE_Y = 12.0


def _lane(index: int) -> Vec3:
    return Vec3(ORIGIN.x, ORIGIN.y + index * LANE_Y, ORIGIN.z)


def _boolean_spec(solid: Solid, part_id: str, notes: str) -> dict:
    return {
        "id": part_id,
        "temporary": True,
        "notes": notes,
        "mesh": solid.to_mesh(material=MAT_RESULT),
    }


def purge_temporary() -> int:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    refs = {part["obj_ref"] for part in data["parts"] if part.get("category") == "__temp__"}
    if not refs:
        return 0
    remove_objects(OBJ_PATH, refs)
    return len(refs)


def build_demo_specs() -> list[dict]:
    specs: list[dict] = []

    lane = _lane(0)
    plane = PlaneGuide(
        lane,
        lane + Vec3(10, 0, 0),
        lane + Vec3(8, 6, 4),
        lane + Vec3(-2, 6, 4),
        label="plano guía",
    )
    specs.append(
        {
            "id": "TMP-P01",
            "temporary": True,
            "notes": "demo:plane",
            "mesh": plane.to_mesh(material=MAT_PLANE),
        }
    )

    lane = _lane(1)
    box = Volume.from_aabb(
        lane.x,
        lane.y,
        lane.z,
        lane.x + 10,
        lane.y + 6,
        lane.z + 4,
    )
    specs.append(
        {
            "id": "TMP-V01",
            "temporary": True,
            "notes": "demo:volume",
            "mesh": box.to_mesh(material=MAT_VOLUME),
        }
    )

    lane = _lane(2)
    skew = Volume(
        [
            lane,
            lane + Vec3(10, 0, 0),
            lane + Vec3(12, 6, 1),
            lane + Vec3(2, 6, 1),
            lane + Vec3(0, 0, 5),
            lane + Vec3(10, 0, 6),
            lane + Vec3(12, 6, 7),
            lane + Vec3(2, 6, 6),
        ]
    )
    specs.append(
        {
            "id": "TMP-V02",
            "temporary": True,
            "notes": "demo:volume-skew",
            "mesh": skew.to_mesh(material=MAT_VOLUME),
        }
    )

    lane = _lane(3)
    a = Volume.from_aabb(lane.x, lane.y, lane.z, lane.x + 10, lane.y + 8, lane.z + 5)
    b = Volume.from_aabb(lane.x + 4, lane.y + 3, lane.z + 1, lane.x + 14, lane.y + 9, lane.z + 6)
    union_solid = ensure_closed_solids(union_volumes(a, b))[0]
    specs.append(_boolean_spec(union_solid, "TMP-U01", "demo:boolean-union"))

    lane = _lane(4)
    outer = Volume.from_aabb(lane.x, lane.y, lane.z, lane.x + 12, lane.y + 8, lane.z + 6)
    inner = Volume.from_aabb(lane.x + 3, lane.y + 2, lane.z + 1, lane.x + 9, lane.y + 6, lane.z + 5)
    subtract_solid = ensure_closed_solids(subtract_volumes(outer, inner))[0]
    specs.append(_boolean_spec(subtract_solid, "TMP-S01", "demo:boolean-subtract"))

    lane = _lane(5)
    left = Volume.from_aabb(lane.x, lane.y, lane.z, lane.x + 9, lane.y + 7, lane.z + 5)
    right = Volume.from_aabb(lane.x + 5, lane.y + 2, lane.z + 1, lane.x + 13, lane.y + 8, lane.z + 6)
    intersect_solid = ensure_closed_solids(intersect_volumes(left, right))[0]
    specs.append(_boolean_spec(intersect_solid, "TMP-I01", "demo:boolean-intersect"))

    lane = _lane(6)
    pillar = Volume.from_aabb(lane.x, lane.y, lane.z, lane.x + 2, lane.y + 2, lane.z + 10)
    extended = extend_volume(pillar, direction="+z", length=5)
    specs.append(_boolean_spec(extended, "TMP-E01", "demo:extend-z"))

    return specs


def assign_temp_catalog(obj_refs: list[str], specs: list[dict]) -> None:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    meta_by_ref = {obj_ref: spec for spec, obj_ref in zip(specs, obj_refs)}

    for part in data["parts"]:
        spec = meta_by_ref.get(part["obj_ref"])
        if not spec:
            continue
        part["id"] = spec["id"]
        part["category"] = "__temp__"
        part["phase"] = None
        part["temporary"] = True
        part["visible"] = True
        part["notes"] = spec["notes"]

    data["summary"] = {
        "parts": len(data["parts"]),
        "with_id": sum(1 for p in data["parts"] if p.get("id")),
        "with_category": sum(1 for p in data["parts"] if p.get("category")),
        "with_phase": sum(1 for p in data["parts"] if p.get("phase") is not None),
        "temporary": sum(1 for p in data["parts"] if p.get("temporary")),
    }
    PARTS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    removed = purge_temporary()
    if removed:
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)

    specs = build_demo_specs()
    print(f"Generando {len(specs)} geometrías temporales de validación en x≈{ORIGIN.x}")
    if removed:
        print(f"  (reemplazadas {removed} temporales previas)")

    with EditSession("demo geometrías trimesh (planos, volúmenes, booleanos)"):
        obj_refs = append_objects(OBJ_PATH, [spec["mesh"] for spec in specs])
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        assign_temp_catalog(obj_refs, specs)

    print("IDs:", ", ".join(spec["id"] for spec in specs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
