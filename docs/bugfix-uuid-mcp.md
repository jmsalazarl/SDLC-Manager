# Corrección De UUID En La Interfaz MCP

## Causa raíz

Los DTO de entrada de la interfaz MCP usaban campos anotados directamente como `UUID` y configuraban `ConfigDict(strict=True)`. En Pydantic v2, el modo estricto no convierte una cadena JSON a `uuid.UUID`; por eso el argumento ya fallaba durante la validación del modelo generado para `get_applicable_rules`, antes de llegar al servicio de aplicación.

El rechazo no provenía del motor de políticas ni de la regla `DEMO-001`.

## Corrección

`src/sdlc_manager/application/schemas.py` define el alias `UuidInput` con `Annotated[UUID, BeforeValidator(parse_uuid)]`. El validador de frontera:

- conserva objetos `uuid.UUID` recibidos internamente;
- convierte cadenas UUID válidas a `uuid.UUID`;
- rechaza cadenas vacías, mal formadas y valores que no sean cadena o UUID;
- mantiene `strict=True` para el resto de los campos.

Los DTO con identificadores UUID fueron revisados: `CreateSprintInput`, `CreateStoryInput`, `ApplicableRulesInput`, `EvaluateGateInput`, `RegisterEvidenceInput`, `VerifyEvidenceInput`, `AnalyzeStoryInput` y `StartSprintInput`.

El JSON Schema publicado por MCP mantiene `type: string` y `format: uuid`. No se reemplazaron los UUID por strings y no se modificó funcionalmente `PolicyEngine`.

## Verificación del flujo MCP

La prueba de protocolo inicia el servidor mediante `stdio`, descubre la herramienta y envía el payload JSON requerido:

```json
{
  "input": {
    "project_id": "00e57f27-4f4c-47d0-be96-84f1b7162a99",
    "event": "file_change",
    "stage": "implementation",
    "changed_files": ["artifacts/sample.artifact"],
    "context": {}
  }
}
```

El resultado no contiene error de validación y detecta `DEMO-001`. La misma prueba verifica el rechazo de `""` y `"not-a-uuid"`.

## Archivos modificados

- `src/sdlc_manager/application/schemas.py`: conversión validada de UUID en la frontera MCP.
- `tests/unit/test_input_schemas.py`: casos positivos, inválidos y no-string para todos los DTO con UUID.
- `tests/integration/test_mcp_protocol.py`: invocación MCP real por `stdio`, validación del JSON Schema y payload positivo/negativo.
- `.sdd/specs/mcp-server-mvp/requirements.md`: requisito de contrato UUID.
- `.sdd/specs/mcp-server-mvp/design.md`: decisión de validación de frontera.
- `.sdd/specs/mcp-server-mvp/tasks.md`: tareas y trazabilidad de la corrección.
- `.sdd/traceability.yaml`: evidencia del requisito y validaciones.

## Validaciones ejecutadas

```bash
uv run pytest tests/integration/test_mcp_protocol.py -q
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Resultados observados:

- Prueba MCP por `stdio`: `3 passed`.
- Suite completa: `26 passed`.
- Ruff: sin errores.
- Formato Ruff: `34 files already formatted`.
- mypy: `Success: no issues found in 27 source files`.

Las pruebas muestran advertencias de deprecación de `pytest-asyncio` relacionadas con las APIs de política de eventos de Python 3.14; no afectan el resultado funcional.
