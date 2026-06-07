"""Subtract diagonal braces from voladizo correas and support pillars."""

from __future__ import annotations

import json
from pathlib import Path

import trimesh

from model.geom.solid import Solid
from model.obj_edit import solid_from_obj_ref
from model.roof.framing import FramingSpec, ROOF_ROWS_Y

HIGH_PILLAR_BY_Y = {
    0.0: "PIL-002",
    -25.0: "PIL-007",
    -50.0: "PIL-012",
    -75.0: "PIL-016",
    -100.0: "PIL-021",
}

LOW_PILLAR_BY_Y = {
    0.0: "PIL-005",
    -25.0: "PIL-010",
    -50.0: "PIL-025",
    -75.0: "PIL-019",
    -100.0: "PIL-024",
}

INTERSECT_MIN_VOLUME = 0.05


def diagonal_links() -> list[tuple[str, str, str]]:
    """Return (RD id, RF voladizo id, pillar id) for each diagonal."""
    links: list[tuple[str, str, str]] = []
    for row_index, y in enumerate(ROOF_ROWS_Y):
        links.append(
            (
                f"RD-{2 * row_index + 1:03d}",
                f"RF-{1 + row_index * 5:03d}",
                HIGH_PILLAR_BY_Y[y],
            )
        )
        links.append(
            (
                f"RD-{2 * row_index + 2:03d}",
                f"RF-{5 + row_index * 5:03d}",
                LOW_PILLAR_BY_Y[y],
            )
        )
    return links


def _normalize_trimesh_result(result) -> list[trimesh.Trimesh]:
    if result is None:
        return []
    if isinstance(result, trimesh.Trimesh):
        return [] if result.is_empty else [result]
    if isinstance(result, (list, tuple)):
        return [mesh for mesh in result if isinstance(mesh, trimesh.Trimesh) and not mesh.is_empty]
    return []


def _intersection_volume(base: Solid, cutter: Solid) -> float:
    try:
        result = trimesh.boolean.intersection(
            [base.to_trimesh(strict=False), cutter.to_trimesh(strict=False)],
            engine="manifold",
        )
    except Exception:
        return 0.0
    meshes = _normalize_trimesh_result(result)
    return sum(float(mesh.volume) for mesh in meshes)


def _difference_largest(base: Solid, cutter: Solid) -> Solid:
    """Resta cutter de base; conserva el fragmento mayor. Usa la malla exacta del cutter."""
    if _intersection_volume(base, cutter) < INTERSECT_MIN_VOLUME:
        return base

    last_error: Exception | None = None
    for engine in ("manifold", None):
        try:
            kwargs = {"engine": engine} if engine else {}
            result = trimesh.boolean.difference(
                [base.to_trimesh(strict=False), cutter.to_trimesh(strict=False)],
                **kwargs,
            )
            meshes = _normalize_trimesh_result(result)
            if not meshes:
                return base
            mesh = max(meshes, key=lambda item: float(item.volume))
            return Solid.from_trimesh_relaxed(mesh)
        except Exception as err:  # noqa: BLE001
            last_error = err
            continue

    raise RuntimeError("No se pudo restar la diagonal del sólido.") from last_error


def apply_diagonal_cutouts(
    specs: list[FramingSpec],
    obj_path: Path,
    parts_path: Path,
) -> tuple[list[FramingSpec], dict[str, dict]]:
    """Notch RF/pillar and clip each diagonal to the exterior of both."""
    catalog = json.loads(parts_path.read_text(encoding="utf-8"))
    id_to_ref = {part["id"]: part["obj_ref"] for part in catalog["parts"] if part.get("id")}
    id_to_material = {part["id"]: part["material"] for part in catalog["parts"] if part.get("id")}

    rf_by_id = {spec.part_id: spec for spec in specs if spec.part_id.startswith("RF-")}
    rd_by_id = {spec.part_id: spec for spec in specs if spec.part_id.startswith("RD-")}

    pillar_solids: dict[str, Solid] = {}
    pillar_refs: dict[str, str] = {}

    for rd_id, rf_id, pillar_id in diagonal_links():
        diagonal = rd_by_id[rd_id].solid
        rf_spec = rf_by_id[rf_id]

        if pillar_id not in pillar_solids:
            obj_ref = id_to_ref[pillar_id]
            pillar_refs[pillar_id] = obj_ref
            pillar_solids[pillar_id] = solid_from_obj_ref(obj_path, obj_ref, strict=False)

        pillar = pillar_solids[pillar_id]
        rf_solid = rf_spec.solid

        rf_by_id[rf_id] = FramingSpec(
            rf_id,
            _difference_largest(rf_solid, diagonal),
            rf_spec.material,
        )
        pillar_solids[pillar_id] = _difference_largest(pillar, diagonal)

        clipped = _difference_largest(diagonal, pillar)
        clipped = _difference_largest(clipped, rf_solid)
        rd_by_id[rd_id] = FramingSpec(rd_id, clipped, rd_by_id[rd_id].material)

    pillar_replacements = {
        pillar_refs[pillar_id]: pillar_solids[pillar_id].to_mesh(
            material=id_to_material[pillar_id],
            validate=False,
        )
        for pillar_id in pillar_solids
    }

    updated_specs: list[FramingSpec] = []
    for spec in specs:
        if spec.part_id.startswith("RF-"):
            updated_specs.append(rf_by_id[spec.part_id])
        elif spec.part_id.startswith("RD-"):
            updated_specs.append(rd_by_id[spec.part_id])
        else:
            updated_specs.append(spec)

    return updated_specs, pillar_replacements
