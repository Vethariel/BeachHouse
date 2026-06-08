#!/usr/bin/env python3
"""Sync catalog/parts.json from tinker.obj (Tinkercad state only).

Preserves manually assigned fields (id, category, phase, visible, notes)
when re-syncing after OBJ updates.

Scale (no geometry rescale): 1 model unit = 0.1 m real.
Example: PIL-002 height 73 model units = 7.3 m.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJ_PATH = ROOT / "tinker.obj"
MTL_PATH = ROOT / "obj.mtl"
CATEGORIES_PATH = ROOT / "catalog" / "categories.json"
PARTS_PATH = ROOT / "catalog" / "parts.json"

MANUAL_FIELDS = ("id", "category", "phase", "visible", "notes", "temporary")
METERS_PER_MODEL_UNIT = 0.1


def model_to_meters(value: float) -> float:
    return value * METERS_PER_MODEL_UNIT


def meters_to_model(value: float) -> float:
    return value / METERS_PER_MODEL_UNIT


def parse_obj(path: Path) -> list[dict]:
    objects: list[dict] = []
    current: dict | None = None

    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if line.startswith("o "):
                if current:
                    objects.append(current)
                current = {
                    "obj_ref": line[2:].strip(),
                    "verts": [],
                    "material": None,
                    "group": None,
                }
            elif current is None:
                continue
            elif line.startswith("g "):
                current["group"] = line[2:].strip()
            elif line.startswith("usemtl "):
                current["material"] = line.split()[1]
            elif line.startswith("v "):
                parts = line.split()
                current["verts"].append(
                    (float(parts[1]), float(parts[2]), float(parts[3]))
                )

    if current:
        objects.append(current)

    return objects


def parse_mtl(path: Path) -> dict[str, str]:
    colors: dict[str, str] = {}
    current: str | None = None

    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if line.startswith("newmtl "):
                current = line.split()[1]
            elif line.startswith("Kd ") and current:
                r, g, b = (float(x) for x in line.split()[1:4])
                colors[current] = "#{:02x}{:02x}{:02x}".format(
                    int(r * 255), int(g * 255), int(b * 255)
                )

    return colors


def dims(verts: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)


def bounds(verts: list[tuple[float, float, float]]) -> dict[str, list[float]]:
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return {
        "min": [round(min(xs), 2), round(min(ys), 2), round(min(zs), 2)],
        "max": [round(max(xs), 2), round(max(ys), 2), round(max(zs), 2)],
    }


def center(verts: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return (
        (min(xs) + max(xs)) / 2,
        (min(ys) + max(ys)) / 2,
        (min(zs) + max(zs)) / 2,
    )


def load_existing() -> dict[str, dict]:
    if not PARTS_PATH.exists():
        return {}
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    return {part["obj_ref"]: part for part in data.get("parts", [])}


def part_from_obj(raw: dict, existing: dict | None) -> dict:
    cx, cy, cz = center(raw["verts"])
    dx, dy, dz = dims(raw["verts"])
    part = {
        "obj_ref": raw["obj_ref"],
        "material": raw["material"],
        "group": raw["group"],
        "center": [round(cx, 2), round(cy, 2), round(cz, 2)],
        "size": [round(dx, 2), round(dy, 2), round(dz, 2)],
        "bounds": bounds(raw["verts"]),
        "id": None,
        "category": None,
        "phase": None,
        "visible": True,
        "notes": "",
    }
    if existing:
        for field in MANUAL_FIELDS:
            if field in existing:
                part[field] = existing[field]
    return part


def obj_ref_sort_key(obj_ref: str) -> tuple:
    match = re.search(r"(\d+)$", obj_ref)
    if match:
        return (0, int(match.group(1)))
    return (1, obj_ref)


def build_catalog() -> dict:
    categories_meta = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))
    existing_by_ref = load_existing()
    raw_parts = parse_obj(OBJ_PATH)
    material_colors = parse_mtl(MTL_PATH)

    parts = [
        part_from_obj(raw, existing_by_ref.get(raw["obj_ref"]))
        for raw in raw_parts
    ]
    parts.sort(key=lambda p: obj_ref_sort_key(p["obj_ref"]))

    category_colors = {
        cat["key"]: cat["color"]
        for cat in categories_meta.get("categories", [])
        if "key" in cat and "color" in cat
    }
    phase_labels = {
        str(phase["id"]): phase["label"]
        for phase in categories_meta.get("phases", [])
        if "id" in phase and "label" in phase
    }

    assigned = sum(1 for p in parts if p.get("category"))
    phased = sum(1 for p in parts if p.get("phase") is not None)

    return {
        "version": 1,
        "source_obj": "tinker.obj",
        "source_mtl": "obj.mtl",
        "units": categories_meta.get("units", {}),
        "material_colors": material_colors,
        "phases": categories_meta.get("phases", []),
        "categories": categories_meta.get("categories", []),
        "wood_finishes": categories_meta.get("wood_finishes", {}),
        "phase_labels": phase_labels,
        "category_colors": category_colors,
        "summary": {
            "parts": len(parts),
            "with_id": sum(1 for p in parts if p.get("id")),
            "with_category": assigned,
            "with_phase": phased,
        },
        "parts": parts,
    }


def main() -> None:
    catalog = build_catalog()
    PARTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PARTS_PATH.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {PARTS_PATH}")
    print(f"Parts: {catalog['summary']['parts']}")
    print(f"  with id:       {catalog['summary']['with_id']}")
    print(f"  with category: {catalog['summary']['with_category']}")
    print(f"  with phase:    {catalog['summary']['with_phase']}")


if __name__ == "__main__":
    main()
