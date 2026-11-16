# Implementation Plan: Sanitización De Knowledge Packs

## Overview

Eliminar referencias específicas del producto distribuible y retirar la
inferencia equivalente del código, conservando reglas declarativas y pruebas.

## Tasks

- [x] 1. Retirar conocimiento específico del código
  - Reemplazar la inferencia por evento genérico cuando haya archivos.
  - _Requerimiento: Requirement 1_
  - _Capa: Backend_
  - _Depende de: ninguno_

- [x] 2. Neutralizar paquetes demo, pruebas y documentación
  - Usar identificadores, rutas y evidencias ficticios y genéricos.
  - _Requerimiento: Requirement 2_
  - _Capa: Knowledge / QA / Docs_
  - _Depende de: 1_

- [x] 3. Actualizar trazabilidad y validaciones
  - Registrar ADR, auditoría y evidencia de búsqueda de referencias.
  - _Requerimiento: Requirement 3_
  - _Capa: Docs / QA_
  - _Depende de: 2_

## Notes

- No agregar secretos ni paquetes privados.
- No cambiar el contrato MCP ni la base de datos.
- La aplicabilidad seguirá dependiendo del YAML activo.

## Task Dependency Graph

```json
{
  "waves": [
    {"id": 0, "tasks": ["1"]},
    {"id": 1, "tasks": ["2"]},
    {"id": 2, "tasks": ["3"]}
  ]
}
```
