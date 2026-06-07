#!/usr/bin/env python3
"""Fase B2: extiende pilares altos y corta el tope con el plano de cubierta."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.geom import extend_volume_to, subtract_solids, volume_from_part
from model.obj_edit import replace_objects
from model.roof.plane import build_roof_above_volume, pillar_extend_z, roof_z_at
from model.session import EditSession

OBJ_PATH = ROOT / "tinker.obj"
PARTS_PATH = ROOT / "catalog/parts.json"
BUILD_CATALOG = ROOT / "tools/build_catalog.py"

SHORT_PILLARS = frozenset(
    {"PIL-001", "PIL-006", "PIL-011", "PIL-015", "PIL-020", "PIL-025"}
)


def load_pillars(part_ids: list[str] | None) -> list[dict]:
    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    pillars = [p for p in data["parts"] if p.get("category") == "pillar" and p.get("id")]

    if part_ids:
        wanted = set(part_ids)
        pillars = [p for p in pillars if p["id"] in wanted]
        missing = sorted(wanted - {p["id"] for p in pillars})
        if missing:
            raise SystemExit(f"IDs no encontrados o no son pilares: {', '.join(missing)}")
    else:
        pillars = [p for p in pillars if p["id"] not in SHORT_PILLARS]

    return sorted(pillars, key=lambda p: p["id"])


def slope_pillar(part: dict, *, above, z_extend: float):
    volume = volume_from_part(part)
    extended = extend_volume_to(volume, z=z_extend)
    return subtract_solids(extended, above)[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cortar pilares al plano de cubierta.")
    parser.add_argument(
        "ids",
        nargs="*",
        help="IDs de pilares (default: 20 pilares altos, excluye cortos)",
    )
    parser.add_argument(
        "-m",
        "--message",
        help="Descripción para el historial",
    )
    args = parser.parse_args(argv)

    pillars = load_pillars(args.ids or None)
    if not pillars:
        raise SystemExit("No hay pilares para procesar.")

    above = build_roof_above_volume()
    z_extend = pillar_extend_z()
    replacements: dict[str, dict] = {}

    print(f"Procesando {len(pillars)} pilares (z_extend={z_extend:.2f})…")
    for part in pillars:
        part_id = part["id"]
        x = part["center"][0]
        target_z = roof_z_at(x)
        solid = slope_pillar(part, above=above, z_extend=z_extend)
        mesh = solid.to_mesh(material=part["material"])
        replacements[part["obj_ref"]] = mesh
        top_z = solid.bounds()[5]
        print(f"  {part_id}  x={x:.0f}  z_plano≈{target_z:.2f}  tope_AABB={top_z:.2f}")

    message = args.message or f"pilares con tope en pendiente ({len(pillars)} piezas)"
    with EditSession(message):
        replace_objects(OBJ_PATH, replacements)
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)

    print(f"\nListo: {len(pillars)} pilares actualizados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
