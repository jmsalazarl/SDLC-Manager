# Validación De Corrección UUID MCP

## Objetivo

Corregir la recepción de UUID serializados como strings JSON en los argumentos MCP sin eliminar la validación estricta ni modificar el motor de políticas.

## Hallazgo

`ConfigDict(strict=True)` rechazaba las cadenas JSON cuando los campos del DTO estaban anotados directamente como `UUID`. La validación ocurría antes de invocar el servicio de aplicación.

## Cambio validado

Se agregó un `BeforeValidator` limitado a los campos UUID de los DTO. Las cadenas válidas se convierten a `uuid.UUID`; los valores vacíos, mal formados o de tipo no permitido se rechazan. El esquema MCP conserva `type: string` y `format: uuid`.

## Evidencia

- Payload positivo de `get_applicable_rules` procesado por `stdio`.
- Regla `DEMO-001` detectada para `artifacts/sample.artifact`.
- Payloads con UUID vacío y mal formado rechazados por MCP.
- DTOs UUID revisados mediante pruebas unitarias.
- `PolicyEngine` sin cambios funcionales.

## Resultados

| Validación | Resultado |
| --- | --- |
| `uv run pytest tests/integration/test_mcp_protocol.py -q` | 3 passed |
| `uv run pytest -q` | 26 passed |
| `uv run ruff check .` | Passed |
| `uv run ruff format --check .` | Passed |
| `uv run mypy src` | Passed; 27 archivos fuente |

## Archivos de evidencia

- `src/sdlc_manager/application/schemas.py`
- `tests/unit/test_input_schemas.py`
- `tests/integration/test_mcp_protocol.py`
- `docs/bugfix-uuid-mcp.md`
