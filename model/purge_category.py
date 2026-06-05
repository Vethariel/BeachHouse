#!/usr/bin/env python3
"""Remove all parts in a catalog category from OBJ + catalog."""

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
PARTS_PATH = ROOT / "catalog" / "parts.json"
BUILD_CATALOG = ROOT / "tools" / "build_catalog.py"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Eliminar piezas por categoría.")
    parser.add_argument("category", help="Clave de categoría (ej. roof)")
    parser.add_argument("-m", "--message", help="Mensaje para historial")
    args = parser.parse_args(argv)

    data = json.loads(PARTS_PATH.read_text(encoding="utf-8"))
    targets = [p for p in data["parts"] if p.get("category") == args.category]
    if not targets:
        print(f"Sin piezas en categoría '{args.category}'.")
        return 0

    obj_refs = {p["obj_ref"] for p in targets}
    ids = [p["id"] for p in targets if p.get("id")]
    message = args.message or f"eliminar categoría {args.category} ({len(targets)} piezas)"

    with EditSession(message):
        remove_objects(OBJ_PATH, obj_refs)
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)

    print(f"Eliminadas {len(targets)} piezas ({args.category}).")
    if ids:
        print(f"  IDs: {', '.join(sorted(ids)[:5])}{'…' if len(ids) > 5 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
