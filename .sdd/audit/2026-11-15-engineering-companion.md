# Evidencia de validación — Engineering Companion

## Alcance

Se implementó la integración contextual opcional de SDLC Manager con
adaptadores externos, instalador no destructivo y reader local de SDDNXP. No se
modificó SDDNXP ni se ejecutaron instalaciones en perfiles reales.

## Especificación

- Spec: `.sdd/specs/engineering-companion/`
- Identificador: `SPEC-008`
- Estado: `implemented`
- Archivos: `requirements.md`, `design.md`, `tasks.md`, `spec.yaml`

## Validaciones ejecutadas

| Comando o prueba | Resultado real |
|---|---|
| `UV_CACHE_DIR=/tmp/sdlc-uv-cache uv run pytest -q` | 73 passed, 1 skipped, 28 warnings |
| `uv run pytest tests/integration/test_engineering_companion.py tests/integration/test_multiagent_integrations.py -q` | 16 passed, 1 warning |
| `UV_CACHE_DIR=/tmp/sdlc-uv-cache uv run ruff check .` | PASS |
| `UV_CACHE_DIR=/tmp/sdlc-uv-cache uv run ruff format --check .` | PASS |
| `UV_CACHE_DIR=/tmp/sdlc-uv-cache uv run mypy src integrations` | PASS, 52 archivos |
| `git diff --check` | PASS |
| `UV_CACHE_DIR=/tmp/sdlc-uv-cache uv run pytest tests/integration/test_mcp_protocol.py -q` | 3 passed |
| `sddnxp validate . --json` | PASS, `valid: true`, `issues: []` |
| `docker build -t sdlc-manager:latest .` | PASS |
| `SDLC_MANAGER_RUN_DOCKER_TESTS=1 uv run pytest tests/integration/test_cli.py::test_cli_runs_in_docker_with_persistent_volume -q` | 1 passed |
| Instalación y desinstalación de Kiro, Claude Code, OpenCode y Codex en directorio temporal | PASS |
| Hook Claude con proceso falso y salida `additionalContext` | PASS |
| Migraciones Alembic 0001 a 0004 en SQLite temporal | PASS |

## Clientes disponibles en el entorno

- Codex CLI `0.169.0`: versión detectada; plugin real no ejecutado.
- Kiro CLI `1.0.242`: la consulta `kiro-cli mcp list` alcanzó el cliente, pero
  terminó con error porque el perfil temporal no estaba autenticado.
- OpenCode `1.19.0`: configuración temporal aceptada por
  `opencode debug config`; el plugin no se ejecutó dentro de una sesión real.
- Claude Code `2.1.73`: versión detectada; hook y MCP no se ejecutaron en una
  sesión autenticada.

## Evidencia de seguridad

- Las pruebas usan directorios temporales y no modifican perfiles reales.
- No se registran secretos ni contenido completo de archivos.
- El instalador preserva entradas externas y rechaza conflictos.
- La consulta SDDNXP no ejecuta comandos ni escribe archivos.
- Las rutas absolutas recibidas por Claude se convierten a rutas relativas
  solamente cuando están dentro del proyecto.

## Estado de capacidades

| Capacidad | Estado |
|---|---|
| Núcleo único mediante `SdlcEventProcessor` | IMPLEMENTADO y probado |
| Recuperación contextual por componente | IMPLEMENTADO y probado |
| Instalador `list`, `plan`, `install`, `status`, `uninstall` | IMPLEMENTADO y probado en filesystem temporal |
| Configuración MCP aditiva | IMPLEMENTADO y probado |
| Propagación Claude mediante `additionalContext` | IMPLEMENTADO y probado con mock |
| Ejecución real Kiro | NO VERIFICADO por autenticación |
| Ejecución real Codex | NO VERIFICADO |
| Ejecución real OpenCode del plugin | NO VERIFICADO; solo configuración parcial |
| Ejecución real Claude Code | NO VERIFICADO |
| Enforcement real de `BLOCK` en clientes | NO IMPLEMENTADO |

## Limitaciones

La validación real requiere ejecutar sesiones de cada cliente con un proyecto de
prueba, una identidad autenticada y los permisos que el usuario autorice. La
instalación no activa bloqueos por defecto y el núcleo continúa funcionando sin
SDDNXP.

## Archivos de evidencia

- `docs/engineering-companion-validation.md`
- `tests/integration/test_engineering_companion.py`
- `tests/integration/test_multiagent_integrations.py`
- `.sdd/specs/engineering-companion/`
- `.sdd/adrs/0011-engineering-companion-multiagente.md`
