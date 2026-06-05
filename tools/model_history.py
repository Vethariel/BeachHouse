#!/usr/bin/env python3
"""Snapshot history for BeachHouse model state.

Tracks geometry and catalog files so code-based edits can be reverted.
Use before/after modeling scripts:

    uv run python tools/model_history.py save -m "descripción del cambio"
    uv run python tools/model_history.py list
    uv run python tools/model_history.py restore 3
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORY_DIR = ROOT / "history"
SNAPSHOTS_DIR = HISTORY_DIR / "snapshots"
MANIFEST_PATH = HISTORY_DIR / "manifest.json"

TRACKED_FILES = (
    "tinker.obj",
    "obj.mtl",
    "catalog/categories.json",
    "catalog/parts.json",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(text: str, max_len: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if not slug:
        slug = "snapshot"
    return slug[:max_len].strip("-")


def _load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"version": 1, "snapshots": []}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _save_manifest(manifest: dict) -> None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _snapshot_stats() -> dict:
    parts_path = ROOT / "catalog" / "parts.json"
    if not parts_path.exists():
        return {}
    data = json.loads(parts_path.read_text(encoding="utf-8"))
    summary = data.get("summary") or {}
    return {
        "parts": summary.get("parts"),
        "with_category": summary.get("with_category"),
        "with_phase": summary.get("with_phase"),
    }


def _snapshot_dir(snapshot_id: int, slug: str) -> Path:
    return SNAPSHOTS_DIR / f"{snapshot_id:04d}-{slug}"


def _resolve_snapshot(manifest: dict, ref: str) -> dict:
    snapshots = manifest.get("snapshots", [])
    if not snapshots:
        raise SystemExit("No hay snapshots guardados.")

    if ref.isdigit():
        target_id = int(ref)
        for snap in snapshots:
            if snap["id"] == target_id:
                return snap
        raise SystemExit(f"Snapshot #{target_id} no encontrado.")

    for snap in reversed(snapshots):
        if snap.get("slug") == ref or str(snap["id"]) == ref:
            return snap
    raise SystemExit(f"Snapshot '{ref}' no encontrado.")


def _copy_tracked_files(source_root: Path, dest_root: Path) -> None:
    for rel in TRACKED_FILES:
        src = source_root / rel
        dst = dest_root / rel
        if not src.exists():
            raise FileNotFoundError(f"Falta archivo rastreado: {rel}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def save_snapshot(message: str, *, auto: bool = False) -> dict:
    manifest = _load_manifest()
    next_id = max((snap["id"] for snap in manifest["snapshots"]), default=0) + 1
    slug = _slugify(message)
    snap_dir = _snapshot_dir(next_id, slug)
    snap_dir.mkdir(parents=True, exist_ok=False)

    _copy_tracked_files(ROOT, snap_dir)

    entry = {
        "id": next_id,
        "slug": slug,
        "created_at": _utc_now(),
        "message": message,
        "auto": auto,
        "files": list(TRACKED_FILES),
        "stats": _snapshot_stats(),
    }
    (snap_dir / "meta.json").write_text(
        json.dumps(entry, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    manifest["snapshots"].append(entry)
    manifest["current"] = next_id
    _save_manifest(manifest)
    return entry


def list_snapshots() -> list[dict]:
    return _load_manifest().get("snapshots", [])


def restore_snapshot(ref: str, *, backup: bool = True) -> dict:
    manifest = _load_manifest()
    target = _resolve_snapshot(manifest, ref)
    snap_dir = _snapshot_dir(target["id"], target["slug"])
    if not snap_dir.exists():
        raise SystemExit(f"Directorio de snapshot ausente: {snap_dir}")

    if backup:
        save_snapshot(
            f"auto-backup antes de restaurar #{target['id']}",
            auto=True,
        )

    _copy_tracked_files(snap_dir, ROOT)
    manifest = _load_manifest()
    manifest["current"] = target["id"]
    _save_manifest(manifest)
    return target


def show_snapshot(ref: str) -> dict:
    manifest = _load_manifest()
    target = _resolve_snapshot(manifest, ref)
    snap_dir = _snapshot_dir(target["id"], target["slug"])
    target = dict(target)
    target["path"] = str(snap_dir.relative_to(ROOT))
    return target


def cmd_save(args: argparse.Namespace) -> int:
    entry = save_snapshot(args.message, auto=args.auto)
    print(f"Snapshot #{entry['id']} guardado: {entry['message']}")
    print(f"  → history/snapshots/{entry['id']:04d}-{entry['slug']}/")
    if entry.get("stats"):
        print(f"  → piezas: {entry['stats']}")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    snapshots = list_snapshots()
    if not snapshots:
        print("Sin snapshots. Creá uno con:")
        print('  uv run python tools/model_history.py save -m "baseline"')
        return 0

    manifest = _load_manifest()
    current = manifest.get("current")
    for snap in snapshots:
        marker = " *" if snap["id"] == current else ""
        auto = " [auto]" if snap.get("auto") else ""
        stats = snap.get("stats") or {}
        parts = stats.get("parts")
        parts_label = f" · {parts} piezas" if parts is not None else ""
        print(
            f"#{snap['id']:04d}{marker}{auto}  {snap['created_at']}  "
            f"{snap['message']}{parts_label}"
        )
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    snap = show_snapshot(args.ref)
    print(json.dumps(snap, indent=2, ensure_ascii=False))
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    target = restore_snapshot(args.ref, backup=not args.no_backup)
    print(f"Restaurado snapshot #{target['id']}: {target['message']}")
    if not args.no_backup:
        print("Se creó un auto-backup del estado previo.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Historial de snapshots del modelo BeachHouse."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    save = sub.add_parser("save", help="Guardar snapshot del estado actual")
    save.add_argument("-m", "--message", required=True, help="Descripción del cambio")
    save.add_argument("--auto", action="store_true", help="Marcar como backup automático")
    save.set_defaults(func=cmd_save)

    list_cmd = sub.add_parser("list", help="Listar snapshots")
    list_cmd.set_defaults(func=cmd_list)

    show = sub.add_parser("show", help="Ver metadata de un snapshot")
    show.add_argument("ref", help="ID numérico o slug")
    show.set_defaults(func=cmd_show)

    restore = sub.add_parser("restore", help="Restaurar archivos desde un snapshot")
    restore.add_argument("ref", help="ID numérico o slug")
    restore.add_argument(
        "--no-backup",
        action="store_true",
        help="No crear auto-backup antes de restaurar",
    )
    restore.set_defaults(func=cmd_restore)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
