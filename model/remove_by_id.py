#!/usr/bin/env python3
"""Remove catalogued parts by ID (updates OBJ + catalog)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.obj_edit import remove_objects
from model.session import EditSession

OBJ_PATH = ROOT / "tinker.obj"
BUILD_CATALOG = ROOT / "tools" / "build_catalog.py"
PARTS_PATH = ROOT / "catalog" / "parts.json"


def resolve_ids(part_ids: list[str]) -> tuple[dict[str, str], set[str]]:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    by_id = {part["id"]: part for part in data["parts"] if part.get("id")}

    mapping: dict[str, str] = {}
    for part_id in part_ids:
        part = by_id.get(part_id)
        if not part:
            raise SystemExit(f"ID no encontrado: {part_id}")
        mapping[part_id] = part["obj_ref"]

    return mapping, set(mapping.values())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Eliminar piezas del modelo por ID.")
    parser.add_argument("ids", nargs="+", help="IDs del catálogo (ej. VG2-015 AM2-018)")
    parser.add_argument(
        "-m",
        "--message",
        help="Descripción para el historial (default: lista de IDs)",
    )
    args = parser.parse_args(argv)

    id_to_ref, obj_refs = resolve_ids(args.ids)
    message = args.message or f"eliminar {', '.join(sorted(id_to_ref))}"

    with EditSession(message):
        remove_objects(OBJ_PATH, obj_refs)
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)

    print(f"Eliminadas {len(id_to_ref)} piezas:")
    for part_id in sorted(id_to_ref):
        print(f"  {part_id} → {id_to_ref[part_id]}")
    summary = json.loads(PARTS_PATH.read_text(encoding="utf-8")).get("summary", {})
    print(f"Piezas restantes: {summary.get('parts')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
