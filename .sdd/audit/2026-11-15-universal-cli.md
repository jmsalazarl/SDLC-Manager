# Evidencia de validación: CLI universal

## Alcance

Validación del comando `sdlc-manager event process --stdin`, su compatibilidad con el servidor MCP, la persistencia SQLite, la salida JSON y la ejecución Docker.

## Comandos ejecutados

| Comando | Resultado observado |
| --- | --- |
| `uv run pytest -q` | `57 passed`, `1 skipped` por prueba Docker optativa y `28 warnings` de deprecación de `pytest-asyncio`. |
| `SDLC_MANAGER_RUN_DOCKER_TESTS=1 uv run pytest -q` | `58 passed`, `28 warnings` de deprecación de `pytest-asyncio`. |
| `uv run ruff check .` | Exitoso; todos los checks pasaron. |
| `uv run ruff format --check .` | Exitoso; 51 archivos formateados. |
| `uv run mypy src` | Exitoso; sin errores en 36 archivos fuente. |
| `uv run alembic upgrade head` | Exitoso; la base existente permaneció en la versión actual sin reinicialización. |
| `uv lock --check` | Exitoso; 49 paquetes resueltos sin cambios. |
| `sddnxp validate . --json` | Exitoso; `valid: true`, `issues: []`. |
| `docker build -t sdlc-manager:latest .` | Exitoso. |
| `SDLC_MANAGER_RUN_DOCKER_TESTS=1 uv run pytest tests/integration/test_cli.py::test_cli_runs_in_docker_with_persistent_volume -q` | `1 passed`; segunda invocación devolvió `DUPLICATE`. |

## Casos verificados

- Códigos distintos para evento informativo, `PASS`, `WARN` y `BLOCK`.
- Rechazo de JSON inválido, UTF-8 inválido, UUID inválido y entrada superior a 1 MiB.
- Conflicto de `event_id` y persistencia entre procesos separados.
- Error de bootstrap devuelto como `ERROR` sin código de éxito.
- JSON limpio en stdout y logs operativos en stderr.
- Ejecución nativa con `uv`.
- Ejecución contenedorizada con red deshabilitada y volumen SQLite persistente.
- Descubrimiento e invocación MCP existentes sin cambios de contrato.

## Códigos de salida

`0` información, `10` PASS, `20` WARN, `30` BLOCK, `40` rechazo, `50` error no reintentable y `51` error reintentable.

## Resultado

La spec `SPEC-005` queda validada y en estado `implemented`.

## Limitaciones

- Un código de salida no obliga por sí solo a un cliente externo a bloquear una operación.
- SQLite puede presentar bloqueo bajo concurrencia elevada.
- No se implementan Hooks ni adaptadores específicos de clientes.
