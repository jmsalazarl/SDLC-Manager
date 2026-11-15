# Requirements Document

## Introduction

Esta especificación convierte el workflow SDLC declarativo de SDLC Manager en un flujo ejecutable y verificable. El cambio debe conservar la interfaz MCP existente, integrar los gates configurados con las políticas YAML, reforzar el aislamiento de prácticas, registrar auditoría y mantener una ruta futura para aprobaciones corporativas sin simular identidad confiable.

El alcance no incluye EventDispatcher, CLI, Hooks ni adaptadores específicos de clientes. El resultado debe poder invocarse desde los casos de uso Python existentes y desde las herramientas MCP actuales.

## Glossary

| Término | Definición |
| --- | --- |
| Workflow | Flujo versionado de etapas, gates, checks y excepciones asignado a un proyecto. |
| Gate | Punto de control de una etapa que puede producir PASS, WARN o BLOCK. |
| Check | Verificación declarativa de una condición de HU o de una evidencia. |
| Evidencia aplicable | Evidencia requerida por un check activo para el gate evaluado. |
| Excepción | Registro con motivo, vigencia, responsable y aprobación potencial para un gate específico. |
| Aprobación confiable | Aprobación emitida por un mecanismo de autoridad inyectado y verificable; un texto recibido desde MCP no es suficiente. |
| Práctica personal | Recomendación cuyo alcance requiere coincidencia con el actor propietario. |
| Auditoría | Registro mínimo de decisiones y transiciones relevantes en TAUDITORIA. |

## Requirements

### Requirement 1: Evaluación ejecutable del workflow

**User Story:** Como responsable de un proyecto, quiero que el gate asignado al proyecto se evalúe con sus checks y condiciones, para que la configuración del workflow tenga efecto real.

#### Acceptance Criteria

1. WHEN se evalúa un gate para una HU, THE Workflow_Enforcement SHALL recuperar el workflow asignado al proyecto y el gate correspondiente.
2. WHEN un gate contiene un check obligatorio incumplido, THE Workflow_Enforcement SHALL producir BLOCK.
3. WHEN un gate contiene un check opcional incumplido, THE Workflow_Enforcement SHALL producir WARN y SHALL NOT producir BLOCK por ese check.
4. WHEN una condición de aplicabilidad es falsa, THE Workflow_Enforcement SHALL marcar el check como NOT_APPLICABLE y SHALL NOT producir WARN o BLOCK por ese check.
5. IF el workflow o gate configurado no puede evaluarse, THEN THE Workflow_Enforcement SHALL evitar PASS y devolver un error estructurado de evaluación.

### Requirement 2: Evaluación de checks y evidencias

**User Story:** Como mantenedor del SDLC, quiero que los checks de las nueve etapas se traduzcan a condiciones verificables, para evitar gates declarativos sin efecto.

#### Acceptance Criteria

1. WHEN se evalúa story_refinement, THE Workflow_Enforcement SHALL verificar description_present.
2. WHEN se evalúa acceptance_criteria, THE Workflow_Enforcement SHALL verificar acceptance_criteria_present.
3. WHEN se evalúa dependency_review, THE Workflow_Enforcement SHALL verificar dependencies_resolved.
4. WHEN se evalúa development, THE Workflow_Enforcement SHALL verificar story_ready.
5. WHEN se evalúa design_approval, THE Workflow_Enforcement SHALL omitir el gate si design_required es false y SHALL exigir evidencia aprobada si design_required es true.
6. WHEN se evalúa technical_review, testing, deployment_preparation o closure, THE Workflow_Enforcement SHALL exigir la evidencia aprobada asociada al check obligatorio.
7. WHEN una evidencia está PENDING o REJECTED, THE Workflow_Enforcement SHALL diferenciarla de una evidencia ausente y SHALL not considerarla VERIFIED.
8. WHEN una evaluación de workflow y una política YAML representan el mismo check, THE Application_Service SHALL evitar contar la condición dos veces y SHALL conservar la trazabilidad de la política relacionada.

### Requirement 3: Combinación con Policy Engine

**User Story:** Como mantenedor de políticas, quiero combinar gates de workflow con reglas YAML, para conservar controles existentes y agregar controles configurables.

#### Acceptance Criteria

1. WHEN existen resultados de workflow y de Policy_Engine, THE Application_Service SHALL combinar ambos con precedencia BLOCK > WARN > PASS.
2. WHEN una regla YAML aprobada produce BLOCK, THE Application_Service SHALL mantener BLOCK aunque los checks de workflow produzcan PASS.
3. WHEN solo existen advertencias, THE Application_Service SHALL producir WARN.
4. WHEN no existen incumplimientos obligatorios, advertencias ni errores, THE Application_Service SHALL producir PASS.
5. IF existe un error de evaluación, THEN THE Application_Service SHALL devolverlo diferenciadamente y SHALL NOT producir PASS.

### Requirement 4: Excepciones seguras

**User Story:** Como responsable técnico, quiero registrar excepciones con alcance temporal y responsable, para documentar casos autorizables sin permitir bypasses no confiables.

