"""Catálogo y fases de animación — barandas (BR-*)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARTS_PATH = ROOT / "catalog/parts.json"
CATEGORIES_PATH = ROOT / "catalog/categories.json"

RAILING_ANIMATION_PHASES = (
    {
        "id": 10,
        "label": "Baranda · P1",
        "category": "railing",
        "animation": "fall",
        "phase_duration_ms": 2500,
        "fall_height": 120,
        "part_id": "BR-002",
    },
    {
        "id": 11,
        "label": "Baranda · P2",
        "category": "railing",
        "animation": "fall",
        "phase_duration_ms": 2500,
        "fall_height": 120,
        "part_id": "BR-001",
    },
)

LEGACY_RAILING_PHASE_IDS = frozenset({13, 14})

_PART_ID_TO_PHASE = {
    spec["part_id"]: spec["id"] for spec in RAILING_ANIMATION_PHASES
}


def railing_phase_for_part_id(part_id: str) -> int:
    return _PART_ID_TO_PHASE.get(part_id, RAILING_ANIMATION_PHASES[0]["id"])


def ensure_railing_catalog_meta() -> None:
    data = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))

    categories = data.get("categories", [])
    if not any(c.get("key") == "railing" for c in categories):
        categories.append(
            {
                "key": "railing",
                "label": "Barandas",
                "color": "#475569",
            }
        )
        data["categories"] = categories

    phases = data.get("phases", [])
    phases = [p for p in phases if p.get("id") not in LEGACY_RAILING_PHASE_IDS]
    for spec in RAILING_ANIMATION_PHASES:
        phases.append({key: spec[key] for key in spec if key != "part_id"})
    phases.sort(key=lambda p: p["id"])
    data["phases"] = phases

    CATEGORIES_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def assign_railing_parts(obj_refs: list[str], specs) -> None:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    meta = {ref: spec for ref, spec in zip(obj_refs, specs)}

    for part in data["parts"]:
        spec = meta.get(part["obj_ref"])
        if not spec:
            continue
        part["id"] = spec.part_id
        part["category"] = "railing"
        part["phase"] = railing_phase_for_part_id(spec.part_id)
        part["temporary"] = False
        part["visible"] = True
        part["notes"] = spec.part_id.split("-")[0]

    _write_parts_summary(data)


def sync_all_railing_phases() -> int:
    """Reasigna fase de animación a todas las piezas railing ya catalogadas."""
    ensure_railing_catalog_meta()
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    updated = 0
    for part in data["parts"]:
        if part.get("category") != "railing" or not part.get("id"):
            continue
        phase = railing_phase_for_part_id(str(part["id"]))
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
