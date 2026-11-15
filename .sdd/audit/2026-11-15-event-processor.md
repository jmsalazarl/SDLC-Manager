# Evidencia de validación: SDLC Event Processor

## Alcance

Validación de la implementación de `SdlcEventProcessor`, su contrato normalizado, persistencia idempotente, integración MCP y migración SQLite. No se implementaron Hooks, plugins, adaptadores específicos ni CLI.

## Comandos ejecutados

| Comando | Resultado observado |
| --- | --- |
| `uv run alembic upgrade head` | Exitoso; ejecutó `0001_initial`, `0002_knowledge_architecture`, `0003_workflow_enforcement` y `0004_event_processor`. |
| `uv run pytest -q` | `53 passed`, `28 warnings` de deprecación de `pytest-asyncio`. |
| `uv run ruff check .` | Exitoso; todos los checks pasaron. |
| `uv run ruff format --check .` | Exitoso; 49 archivos formateados. |
| `uv run mypy src` | Exitoso; sin errores en 35 archivos fuente. |
| `uv lock --check` | Exitoso; 49 paquetes resueltos sin cambios. |
| `sddnxp validate . --json` | Exitoso; `valid: true`, `issues: []`. |
| `docker build -t sdlc-manager:latest .` | Exitoso; imagen construida con Python 3.12 slim y usuario no root. |

## Cobertura funcional verificada

- Contratos Pydantic estrictos con UUID serializados como texto JSON.
- Rechazo de UUID inválidos, eventos incompletos y tipos no soportados.
- Procesamiento de formularios `.wpx` y detección de `SDLC-001`.
- Advertencias de prácticas aprobadas sin producir `BLOCK`.
- Bloqueo de HU incompleta.
- Bloqueo con evidencias pendientes y `PASS` con evidencias verificadas.
- Idempotencia para eventos repetidos.
- Rechazo de reutilización de `event_id` con payload diferente.
- Persistencia y recuperación después de reconstruir el contenedor de aplicación.
- Aislamiento de memorias con alcance PROJECT.
- Descubrimiento e invocación MCP por stdio.
- Evento desconocido devuelto como `UNSUPPORTED` desde la frontera Python.
- Error inesperado devuelto como `ERROR` sin convertirlo en `PASS`.

## Prueba Docker de persistencia

Se inició el servidor MCP dos veces usando la imagen `sdlc-manager:latest`, red deshabilitada y el volumen `sdlc-manager-event-processor-final-20261115:/app/data`. La primera invocación de `process_sdlc_event` devolvió `PROCESSED` y la segunda devolvió `DUPLICATE` para el mismo `event_id`.

## Resultado

La implementación cumple los criterios de validación de la spec `SPEC-004`. El estado de la spec se actualiza a `implemented`.

## Limitaciones observadas

- El schema MCP usa un enum cerrado; un evento desconocido es rechazado en la validación MCP. La frontera Python conserva la respuesta estructurada `UNSUPPORTED_EVENT_TYPE`.
- No hay procesamiento asíncrono, reintento automático ni coordinación distribuida para procesos concurrentes.
- `source_client` permanece como metadata y todavía no existe una autoridad corporativa para validar identidad.
