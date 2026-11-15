# Implementation Plan: Integraciones Multiagente

## Overview

Se implementan superficies opcionales para cuatro clientes, un contrato común
de wrappers y pruebas de contrato. No se modifican motores de dominio,
migraciones ni el contrato MCP existente.

## Tasks

- [x] 1. Definir la especificación de integración
  - Crear requirements, design y matriz de estados verificables.
  - _Requerimiento: Requirement 1, Requirement 5_
  - _Capa: Docs_
  - _Depende de: SPEC-005_

- [x] 2. Implementar el contrato común de adaptadores
  - Crear normalización acotada, UUID estable y wrapper de CLI sin shell.
  - _Requerimiento: Requirement 4, Requirement 5_
  - _Capa: Integraciones_
  - _Depende de: 1

- [x] 3. Implementar configuración e instrucciones por cliente
  - Crear MCP, instrucciones y archivos opcionales de Kiro, Codex, OpenCode y
    Claude Code.
  - _Requerimiento: Requirement 2, Requirement 3, Requirement 6_
  - _Capa: Integraciones_
  - _Depende de: 2

- [x] 4. Implementar el adaptador de evento Kiro de ejemplo
  - Mapear `PostFileSave` a `file_changed` y mantenerlo desactivado por defecto.
  - _Requerimiento: Requirement 1, Requirement 4, Requirement 5_
  - _Capa: Integraciones_
  - _Depende de: 2, 3

- [x] 5. Crear pruebas de contrato y wrappers
  - Verificar configuraciones, normalización, códigos, stdout y stderr.
  - _Requerimiento: Requirement 4, Requirement 5, Requirement 6_
  - _Capa: QA
  - _Depende de: 2, 3, 4

- [x] 6. Generar documentación de validación
  - Documentar capacidades oficiales, instalación, matrices, pruebas y
    limitaciones reales.
  - _Requerimiento: Requirement 1, Requirement 2, Requirement 3, Requirement 6_
  - _Capa: Docs
  - _Depende de: 5

## Notes

- No copiar configuraciones a directorios del usuario automáticamente.
- No incluir experiencias, proyectos ni bases SQLite en las integraciones.
- No declarar validación en cliente real sin ejecutar el cliente.

## Task Dependency Graph

```json
{
  "waves": [
    {"id": 0, "tasks": ["1"]},
    {"id": 1, "tasks": ["2"]},
    {"id": 2, "tasks": ["3", "4"]},
    {"id": 3, "tasks": ["5"]},
    {"id": 4, "tasks": ["6"]}
  ]
}
```
