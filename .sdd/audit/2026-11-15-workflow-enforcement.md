# Auditoría de Workflow Enforcement

## Alcance

Se implementó la evaluación ejecutable de los nueve gates del workflow predeterminado, la combinación con políticas, las excepciones seguras, el aislamiento de prácticas y la auditoría en `TAUDITORIA`. No se implementaron `SDLCEventProcessor`, CLI ni Hooks.

## Validaciones

| Comando o prueba | Resultado |
| --- | --- |
| `uv run pytest -q` | 43 passed, 28 warnings deprecación de `pytest-asyncio`. |
| `uv run ruff check .` | Exitoso. |
| `uv run ruff format --check .` | 45 archivos formateados. |
| `uv run mypy src` | Sin issues en 33 archivos. |
| `uv lock --check` | Resolved 49 packages in 1ms. |
| `sddnxp validate . --json` | `valid: true`, sin issues. |
| `docker build -t sdlc-manager:latest .` | Exitoso. |
| MCP Docker con dos reinicios y volumen temporal | Persistencia verificada; volumen temporal eliminado. |

## Evidencia funcional

- `WorkflowEngine` distingue `MISSING`, `PENDING`, `REJECTED`, `NOT_APPLICABLE` y `ERROR`.
- `BLOCK` tiene precedencia sobre `WARN` y `PASS`.
- `SDLC-003` conserva trazabilidad y no duplica el control `story_ready`.
- Las excepciones sin autoridad confiable no permiten bypass.
- Las prácticas por proyecto y personales se filtran por su alcance.
- Las evaluaciones y cambios de evidencias escriben en `TAUDITORIA`.
- La migración `0003_workflow_enforcement` conserva datos previos.
