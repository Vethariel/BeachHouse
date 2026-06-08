"""Catálogo y fases de animación — escalera."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARTS_PATH = ROOT / "catalog/parts.json"
CATEGORIES_PATH = ROOT / "catalog/categories.json"

STAIR_ANIMATION_PHASES = (
    {
        "id": 9,
        "label": "Escalera",
        "category": "stair",
        "animation": "fall",
        "phase_duration_ms": 2500,
        "fall_height": 120,
    },
)

LEGACY_STAIR_PHASE_IDS = frozenset({9, 10, 11})


def _is_legacy_stair_phase(phase: dict) -> bool:
    phase_id = phase.get("id")
    if phase_id in LEGACY_STAIR_PHASE_IDS:
        return True
    return phase_id == 12 and phase.get("category") == "stair"


def stair_phase_for_part_id(part_id: str) -> int:
    return STAIR_ANIMATION_PHASES[0]["id"]


def ensure_stair_catalog_meta() -> None:
    data = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))

    categories = data.get("categories", [])
    if not any(c.get("key") == "stair" for c in categories):
        categories.append(
            {
                "key": "stair",
                "label": "Escalera",
                "color": "#b45309",
            }
        )
        data["categories"] = categories

    phases = data.get("phases", [])
    phases = [p for p in phases if not _is_legacy_stair_phase(p)]
    for spec in STAIR_ANIMATION_PHASES:
        phases.append(dict(spec))
    phases.sort(key=lambda p: p["id"])
    data["phases"] = phases

    CATEGORIES_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def assign_stair_parts(obj_refs: list[str], specs) -> None:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    meta = {ref: spec for ref, spec in zip(obj_refs, specs)}

    for part in data["parts"]:
        spec = meta.get(part["obj_ref"])
        if not spec:
            continue
        part["id"] = spec.part_id
        part["category"] = "stair"
        part["phase"] = stair_phase_for_part_id(spec.part_id)
        part["temporary"] = False
        part["visible"] = True
        part["notes"] = spec.part_id.split("-")[0]

    _write_parts_summary(data)


def sync_all_stair_phases() -> int:
    """Reasigna fase de animación a todas las piezas stair ya catalogadas."""
    ensure_stair_catalog_meta()
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    updated = 0
    for part in data["parts"]:
        if part.get("category") != "stair" or not part.get("id"):
            continue
        phase = stair_phase_for_part_id(str(part["id"]))
        if part.get("phase") != phase:
            updated += 1
        part["phase"] = phase
    _write_parts_summary(data)
    return updated


def _write_parts_summary(data: dict) -> None:
    data["summary"] = {
        "parts": len(data["parts"]),
        "with_id": sum(1 for p in data["parts"] if p.get("id")),
        "with_category": sum(1 for p in data["parts"] if p.get("category")),
        "with_phase": sum(1 for p in data["parts"] if p.get("phase") is not None),
        "temporary": sum(1 for p in data["parts"] if p.get("temporary")),
    }
    PARTS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
