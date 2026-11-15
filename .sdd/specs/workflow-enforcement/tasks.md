# Implementation Plan: Workflow Enforcement

## Overview

Implementar enforcement ejecutable para gates de workflow, combinarlo con PolicyEngine, reforzar alcance de prácticas, registrar auditoría y mantener compatibilidad MCP. No implementar EventDispatcher, CLI ni Hooks.

## Tasks

- [x] 1. Completar el contrato SDD y validar la trazabilidad.
  - [x] 1.1 Revisar requirements.md, design.md y esta lista contra la auditoría B3-B6.
  - [x] 1.2 Validar la spec con sddnxp validate.
  - _Requerimientos: Todos_
  - _Capa: SDD_
  - _Depende de: ninguno_

- [x] 2. Extraer y compartir la evaluación de condiciones.
  - [x] 2.1 Crear ConditionEvaluator con operadores cerrados.
  - [x] 2.2 Adaptar PolicyEngine sin cambiar sus pruebas directas.
  - [x] 2.3 Agregar metadata workflow_checks a PolicyRule y PolicyLoader.
  - _Requerimientos: Requirement 3_
  - _Capa: Domain / Engines_
  - _Depende de: 1_

- [x] 3. Implementar Workflow Engine.
  - [x] 3.1 Crear resultados estructurados para PASS/WARN/BLOCK, no aplicable y errores.
  - [x] 3.2 Evaluar checks de HU y evidencia de las nueve etapas.
  - [x] 3.3 Diferenciar ausencia, PENDING, REJECTED y VERIFIED.
  - [x] 3.4 Evaluar condiciones de aplicabilidad y checks opcionales.
  - _Requerimientos: Requirement 1, Requirement 2_
  - _Capa: Engines_
  - _Depende de: 2_

- [x] 4. Integrar workflow y políticas en SdlcService.
  - [x] 4.1 Recuperar workflow/gate del proyecto.
  - [x] 4.2 Combinar decisiones con precedencia BLOCK > WARN > PASS.
  - [x] 4.3 Evitar duplicación de SDLC-003 mediante metadata de compatibilidad.
  - [x] 4.4 Mantener contratos y UUID MCP existentes.
  - _Requerimientos: Requirement 1, Requirement 3, Requirement 7_
  - _Capa: Application / MCP_
  - _Depende de: 3_

- [x] 5. Implementar excepciones seguras.
  - [x] 5.1 Agregar vigencia, responsable y metadata de autoridad.
  - [x] 5.2 Crear puerto ExceptionApprovalAuthority y implementación deny-all.
  - [x] 5.3 Mantener excepciones PENDING sin efecto de bypass.
  - [x] 5.4 Probar excepción pendiente, vencida y aprobada sin autoridad confiable.
  - _Requerimientos: Requirement 4_
  - _Capa: Domain / Engines / Persistence_
  - _Depende de: 3_

- [x] 6. Aislar prácticas por alcance.
  - [x] 6.1 Agregar project_id, owner_id y organization_id según corresponda.
  - [x] 6.2 Validar contexto requerido durante activación.
  - [x] 6.3 Evitar activar prácticas personales en otro actor y prácticas PROJECT en otro proyecto.
  - _Requerimientos: Requirement 5_
  - _Capa: Domain / Application / Infrastructure / Engines_
  - _Depende de: 1_

- [x] 7. Implementar auditoría.
  - [x] 7.1 Crear AuditRepository y repositorio SQLAlchemy.
  - [x] 7.2 Registrar evaluación de gate, BLOCK y cambios de evidencia.
  - [x] 7.3 Mantener payload mínimo sin secretos ni referencias sensibles.
  - _Requerimientos: Requirement 6_
  - _Capa: Application / Infrastructure_
  - _Depende de: 4_

- [x] 8. Crear migración aditiva y actualizar bootstrap.
  - [x] 8.1 Crear migración 0003_workflow_enforcement.
  - [x] 8.2 Preservar filas de 0001 y 0002 sin backfill de aprobaciones.
  - [x] 8.3 Mantener Docker y SQLite.
  - _Requerimientos: Requirement 7_
  - _Capa: Base de Datos / Docker_
  - _Depende de: 5, 6, 7_

- [x] 9. Implementar pruebas de enforcement y compatibilidad.
  - [x] 9.1 Probar HU incompleta y dependencias pendientes.
  - [x] 9.2 Probar diseño requerido/no requerido.
  - [x] 9.3 Probar testing y cierre sin evidencia.
  - [x] 9.4 Probar custom gate, excepción, combinación política/workflow y aislamiento.
  - [x] 9.5 Probar auditoría, MCP, migración y Docker.
  - _Requerimientos: Requirement 8 y todos_
  - _Capa: QA_
  - _Depende de: 4, 5, 6, 7, 8_

- [x] 10. Actualizar documentación y validación final.
  - [x] 10.1 Crear docs/workflow-enforcement-validation.md con resultados reales.
  - [x] 10.2 Actualizar docs/architecture.md y docs/mcp-tools.md si cambian contratos.
  - [x] 10.3 Ejecutar pytest, Ruff, mypy, sddnxp validate y docker build.
  - [x] 10.4 Marcar esta spec implementada solo con evidencia ejecutada.
  - _Requerimientos: Todos_
  - _Capa: Docs / QA_
  - _Depende de: 9_

## Notes

- No implementar EventDispatcher, CLI ni Hooks.
- No aceptar texto de un cliente como identidad confiable para excepciones.
- No permitir que prácticas produzcan BLOCK.
- No usar eval, exec ni expresiones ejecutables.
- No eliminar datos ni migraciones existentes.

## Task Dependency Graph

~~~json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2", "6"] },
    { "id": 2, "tasks": ["3"] },
    { "id": 3, "tasks": ["4", "5", "7"] },
    { "id": 4, "tasks": ["8"] },
    { "id": 5, "tasks": ["9"] },
    { "id": 6, "tasks": ["10"] }
  ]
}
~~~
