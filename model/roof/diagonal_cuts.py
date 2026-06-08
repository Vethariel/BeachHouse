"""Recorte de diagonales con copias temporales de correa voladizo y pilar de apoyo."""

from __future__ import annotations

import json
from pathlib import Path

import trimesh

from model.geom.solid import Solid
from model.obj_edit import solid_from_obj_ref
from model.roof.framing import EXCLUDED_DIAGONAL_IDS, FramingSpec, ROOF_ROWS_Y

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
    return [
        link for link in links if link[0] not in EXCLUDED_DIAGONAL_IDS
    ]


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
    """Resta cutter de base; conserva el fragmento mayor."""
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

    raise RuntimeError("No se pudo recortar la diagonal.") from last_error


def temporary_support_solids(
    obj_path: Path,
    id_to_ref: dict[str, str],
    rf_id: str,
    pillar_id: str,
) -> tuple[Solid, Solid]:
    """Copias temporales en memoria de la correa voladizo y el pilar (sin alterar el OBJ)."""
    rf_temp = solid_from_obj_ref(obj_path, id_to_ref[rf_id], strict=False)
    pillar_temp = solid_from_obj_ref(obj_path, id_to_ref[pillar_id], strict=False)
    return rf_temp, pillar_temp


def clip_diagonal_with_supports(
    diagonal: Solid,
    rf_temp: Solid,
    pillar_temp: Solid,
) -> Solid:
    """Resta copias temporales de pilar y correa de la diagonal."""
    clipped = _difference_largest(diagonal, pillar_temp)
    return _difference_largest(clipped, rf_temp)


def _catalog_maps(parts_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    catalog = json.loads(parts_path.read_text(encoding="utf-8"))
    id_to_ref = {part["id"]: part["obj_ref"] for part in catalog["parts"] if part.get("id")}
    id_to_material = {
        part["id"]: part["material"] for part in catalog["parts"] if part.get("id")
    }
    return id_to_ref, id_to_material


def apply_diagonal_clips_to_specs(
    specs: list[FramingSpec],
    obj_path: Path,
    parts_path: Path,
) -> list[FramingSpec]:
    """Recorta cada RD usando copias temporales de su RF voladizo y pilar de apoyo."""
    id_to_ref, _ = _catalog_maps(parts_path)
    rd_by_id = {spec.part_id: spec for spec in specs if spec.part_id.startswith("RD-")}

    for rd_id, rf_id, pillar_id in diagonal_links():
        rf_temp, pillar_temp = temporary_support_solids(
            obj_path, id_to_ref, rf_id, pillar_id
        )
        spec = rd_by_id[rd_id]
        clipped = clip_diagonal_with_supports(spec.solid, rf_temp, pillar_temp)
        rd_by_id[rd_id] = FramingSpec(rd_id, clipped, spec.material)

    updated: list[FramingSpec] = []
    for spec in specs:
        if spec.part_id.startswith("RD-"):
            updated.append(rd_by_id[spec.part_id])
        else:
            updated.append(spec)
    return updated


def clip_diagonals_in_obj(
    obj_path: Path,
    parts_path: Path,
) -> dict[str, dict]:
    """Recorta diagonales ya presentes en el OBJ. Devuelve meshes para replace_objects."""
    id_to_ref, id_to_material = _catalog_maps(parts_path)
    replacements: dict[str, dict] = {}

    for rd_id, rf_id, pillar_id in diagonal_links():
        rd_ref = id_to_ref[rd_id]
        diagonal = solid_from_obj_ref(obj_path, rd_ref, strict=False)
        rf_temp, pillar_temp = temporary_support_solids(
            obj_path, id_to_ref, rf_id, pillar_id
        )
        clipped = clip_diagonal_with_supports(diagonal, rf_temp, pillar_temp)
        replacements[rd_ref] = clipped.to_mesh(
            material=id_to_material[rd_id],
            validate=False,
        )

    return replacements
