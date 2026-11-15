# Herramientas MCP

Todas las herramientas usan entradas Pydantic y devuelven objetos estructurados. El transporte del MVP es `stdio`.

| Herramienta | Propósito |
| --- | --- |
| `health_check` | Comprueba base local, transporte y cantidad de políticas. |
| `list_policies` | Lista reglas con filtros `status` y `severity`. |
| `get_applicable_rules` | Busca reglas para evento, etapa, archivos y componente. |
| `evaluate_gate` | Evalúa y persiste un gate para una HU. |
| `register_experience` | Crea una experiencia en `PENDING`. |
| `search_experiences` | Busca experiencias aprobadas o, si se solicita, pendientes. |
| `review_experience` | Aprueba o rechaza memoria técnica. |
| `register_evidence` | Registra evidencia en `PENDING`. |
| `verify_evidence` | Registra aprobación humana o rechazo. |
| `analyze_user_story` | Detecta descripción, criterios, dependencias y reglas aplicables. |
| `start_sprint` | Analiza todas las historias de un proyecto o sprint. |
| `create_project` | Prepara un proyecto local para el análisis. |
| `create_sprint` | Crea un sprint local. |
| `create_user_story` | Crea una historia local. |
| `get_sdlc_workflow` | Consulta el workflow asignado a un proyecto. |
| `customize_sdlc_workflow` | Crea una versión derivada del workflow de un proyecto. |
| `register_practice` | Registra una práctica en estado pendiente. |
| `review_practice` | Aprueba o rechaza una práctica. |
| `list_practices` | Lista prácticas aprobadas o pendientes. |
| `get_applicable_practices` | Obtiene recomendaciones aprobadas para un contexto. |
| `process_sdlc_event` | Procesa un evento normalizado con idempotencia local y devuelve una decisión estructurada. |

## Workflow

`get_sdlc_workflow` recibe `project_id` y devuelve la versión, etapas, gates, verificaciones y excepciones del proyecto.

`customize_sdlc_workflow` recibe `project_id`, `name`, `version`, etapas y excepciones opcionales. La operación crea una copia derivada; no modifica la plantilla de origen. Las excepciones nuevas quedan `PENDING` hasta contar con una aprobación registrada.

## Memoria y prácticas

`register_experience` acepta opcionalmente `memory_type`, `technology`, `category`, `scope`, `author` y `related_experience_ids`. La experiencia queda `PENDING`.

`register_practice` acepta `context`, `triggers`, `intervention_message`, `severity`, `scope` y una experiencia de origen opcional. La práctica queda `PENDING` y no puede producir `BLOCK`. Solo una práctica aprobada aparece en `get_applicable_practices`.

Las prácticas `PROJECT`, `PERSONAL` y `ORGANIZATION` requieren respectivamente `project_id`, `owner_id` u `organization_id`. `get_applicable_practices` recibe el contexto de esos identificadores para mantener el aislamiento.

## Ejemplo de evaluación

Entrada conceptual:

```json
{
  "project_id": "uuid-del-proyecto",
  "user_story_id": "uuid-de-la-historia",
  "gate": "task_completion",
  "context": {
    "event": "file_change",
    "changed_files": ["forms/customer.wpx"]
  }
}
```

Respuesta cuando faltan evidencias:

```json
{
  "result": "BLOCK",
  "gate": "task_completion",
  "triggered_rules": ["SDLC-001"],
  "missing_evidence": ["production_version", "comparison_result", "closure_evidence"],
  "pending_evidence": [],
  "rejected_evidence": [],
  "not_applicable_checks": [],
  "workflow_findings": [{"check": "closure_evidence", "status": "MISSING"}],
  "evaluation_errors": [],
  "deduplicated_policy_rules": [],
  "explanation": "Faltan evidencias obligatorias para reglas aprobadas"
}
```

`evaluate_gate` combina el resultado del workflow y de las políticas con precedencia `BLOCK > WARN > PASS`. Los checks compartidos se declaran con `workflow_checks` en la política para evitar evaluar dos veces la misma condición. Una excepción solo puede omitir controles cuando está vigente, tiene referencia y responsable, y una autoridad confiable la autoriza; la implementación predeterminada no autoriza excepciones.

## process_sdlc_event

Recibe un objeto de evento con `event_id`, `event_type`, `source_client`, alcance, `timestamp`, archivos afectados, contexto y `schema_version`. Los UUID serializados como texto JSON se convierten internamente a `uuid.UUID` y conservan `format: uuid` en JSON Schema.

Los eventos sin evaluación de gate devuelven `decision: null`; esto no representa `PASS`. Los reintentos del mismo evento devuelven `status: DUPLICATE` y no repiten evaluaciones ni auditorías. Si el mismo `event_id` contiene otro payload, devuelve `EVENT_ID_REUSED`.

## Errores

Los errores de validación de entrada son rechazados por el esquema MCP. Los errores de dominio incluyen proyecto o historia inexistente, política inválida y referencia de evidencia no permitida. No se aceptan rutas locales absolutas ni segmentos `..`.

