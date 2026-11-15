# Implementation Plan: Knowledge Architecture

## Overview

Implementar la separación entre workflow SDLC, memoria, prácticas y políticas mediante una migración Alembic aditiva, inicialización idempotente, servicios independientes, nuevas herramientas MCP y pruebas de actualización.

## Tasks

- [x] 1. Actualizar el dominio y los contratos de persistencia.
  - [x] 1.1 Agregar enums y entidades de workflow, memoria clasificada y práctica.
  - [x] 1.2 Ampliar `Project` y `EngineeringExperience` con referencias y metadatos compatibles.
  - [x] 1.3 Crear puertos de repositorio para workflow y prácticas.
  - _Requerimientos: Requirement 2, Requirement 3, Requirement 4_
  - _Capa: Domain_

- [x] 2. Implementar el esquema y migración Alembic.
  - [x] 2.1 Agregar modelos SQLAlchemy con nombres físicos en español.
  - [x] 2.2 Crear `0002_knowledge_architecture` sin borrar ni reinicializar datos.
  - [x] 2.3 Implementar backfill trazable de experiencias legacy.
  - _Requerimientos: Requirement 6_
  - _Capa: Base de Datos_
  - _Depende de: 1_

- [x] 3. Implementar plantilla e inicialización SDLC.
  - [x] 3.1 Crear y validar `knowledge/sdlc/default.yaml`.
  - [x] 3.2 Implementar carga, instalación idempotente y asignación a proyectos sin workflow.
  - [x] 3.3 Implementar consulta y personalización por copia.
  - _Requerimientos: Requirement 1, Requirement 2_
  - _Capa: Application / Infrastructure_
  - _Depende de: 1, 2_

- [x] 4. Implementar memoria y prácticas.
  - [x] 4.1 Persistir metadatos de memoria sin cargar datos iniciales.
  - [x] 4.2 Implementar registro, revisión y búsqueda compatible.
  - [x] 4.3 Implementar prácticas contextuales sin resultado BLOCK.
  - _Requerimientos: Requirement 3, Requirement 4, Requirement 5_
  - _Capa: Application / Engines_
  - _Depende de: 1, 2_

- [x] 5. Extender la interfaz MCP sin romper contratos existentes.
  - [x] 5.1 Agregar DTO y herramientas de workflow.
  - [x] 5.2 Agregar DTO y herramientas de memoria y prácticas.
  - [x] 5.3 Mantener herramientas actuales y validar JSON Schema.
  - _Requerimientos: Requirement 7_
  - _Capa: MCP_
  - _Depende de: 3, 4_

- [x] 6. Agregar pruebas y documentación.
  - [x] 6.1 Probar instalación limpia, memoria vacía e idempotencia.
  - [x] 6.2 Probar migración desde `0001`, persistencia y Docker.
  - [x] 6.3 Probar personalización, prácticas y regresión PASS/WARN/BLOCK.
  - [x] 6.4 Actualizar README, arquitectura, Docker, herramientas y ADR.
  - _Requerimientos: Todos_
  - _Capa: QA / Docs_
  - _Depende de: 2, 3, 4, 5_

## Notes

- No borrar bases SQLite ni datos existentes.
- No cargar experiencias, proyectos, HU o evidencias de demostración automáticamente.
- No convertir prácticas personales en políticas obligatorias sin aprobación explícita.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2"] },
    { "id": 2, "tasks": ["3", "4"] },
    { "id": 3, "tasks": ["5"] },
    { "id": 4, "tasks": ["6"] }
  ]
}
```