#### Acceptance Criteria

1. WHEN se registra una excepción, THE Workflow_Service SHALL conservar gate, motivo, responsable, vigencia y condición.
2. WHEN una excepción está PENDING, THE Workflow_Enforcement SHALL mantener los controles activos.
3. WHEN una excepción tiene APPROVED pero no existe una autoridad de aprobación confiable, THE Workflow_Enforcement SHALL mantener los controles activos.
4. WHEN una excepción aprobada está fuera de vigencia, THE Workflow_Enforcement SHALL mantener los controles activos.
5. WHEN una excepción activa autorizada coincide con el gate, THE Workflow_Enforcement SHALL registrar la excepción aplicada y no omitir controles no cubiertos por ella.
6. THE Domain SHALL mantener una interfaz de autoridad de aprobación inyectable para una integración corporativa futura.

### Requirement 5: Aislamiento de prácticas

**User Story:** Como usuario, quiero que las prácticas personales y de proyecto solo se apliquen a su alcance, para evitar recomendaciones o preferencias de otros usuarios o proyectos.

#### Acceptance Criteria

1. WHEN una práctica tiene alcance PROJECT, THE Practice_Engine SHALL exigir coincidencia con project_id.
2. WHEN una práctica tiene alcance PERSONAL, THE Practice_Engine SHALL exigir coincidencia con el actor propietario.
3. WHEN falta el ámbito requerido, THE Practice_Engine SHALL no activar la práctica.
4. THE Practice_Engine SHALL never produce BLOCK.
5. WHEN una práctica es aplicable, THE Practice_Engine SHALL conservar origen, alcance y estado de aprobación en la respuesta.

### Requirement 6: Auditoría de enforcement

**User Story:** Como auditor, quiero consultar trazabilidad mínima de gates, bloqueos y evidencias, para conocer qué proyecto, HU y regla originaron una decisión.

#### Acceptance Criteria

1. WHEN se evalúa un gate, THE Audit_Service SHALL registrar proyecto, HU, gate, resultado y evaluación.
2. WHEN una evaluación produce BLOCK, THE Audit_Service SHALL registrar reglas activadas y motivo sin incluir secretos ni referencias sensibles.
3. WHEN una evidencia se registra o cambia de estado, THE Audit_Service SHALL registrar proyecto, HU, política, evidencia y estado.
4. THE Audit_Service SHALL use TAUDITORIA and SHALL preserve existing audit rows.
5. WHEN se registra auditoría, THE Audit_Service SHALL store only the minimum context needed for traceability.

### Requirement 7: Compatibilidad y migración

**User Story:** Como mantenedor del producto, quiero evolucionar el enforcement sin romper clientes MCP ni bases existentes.

#### Acceptance Criteria

1. WHEN un cliente invoca herramientas MCP existentes, THE MCP_Interface SHALL conservar nombres y contratos principales.
2. WHEN un cliente envía UUID como string JSON, THE MCP_Interface SHALL convertirlo a UUID y conservar el esquema string/uuid.
3. WHEN se actualiza una base existente, THE Migration SHALL be additive and SHALL preserve projects, experiences, evidence, evaluations and audit rows.
4. THE Project SHALL continue to support SQLite, Alembic and Docker without client-specific dependencies.
5. THE Domain SHALL contain one implementation of workflow/policy rules independent of MCP.

### Requirement 8: Pruebas verificables

**User Story:** Como equipo de ingeniería, quiero pruebas de enforcement y regresión, para validar el comportamiento antes de integrar eventos automáticos.

#### Acceptance Criteria

1. THE Test_Suite SHALL cover missing acceptance criteria and pending dependencies.
2. THE Test_Suite SHALL cover required design without approval and design not required.
3. THE Test_Suite SHALL cover testing and closure without verified evidence.
4. THE Test_Suite SHALL cover custom gate checks, pending exceptions and simultaneous workflow/policy applicability.
5. THE Test_Suite SHALL cover project/practice isolation, MCP compatibility and additive migration.

## Alcance MVP

- Ejecutar los gates de workflow desde evaluate_gate y desde el caso de uso Python.
- Compartir un evaluador cerrado de condiciones entre workflow y políticas.
- Mantener compatibilidad con PolicyEngine y herramientas MCP.
- Registrar auditoría mínima.
- Mantener excepciones no confiables sin efecto de bypass.
- Aislar prácticas personales, de proyecto y de organización mediante contexto explícito.

## Fuera De Alcance Inicial

- EventDispatcher, SDLCEventProcessor, CLI y Hooks.
- Autenticación corporativa o integración con directorios.
- Aprobación corporativa real de excepciones.
- Microservicios, colas, PostgreSQL o vector database.
- Adaptadores específicos de Kiro, Codex, OpenCode o Claude Code.

## Preguntas Abiertas

No hay preguntas que bloqueen la implementación del enforcement local. La autoridad corporativa de aprobación queda como dependencia futura y se representará mediante un puerto que por defecto no autoriza excepciones.
