# Evidencia De Validación: Integraciones Multiagente

## Alcance

Validación de configuraciones MCP, instrucciones persistentes, wrappers de CLI,
normalización de eventos y ausencia de cambios al núcleo de dominio.

## Comandos ejecutados

| Comando | Resultado observado |
|---|---|
| `uv run pytest -q` | `64 passed`, `1 skipped`, `28 warnings` antes de habilitar la prueba Docker |
| `SDLC_MANAGER_RUN_DOCKER_TESTS=1 uv run pytest -q` | `65 passed`, `28 warnings` |
| `uv run pytest tests/integration/test_multiagent_integrations.py -q` | `7 passed`, `1 warning` |
| `uv run ruff check .` | Exitoso |
| `uv run ruff format --check .` | Exitoso; `60 files already formatted` |
| `uv run mypy src` | Exitoso; sin errores en 36 archivos fuente |
| `uv run mypy integrations` | Exitoso; sin errores en 8 archivos de adaptadores |
| `sddnxp validate . --json` | Exitoso; `valid: true`, `issues: []` |
| `docker build -t sdlc-manager:latest .` | Exitoso |
| `uv run alembic` con configuración y SQLite temporales | Exitoso; migraciones 0001 a 0004 aplicadas |

## Casos verificados

- Configuración estructural de Kiro, Codex, OpenCode y Claude Code.
- Hook Kiro `PostFileSave` desactivado por defecto.
- UUID estable durante reintentos de un evento de archivo.
- Rechazo de UUID de proyecto inválido y rutas inseguras.
- Salida JSON por stdout y stderr separado en wrapper Kiro.
- Traducción del código de salida `20` mediante un ejecutable falso.
- Sobrescritura de `source_client` por wrappers de transporte.
- Persistencia y compatibilidad del núcleo mediante la suite completa y Docker.

## Límites de evidencia

No se ejecutaron Kiro, Codex, OpenCode ni Claude Code reales. Por ello, todos
los adaptadores de cliente están marcados como `NO VALIDADO EN CLIENTE REAL` y
los wrappers como `PROBADO CON MOCK` cuando corresponde. No se afirma
enforcement automático.
