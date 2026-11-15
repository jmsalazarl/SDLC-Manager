# Validación De Arquitectura De Conocimiento

## Alcance

Se separaron workflow SDLC, memoria de ingeniería, prácticas contextuales y políticas obligatorias mediante una migración aditiva desde `0001_initial`.

## Cambios validados

- `0002_knowledge_architecture` crea workflows, etapas, gates, excepciones y prácticas.
- `TEXPERIENCIA` conserva compatibilidad y recibe clasificación, tecnología, categoría, alcance, autor, revisión y relaciones.
- `knowledge/sdlc/default.yaml` instala nueve etapas en una base nueva.
- La inicialización es idempotente y no crea experiencias, proyectos, HU ni evidencias.
- La personalización usa copy-on-write y conserva la plantilla original.
- Las personalizaciones pueden incluir excepciones declarativas, siempre pendientes de aprobación.
- Las prácticas pendientes no se activan; las aprobadas solo generan recomendaciones.
- Las herramientas MCP existentes permanecen disponibles y se agregan operaciones de workflow, memoria y prácticas.
- El motor de políticas conserva `PASS`, `WARN` y `BLOCK` sin cambios de comportamiento.

## Validaciones ejecutadas

| Validación | Resultado |
| --- | --- |
| `uv run pytest -q` | 31 passed |
| `uv run ruff check .` | Passed |
| `uv run ruff format --check .` | 40 files already formatted |
| `uv run mypy src` | Success; 31 source files |
| `docker build -t sdlc-manager:latest .` | Passed |
| Docker MCP instalación limpia | Passed |
| Docker persistencia tras reinicio | Passed |
| `sddnxp validate . --json` | Valid; sin issues |

Las pruebas muestran advertencias de deprecación de `pytest-asyncio` relacionadas con APIs de política de eventos de Python 3.14.
