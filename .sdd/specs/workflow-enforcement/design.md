# Diseño De Workflow Enforcement

## Overview

Se agrega un Workflow Engine determinista que evalúa el gate del workflow asignado al proyecto. El engine no duplica el lenguaje de condiciones del Policy Engine: ambos usan un evaluador cerrado compartido. SdlcService coordina workflow, políticas, evidencias, prácticas y auditoría, conserva la salida PASS/WARN/BLOCK y mantiene las herramientas MCP existentes.

Las excepciones quedan registradas con vigencia y responsable, pero ninguna excepción podrá omitir controles mientras no exista una autoridad de aprobación confiable inyectada. El valor por defecto será deny-all.

## Architecture

~~~mermaid
flowchart LR
    MCP[MCP Interface] --> APP[SdlcService]
    APP --> WF[Workflow Engine]
    APP --> POL[Policy Engine]
    WF --> COND[Condition Evaluator]
    POL --> COND
    APP --> EVID[Evidence Repository]
    APP --> AUD[Audit Repository]
    APP --> PRACT[Practice Engine]
    WF --> AUTH[Exception Approval Authority]
    APP --> REPO[SQLAlchemy Repositories]
    REPO --> DB[(SQLite)]
    DB --> MIG[Alembic]
~~~

Responsabilidades:

- Workflow Engine: checks de gate, aplicabilidad, evidencias, excepciones y resultados de workflow.
- Condition Evaluator: operadores cerrados reutilizados por workflow y políticas.
- Policy Engine: reglas YAML, severidad, aprobación, triggers y decisiones de políticas.
- SdlcService: orquestación, precedencia de resultados, persistencia de evaluación y auditoría.
- Practice Engine: recomendaciones contextualizadas sin BLOCK.
- Audit Repository: escritura mínima en TAUDITORIA.
- Exception Approval Authority: interfaz para autoridad futura; implementación local deny-all.

## Components and Interfaces

### Workflow Engine

Archivo propuesto: src/sdlc_manager/engines/workflow_engine.py.

Entrada:

- SdlcGate.
- Contexto normalizado de proyecto/HU.
- Evidencias agrupadas por tipo y estado.
- Excepciones del workflow.
- Fecha de evaluación.

Salida:

- resultado PASS/WARN/BLOCK.
- checks obligatorios incumplidos.
- checks opcionales que generan WARN.
- checks NOT_APPLICABLE.
- evidencias ausentes, PENDING o REJECTED.
- errores de evaluación.
- excepciones consideradas y aplicadas.

Checks iniciales:

| Check | Evaluación |
| --- | --- |
| description_present | Campo description no vacío. |
| acceptance_criteria_present | Lista de criterios no vacía. |
| dependencies_resolved | Todas las dependencias tienen estado resuelto. |
| story_ready | description, criterios y dependencias satisfechos. |
| design_evidence | Evidencia VERIFIED cuando design_required es true. |
| review_evidence | Evidencia VERIFIED del mismo tipo. |
| test_evidence | Evidencia VERIFIED del mismo tipo. |
| deployment_evidence | Evidencia VERIFIED del mismo tipo. |
| closure_evidence | Evidencia VERIFIED del mismo tipo. |

Los checks desconocidos serán errores de evaluación y no producirán PASS.

### Condition Evaluator

Archivo propuesto: src/sdlc_manager/engines/condition_evaluator.py.

Se extrae la lógica de operadores actualmente implementada en PolicyEngine. El lenguaje permitido conserva all, any, equals, not_equals, exists, contains, in y file_extension_matches. No se agrega eval, exec ni expresiones libres.

### Policy Engine

Se agrega metadata opcional workflow_checks a PolicyRule y al esquema YAML. SDLC-003 se identifica como compatibilidad del check story_ready. En una evaluación coordinada, la regla sigue siendo visible y trazable, pero su condición no se cuenta dos veces cuando el Workflow Engine ya evaluó el mismo check. Las pruebas unitarias directas de PolicyEngine conservan su comportamiento actual.

### Practice Engine

EngineeringPractice recibe project_id, owner_id y organization_id opcionales según el alcance. La activación compara:

- PROJECT: project_id del contexto.
- PERSONAL: actor_id del contexto con owner_id.
- ORGANIZATION: organization_id del contexto con organization_id.

Si falta el ámbito, la práctica no se activa. Las prácticas nunca se consideran parte de la decisión BLOCK.

### Excepción y autoridad

SdlcException agrega responsible, valid_from, valid_until, approval_source y approval_reference. Se agrega ExceptionApprovalAuthority en domain/ports. DenyAllExceptionApproval siempre retorna false. Una excepción solo se considera activa cuando:

