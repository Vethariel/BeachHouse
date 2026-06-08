# BeachHouse

Modelo 3D modular de una casa de playa en madera, con catálogo semántico de piezas, pipeline de edición por código y visualizador web con animación de construcción por fases.

## Origen del modelo

La geometría base salió de **Tinkercad** (`tinker.obj`): cimentación, pilares, forjados, entramado y la estructura general. A partir de ahí el modelo se completó y refinó con **scripts Python** en este repositorio: cubierta, escalera, barandas, operaciones booleanas, recortes y sincronización del catálogo.

El visualizador no reescala el OBJ: **1 unidad del modelo = 0,1 m reales** (eje Z vertical).

## Qué incluye

- **`tinker.obj` + `obj.mtl`** — malla exportada y materiales de referencia.
- **`catalog/`** — catálogo de piezas (`parts.json`) y metadatos de categorías, fases y acabados (`categories.json`).
- **`index.html`** — visor Three.js: modo modelado, animación por fases, escena de playa al final y audio ambiente.
- **`model/`** — scripts de modelado (cubierta, escalera, barandas, utilidades geométricas).
- **`tools/`** — generación del catálogo desde el OBJ e historial de snapshots del modelo.
- **`docs/`** — notas de diseño (cubierta, escaleras).

## Requisitos

- Navegador moderno con WebGL.
- [Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer) (o servidor HTTP equivalente) para abrir el visor — **no uses `file://`**.
- Python ≥ 3.11 y [uv](https://docs.astral.sh/uv/) para los scripts de modelado.

## Visualizador

```bash
# Desde la raíz del repo, servir con Live Server apuntando a index.html
# o, por ejemplo:
python -m http.server 5500
```

Abrir `http://localhost:5500/index.html`.

### Modos

| Modo | Descripción |
|------|-------------|
| **Modelado** | Orbitar, filtrar por categoría, inspeccionar piezas. |
| **Animación** | Construcción secuencial por fases (caída de piezas → escalera → barandas → acabados en madera con transición a playa). |

### Audio (opcional)

En la fase final suena **«Wasteland»** de **DM Dokuro** (*Terraria: Calamity Mod*). Colocá el archivo en:

```
assets/audio/wasteland.mp3
```

Ver [Créditos y terceros](#créditos-y-terceros).

## Modelado por código

Instalar dependencias:

```bash
uv sync
```

Ejemplos habituales:

```bash
# Regenerar catálogo tras editar tinker.obj
uv run python tools/build_catalog.py

# Guardar / listar / restaurar snapshots del modelo
uv run python tools/model_history.py save -m "descripción del cambio"
uv run python tools/model_history.py list
uv run python tools/model_history.py restore 3

# Scripts de construcción (cada uno con su EditSession y snapshot)
uv run python model/build_roof_framing.py
uv run python model/build_stairs_treads.py
uv run python model/build_railing_br001.py
```

Los scripts en `model/` modifican `tinker.obj` y actualizan `catalog/parts.json` (y a veces `categories.json`). `model/session.py` guarda snapshots automáticos antes y después de cada sesión de edición.

## Fases de animación

| Fase | Contenido |
|------|-----------|
| 0–8 | Estructura (cimentación → cubierta) |
| 9 | Escalera |
| 10 | Baranda P1 (BR-002) |
| 11 | Baranda P2 (BR-001) |
| 12 | Acabados · maderas (transición suave a escena de playa) |

Las fases se definen en `catalog/categories.json` / `catalog/parts.json` (`phase`, `animation`, `wood_finishes`).

## Estructura del repo

```
BeachHouse/
├── index.html          # Visor web
├── tinker.obj          # Geometría principal
├── obj.mtl
├── catalog/
│   ├── parts.json      # Piezas (id, obj_ref, phase, category…)
│   └── categories.json # Categorías, fases, colores, acabados
├── model/              # Scripts de modelado
├── tools/              # Catálogo e historial
├── assets/audio/       # Música (no incluida en la licencia del repo)
├── docs/               # Planes de diseño
└── history/            # Snapshots locales del modelo
```

## Créditos y terceros

| Recurso | Autor | Uso en el proyecto | Licencia |
|---------|--------|-------------------|----------|
| **Wasteland** | [DM Dokuro](https://www.youtube.com/@DMDokuro) — *Terraria: Calamity Mod* | Banda sonora de la animación final | **No** cubierta por la licencia MIT de este repo. Derechos reservados por el autor. |

El resto del código, catálogo y geometría generada en este repositorio (salvo la base inicial de Tinkercad) se publica bajo **MIT** — ver [LICENSE](LICENSE).

## Licencia

MIT — Copyright (c) 2026 Vethariel. Ver [LICENSE](LICENSE).
