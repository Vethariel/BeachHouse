from __future__ import annotations

import trimesh

from model.geom.solid import Solid
from model.geom.volume import Volume


def _normalize_trimesh_result(result) -> list[trimesh.Trimesh]:
    if result is None:
        return []
    if isinstance(result, trimesh.Trimesh):
        return [] if result.is_empty else [result]
    if isinstance(result, (list, tuple)):
        return [mesh for mesh in result if isinstance(mesh, trimesh.Trimesh) and not mesh.is_empty]
    raise TypeError(f"Resultado booleano inesperado: {type(result)!r}")


def _mesh_to_solid(mesh: trimesh.Trimesh) -> Solid:
    mesh = mesh.copy()
    mesh.merge_vertices()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.fill_holes()

    if mesh.is_empty:
        raise ValueError("El resultado booleano quedó vacío.")
    if not mesh.is_watertight:
        raise ValueError("El resultado booleano no es un volumen cerrado (watertight).")
    if not mesh.is_volume:
        raise ValueError("El resultado booleano no es un volumen válido.")

    return Solid.from_trimesh(mesh)


def _boolean(meshes: list[trimesh.Trimesh], operation: str) -> list[Solid]:
    if len(meshes) < 2:
        raise ValueError("Se requieren al menos dos mallas para la operación booleana.")

    engines = ("manifold", "blender", None)
    last_error: Exception | None = None

    for engine in engines:
        try:
            kwargs = {"engine": engine} if engine else {}
            if operation == "union":
                result = trimesh.boolean.union(meshes, **kwargs)
            elif operation == "difference":
                result = trimesh.boolean.difference(meshes, **kwargs)
            elif operation == "intersection":
                result = trimesh.boolean.intersection(meshes, **kwargs)
            else:
                raise ValueError(f"Operación desconocida: {operation}")

            return [_mesh_to_solid(mesh) for mesh in _normalize_trimesh_result(result)]
        except Exception as err:  # noqa: BLE001 - probar motores disponibles
            last_error = err
            continue

    raise RuntimeError(f"No se pudo completar la operación booleana ({operation}).") from last_error


def union_volumes(a: Volume, b: Volume) -> list[Solid]:
    meshes = [Solid.from_volume(a).to_trimesh(), Solid.from_volume(b).to_trimesh()]
    return _boolean(meshes, "union")


def subtract_volumes(base: Volume, cut: Volume) -> list[Solid]:
    meshes = [Solid.from_volume(base).to_trimesh(), Solid.from_volume(cut).to_trimesh()]
    return _boolean(meshes, "difference")


def intersect_volumes(a: Volume, b: Volume) -> list[Solid]:
    meshes = [Solid.from_volume(a).to_trimesh(), Solid.from_volume(b).to_trimesh()]
    return _boolean(meshes, "intersection")


def ensure_closed_solids(solids: list[Solid]) -> list[Solid]:
    for solid in solids:
        solid.validate()
    return solids


# Compatibilidad con scripts previos
ensure_closed_volumes = ensure_closed_solids
