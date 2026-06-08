#!/usr/bin/env python3
"""Elimina la guía temporal de escalera (TMP-ESC)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.build_stairs_guide import purge_stairs_guide
from model.stairs.envelope import STAIR_GUIDE_PART_ID
from model.session import EditSession

BUILD_CATALOG = ROOT / "tools/build_catalog.py"


def main() -> int:
    with EditSession("eliminar guía escalera (TMP-ESC)"):
        removed = purge_stairs_guide()
        if not removed:
            print(f"{STAIR_GUIDE_PART_ID} no estaba en el modelo.")
            return 0
        subprocess.run([sys.executable, str(BUILD_CATALOG)], check=True)
        print(f"Eliminado {STAIR_GUIDE_PART_ID}: {', '.join(removed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
