"""Helpers for code-based modeling sessions."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from model_history import restore_snapshot, save_snapshot  # noqa: E402


class EditSession:
    """Guarda snapshot al entrar y otro al salir si la edición fue exitosa."""

    def __init__(self, message: str, *, backup_before: bool = True):
        self.message = message
        self.backup_before = backup_before
        self._before_id: int | None = None
        self._after_id: int | None = None

    def __enter__(self) -> EditSession:
        if self.backup_before:
            entry = save_snapshot(f"antes: {self.message}", auto=True)
            self._before_id = entry["id"]
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            entry = save_snapshot(f"después: {self.message}")
            self._after_id = entry["id"]
        return False

    def checkpoint(self, note: str) -> int:
        entry = save_snapshot(note, auto=True)
        return entry["id"]

    def revert_to_start(self) -> None:
        if self._before_id is None:
            raise RuntimeError("No hay snapshot inicial en esta sesión.")
        restore_snapshot(str(self._before_id), backup=True)
