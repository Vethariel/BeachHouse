"""Edit Wavefront OBJ geometry exported from Tinkercad."""

from __future__ import annotations

import re
from pathlib import Path


def _parse_objects(text: str) -> list[dict]:
    objects: list[dict] = []
    current: dict | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("o "):
            if current:
                objects.append(current)
            current = {
                "obj_ref": stripped[2:].strip(),
                "verts": [],
                "faces": [],
                "group": None,
                "material": None,
            }
            continue
        if current is None:
            continue
        if stripped.startswith("v "):
            parts = stripped.split()
            current["verts"].append((parts[1], parts[2], parts[3]))
        elif stripped.startswith("f "):
            current["faces"].append(
                [int(token.split("/")[0]) for token in stripped.split()[1:]]
            )
        elif stripped.startswith("g "):
            current["group"] = stripped[2:].strip()
        elif stripped.startswith("usemtl "):
            current["material"] = stripped.split()[1]

    if current:
        objects.append(current)

    vert_offset = 0
    for obj in objects:
        base = vert_offset + 1
        obj["faces_local"] = [[idx - base for idx in face] for face in obj["faces"]]
        vert_offset += len(obj["verts"])

    return objects


def _format_object(obj: dict, global_base: int) -> str:
    lines = [f"o {obj['obj_ref']}"]
    for vert in obj["verts"]:
        if isinstance(vert, str):
            lines.append(f"v {vert}")
        else:
            x, y, z = vert
            lines.append(f"v {x} \t\t{y} \t\t{z}")
    lines.append(f"# {len(obj['verts'])} vertices")
    lines.append("")
    lines.append(f"g {obj['group']}")
    lines.append("")
    lines.append(f"usemtl {obj['material']}")
    lines.append("s 0")
    lines.append("")

    for face in obj["faces_local"]:
        one_based = [str(global_base + idx + 1) for idx in face]
        lines.append(f"f {' \t'.join(one_based)}")
    lines.append(f"# {len(obj['faces_local'])} faces")
    lines.append("")
    lines.append(f" #end of {obj['obj_ref']}")
    lines.append("")
    return "\n".join(lines)


def _write_objects(path: Path, objects: list[dict], header: str) -> None:
    chunks = [header.rstrip(), ""]
    global_base = 0
    for obj in objects:
        chunks.append(_format_object(obj, global_base))
        global_base += len(obj["verts"])
    path.write_text("\n".join(chunks).rstrip() + "\n", encoding="utf-8")


def remove_objects(path: Path, obj_refs: set[str]) -> list[str]:
    """Remove objects and rewrite OBJ with valid global face indices."""
    text = path.read_text(encoding="utf-8")
    header_lines: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("o "):
            break
        header_lines.append(line)
    header = "\n".join(header_lines)
    if "mtllib" not in header:
        header = "# Object Export From Tinkercad Server 2015\n\nmtllib obj.mtl"

    objects = _parse_objects(text)
    kept = [obj for obj in objects if obj["obj_ref"] not in obj_refs]
    removed = [obj["obj_ref"] for obj in objects if obj["obj_ref"] in obj_refs]

    missing = sorted(obj_refs - set(removed))
    if missing:
        raise ValueError(f"Objetos no encontrados en {path.name}: {', '.join(missing)}")

    _write_objects(path, kept, header)
    return removed


def _read_header(text: str) -> str:
    header_lines: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("o "):
            break
        header_lines.append(line)
    header = "\n".join(header_lines)
    if "mtllib" not in header:
        header = "# Object Export From Tinkercad Server 2015\n\nmtllib obj.mtl"
    return header


def _next_obj_number(objects: list[dict]) -> int:
    nums = [int(match.group(1)) for obj in objects if (match := re.search(r"(\d+)$", obj["obj_ref"]))]
    return max(nums, default=-1) + 1


def append_objects(path: Path, new_objects: list[dict]) -> list[str]:
    """Append new mesh objects with sequential obj_N refs. Returns new obj_refs."""
    text = path.read_text(encoding="utf-8")
    header = _read_header(text)
    objects = _parse_objects(text)
    next_num = _next_obj_number(objects)
    created: list[str] = []

    for offset, raw in enumerate(new_objects):
        num = next_num + offset
        material = raw["material"]
        obj_ref = f"obj_{num}"
        created.append(obj_ref)
        objects.append(
            {
                "obj_ref": obj_ref,
                "verts": raw["verts"],
                "faces_local": raw["faces_local"],
                "group": raw.get("group") or f"group_{num}_{material}",
                "material": material,
            }
        )

    _write_objects(path, objects, header)
    return created
