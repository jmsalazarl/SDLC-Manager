# Implementation Plan: SDLC Event Processor

## Overview

Implementar el contrato normalizado, el procesador de aplicación, persistencia idempotente, auditoría, herramienta MCP, pruebas y documentación. No implementar adaptadores externos, Hooks ni CLI.

## Tasks

- [x] 1. Crear y validar la especificación SDD.
  - [x] 1.1 Documentar requisitos, diseño, límites y criterios EARS.
  - [x] 1.2 Validar dependencias con SPEC-001, SPEC-002 y SPEC-003.
  - _Requerimientos: Todos_
  - _Capa: SDD_
  - _Depende de: ninguno_

- [x] 2. Implementar contratos de eventos y respuestas.
  - [x] 2.1 Agregar enums cerrados y DTOs Pydantic.
  - [x] 2.2 Validar UUID JSON, timestamps UTC, alcance y límites de payload.
  - [x] 2.3 Definir respuestas de error, no soportado y decisión nula.
  - _Requerimientos: Requirement 1, Requirement 3, Requirement 5_
  - _Capa: Domain / Application_
  - _Depende de: 1_

- [x] 3. Implementar persistencia e idempotencia.
  - [x] 3.1 Agregar entidad, puerto y repositorio SQLAlchemy.
  - [x] 3.2 Crear migración Alembic aditiva `0004_event_processor`.
  - [x] 3.3 Implementar huella canónica y detección de conflicto.
  - _Requerimientos: Requirement 4, Requirement 7_
  - _Capa: Domain / Infrastructure_
  - _Depende de: 2_

- [x] 4. Implementar SDLCEventProcessor.
  - [x] 4.1 Coordinar `SdlcService` sin duplicar reglas.
  - [x] 4.2 Implementar acciones de los ocho eventos.
  - [x] 4.3 Registrar auditoría y diferenciar BLOCK de ERROR.
  - [x] 4.4 Recuperar resultados duplicados sin repetir efectos.
  - _Requerimientos: Requirement 2, Requirement 3, Requirement 4, Requirement 5_
  - _Capa: Application_
  - _Depende de: 2, 3_

- [x] 5. Integrar MCP.
  - [x] 5.1 Agregar `process_sdlc_event` sin modificar herramientas existentes.
  - [x] 5.2 Verificar schema UUID y salida estructurada.
  - _Requerimientos: Requirement 6_
  - _Capa: MCP_
  - _Depende de: 4_

- [x] 6. Crear pruebas funcionales y de compatibilidad.
  - [x] 6.1 Probar eventos válidos, inválidos y no soportados.
  - [x] 6.2 Probar duplicados, conflictos, persistencia y aislamiento.
  - [x] 6.3 Probar formularios, prácticas, HU, evidencias y gates.
  - [x] 6.4 Probar MCP, migración y Docker.
  - _Requerimientos: Todos_
  - _Capa: QA_
  - _Depende de: 4, 5_

- [x] 7. Documentar y validar.
  - [x] 7.1 Crear `docs/event-processor-validation.md` con resultados reales.
  - [x] 7.2 Actualizar arquitectura, herramientas y trazabilidad.
  - [x] 7.3 Ejecutar pytest, Ruff, mypy, migraciones, `sddnxp validate` y Docker.
  - _Requerimientos: Requirement 7_
  - _Capa: Docs / QA_
  - _Depende de: 6_

## Notes

- No implementar Hooks, plugins, adaptadores externos ni CLI.
- No usar `source_client` como identidad confiable.
- No ejecutar comandos, expresiones ni rutas recibidas en `context`.
- No cambiar contratos MCP existentes sin necesidad documentada.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2"] },
    { "id": 2, "tasks": ["3", "4"] },
    { "id": 3, "tasks": ["5"] },
    { "id": 4, "tasks": ["6"] },
    { "id": 5, "tasks": ["7"] }
  ]
}
```
