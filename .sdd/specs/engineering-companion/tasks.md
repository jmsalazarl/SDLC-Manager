# Implementation Plan: Engineering Companion Multiagente

## Overview

Se implementan recuperación contextual, reader opcional de SDDNXP, adapters
visibles y un instalador no destructivo. No se modifica SDDNXP ni se ejecutan
instalaciones en perfiles reales durante las pruebas.

## Tasks

- [x] 1. Implementar resolución contextual y reader SDDNXP
  - Inferir componente seguro y limitar experiencias relevantes.
  - Leer `.sdd/config.yaml` únicamente en modo lectura.
  - _Requerimiento: Requirement 1, Requirement 5_
  - _Capa: Application / Infrastructure_
  - _Depende de: ninguno_

- [x] 2. Implementar runner visible para hooks
  - Normalizar payloads, invocar el CLI sin shell y mostrar resultados al agente.
  - _Requerimiento: Requirement 2, Requirement 6_
  - _Capa: Integraciones_
  - _Depende de: 1_

- [x] 3. Implementar recursos por proveedor
  - Crear hooks o plugins propios para Kiro, Claude Code, OpenCode y Codex.
  - _Requerimiento: Requirement 4_
  - _Capa: Integraciones_
  - _Depende de: 2_

- [x] 4. Implementar instalador seguro
  - Agregar list, plan, install, status y uninstall con backups y conflictos.
  - _Requerimiento: Requirement 3, Requirement 4_
  - _Capa: Infrastructure / CLI_
  - _Depende de: 3_

- [x] 5. Agregar pruebas automatizadas
  - Cubrir contexto, propagación visible, idempotencia, preservación y rollback.
  - _Requerimiento: Requirement 1, Requirement 2, Requirement 3, Requirement 6_
  - _Capa: QA_
  - _Depende de: 1, 2, 4

- [x] 6. Actualizar documentación y evidencias SDD
  - Documentar instalación, clientes, SDDNXP y estados de validación.
  - _Requerimiento: Requirement 4, Requirement 5_
  - _Capa: Docs_
  - _Depende de: 5

## Notes

- No copiar configuraciones a perfiles reales durante pruebas.
- No incluir experiencias, secretos ni bases de datos en los assets.
- No declarar un cliente como validado sin ejecución real.

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