1. status es APPROVED.
2. existe autoridad confiable que la autoriza.
3. tiene responsable y referencia de aprobación.
4. está dentro de vigencia.
5. coincide con el gate y su condición.

No se agrega una herramienta MCP que pueda simular una aprobación confiable.

### Auditoría

Se agrega AuditRepository y SqlAlchemyAuditRepository. SdlcService registra:

- gate_evaluated.
- gate_blocked.
- evidence_registered.
- evidence_status_changed.

El campo DETALLE conserva JSON mínimo con evaluation_id, user_story_id, gate, result, rule_ids, evidence_id y status cuando corresponda. No se registran referencias de archivos, secretos ni contenido libre de evidencias.

## Data Models

La migración 0003_workflow_enforcement agrega:

- Responsable, vigencia y metadata de autoridad en TEXCEPCIONDLC.
- Proyecto, propietario y organización en TPRACTICA.
- Índices para alcance de prácticas.

Los hallazgos detallados de workflow se devuelven en la salida de `evaluate_gate` y no requieren una nueva tabla en esta fase.

Las columnas nuevas deben ser nullable para filas legacy. El backfill no debe inventar propietarios ni aprobaciones. Las excepciones legacy permanecen no autorizadas y las prácticas legacy sin alcance suficiente no se activan automáticamente.

## API Contracts

Las herramientas MCP existentes no cambian de nombre ni de estructura principal.

La salida de evaluate_gate se amplía de forma compatible con campos opcionales:

~~~json
{
  "result": "BLOCK",
  "gate": "testing_complete",
  "triggered_rules": ["SDLC-001"],
  "missing_evidence": ["test_evidence"],
  "pending_evidence": [],
  "rejected_evidence": [],
  "not_applicable_checks": [],
  "workflow_findings": [],
  "evaluation_errors": [],
  "deduplicated_policy_rules": [],
  "explanation": "Falta evidencia obligatoria"
}
~~~

Las entradas UUID continúan usando UuidInput y el esquema JSON string/uuid.

## Error Handling

- Gate no configurado: error de aplicación y no PASS.
- Check desconocido: evaluation_error y BLOCK preventivo.
- Condición inválida: evaluation_error y BLOCK preventivo.
- Evidencia ausente: missing_evidence.
- Evidencia PENDING: pending_evidence.
- Evidencia REJECTED: rejected_evidence.
- Excepción PENDING/no confiable/vencida: control activo y detalle de excepción no aplicable.
- Auditoría fallida: error técnico explícito; no ocultar la decisión.

## Testing Strategy

- Unit tests de ConditionEvaluator y WorkflowEngine.
- Integración de cada gate de default.yaml.
- Evidencia ausente, PENDING, REJECTED y VERIFIED.
- Diseño requerido/no requerido.
- Excepción pending y excepción aprobada sin autoridad.
- Custom gate y custom workflow.
- Deducción de SDLC-003 cuando el workflow evalúa story_ready.
- Prácticas personales/proyecto/organización aisladas.
- Auditoría de gate, bloqueo y evidencia.
- MCP discovery, UUID JSON y salida compatible.
- Migración 0003 desde 0002 con preservación de filas.
- Docker build y arranque con migraciones.

## Decisiones Técnicas

1. El Workflow Engine se separa del Policy Engine para evitar mezclar configuración de proceso con reglas YAML.
2. El lenguaje de condiciones se comparte para evitar duplicar operadores y validaciones.
3. La precedencia es BLOCK > WARN > PASS; errores no producen PASS.
4. La autoridad de excepciones es deny-all por defecto para no aceptar aprobaciones simuladas.
5. La auditoría usa TAUDITORIA existente y una nueva interfaz, sin introducir otro sistema de persistencia.
6. Los cambios de esquema son aditivos y compatibles con SQLite mediante Alembic.

## Riesgos e Incertidumbres

- La aplicación real de excepciones depende de una autoridad futura.
- Un cliente que no invoque evaluate_gate puede omitir el control; EventDispatcher queda fuera de alcance.
- La semántica de checks personalizados debe permanecer cerrada y versionada.
- Las prácticas organization requieren identidad organizacional futura.

## Correctness Properties

1. Un gate obligatorio incumplido nunca produce PASS.
2. Una excepción PENDING nunca reduce los controles.
3. Una práctica PERSONAL nunca aparece sin actor propietario coincidente.
4. Una práctica PROJECT nunca aparece para otro project_id.
5. Una política aprobada con BLOCK mantiene BLOCK aunque workflow produzca PASS.
6. Una decisión auditada conserva project_id, user_story_id y rule_ids cuando existan.
7. La migración no elimina filas ni crea aprobaciones confiables por backfill.
