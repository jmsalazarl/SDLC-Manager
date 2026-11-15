# Requirements Document

## Introduction

SDLC Manager necesita un punto de entrada independiente del cliente para procesar eventos normalizados del ciclo de vida. El procesador debe reutilizar los casos de uso existentes, activar evaluaciones cuando corresponda y mantener una respuesta trazable sin convertir una operación no evaluada en `PASS`.

## Glossary

- **SDLCEvent**: evento validado con identificador, tipo, cliente de origen, alcance y contexto.
- **SDLCEventProcessor**: servicio de aplicación que coordina eventos, servicios y auditoría.
- **EventProcessingResult**: respuesta persistible de un procesamiento.
- **Idempotencia**: reutilización del resultado cuando llega el mismo evento con el mismo contenido.
- **Conflicto de evento**: reutilización de `event_id` con una huella de payload diferente.
- **Cliente de origen**: etiqueta informativa del adaptador; no es una identidad confiable.

## Requirements

### Requirement 1: Contrato normalizado de eventos

**User Story:** Como adaptador de cliente, quiero enviar eventos con un contrato común, para reutilizar el mismo núcleo de gobernanza.

#### Acceptance Criteria

1. WHEN un evento válido es recibido, THE Event_Contract SHALL aceptar `event_id`, `event_type`, `source_client`, alcance, timestamp UTC, archivos afectados, contexto y `schema_version`.
2. WHERE el evento contiene un identificador UUID serializado como texto JSON, THE Event_Contract SHALL convertirlo a `uuid.UUID`.
3. IF un UUID, timestamp, ruta, tipo de evento o contexto no cumple las restricciones, THEN THE Event_Contract SHALL rechazar el evento sin ejecutar casos de uso.
4. WHERE el evento requiere proyecto o HU, THE Event_Contract SHALL rechazarlo cuando falte el identificador correspondiente.

### Requirement 2: Procesamiento coordinado

**User Story:** Como sistema consumidor, quiero procesar eventos sin depender de un cliente de IA, para integrar múltiples adaptadores futuros.

#### Acceptance Criteria

1. WHEN `file_changed` es procesado, THE SDLCEventProcessor SHALL identificar políticas, prácticas y experiencias relevantes sin ejecutar comandos ni código del contexto.
2. WHEN `user_story_started` es procesado, THE SDLCEventProcessor SHALL reutilizar el análisis existente de HU y devolver `BLOCK` cuando la HU no esté lista.
3. WHEN `task_completed` o `gate_evaluation_requested` es procesado, THE SDLCEventProcessor SHALL evaluar el gate configurado mediante `SdlcService`.
4. WHEN `sprint_started` es procesado, THE SDLCEventProcessor SHALL reutilizar el análisis de sprint existente.
5. WHERE el evento no requiere evaluación de gate, THE SDLCEventProcessor SHALL devolver estado procesado con `decision` nula y no SHALL reportar `PASS`.

### Requirement 3: Respuesta estructurada

**User Story:** Como adaptador, quiero una respuesta uniforme, para presentar decisiones y advertencias sin interpretar texto libre.

#### Acceptance Criteria

1. WHEN el procesamiento finaliza, THE EventProcessingResult SHALL incluir identificador, estado, decisión opcional, reglas, checks, prácticas, experiencias, evidencias faltantes, explicación, código de error, reintento y fecha.
2. IF el evento es desconocido o no está soportado, THEN THE EventProcessingResult SHALL devolver estado no soportado, decisión nula y código identificable.
3. IF ocurre un error funcional o técnico, THEN THE EventProcessingResult SHALL distinguirlo de `BLOCK` y nunca SHALL devolver `PASS`.

### Requirement 4: Idempotencia y conflictos

**User Story:** Como sistema local, quiero evitar reprocesar eventos, para no duplicar evaluaciones, cambios ni auditoría.

#### Acceptance Criteria

1. WHEN llega el mismo `event_id` con la misma huella de payload, THE SDLCEventProcessor SHALL devolver el resultado persistido sin repetir efectos.
2. IF llega el mismo `event_id` con una huella diferente, THEN THE SDLCEventProcessor SHALL rechazarlo con `EVENT_ID_REUSED` y no SHALL sobrescribir el resultado original.
3. WHERE un evento fue procesado antes de reiniciar la aplicación, THE SDLCEventProcessor SHALL recuperar su resultado desde SQLite.

### Requirement 5: Seguridad y aislamiento

**User Story:** Como responsable de seguridad, quiero que los eventos no puedan ejecutar acciones arbitrarias ni cruzar proyectos, para reducir riesgos de integración.

#### Acceptance Criteria

1. WHEN el contexto contiene datos arbitrarios, THE SDLCEventProcessor SHALL aceptar únicamente valores JSON acotados y no SHALL ejecutar expresiones, comandos o rutas del sistema.
2. WHERE un evento utiliza proyecto o HU, THE SDLCEventProcessor SHALL reutilizar repositorios que validen el aislamiento por proyecto.
3. IF una excepción inesperada ocurre, THEN THE SDLCEventProcessor SHALL registrar un error técnico trazable y SHALL marcar si es reintentable.
4. WHEN una auditoría es registrada, THE AuditRepository SHALL conservar identificadores mínimos y no SHALL almacenar secretos ni payload completo.

### Requirement 6: Compatibilidad MCP

**User Story:** Como cliente MCP, quiero invocar el procesador con la misma frontera stdio, para integrarlo sin cambiar las herramientas existentes.

#### Acceptance Criteria

1. WHEN el servidor MCP es iniciado, THE MCP_Interface SHALL conservar las herramientas existentes y exponer opcionalmente `process_sdlc_event`.
2. WHERE la herramienta recibe UUID como texto JSON, THE MCP_Interface SHALL conservar el schema `type: string` y `format: uuid`.
3. WHEN la herramienta es invocada, THE MCP_Interface SHALL delegar al mismo `SDLCEventProcessor` usado desde Python.

### Requirement 7: Validación y operación

**User Story:** Como equipo de mantenimiento, quiero comprobar el procesador sin servicios externos, para conservar el despliegue local offline.

#### Acceptance Criteria

1. WHEN se ejecutan las validaciones del repositorio, THE Project SHALL pasar pytest, Ruff, mypy, migraciones y construcción Docker disponibles.
2. WHERE se actualiza una base existente, THE Migration SHALL agregar la persistencia de eventos sin eliminar datos previos.
3. WHEN un evento válido es reprocesado después de reiniciar el contenedor, THE SDLCEventProcessor SHALL devolver el resultado anterior.

## Alcance MVP

- Contrato de eventos versión `1.0`.
- Procesamiento local en memoria de aplicación y persistencia SQLite.
- Idempotencia por `event_id` y huella SHA-256 del payload normalizado.
- Auditoría mínima y herramienta MCP `process_sdlc_event`.
- Eventos definidos en el contrato inicial.

## Fuera De Alcance Inicial

- Hooks, plugins y adaptadores específicos de Kiro, Codex, OpenCode o Claude Code.
- CLI universal.
- Brokers, colas, workers o bases de datos remotas.
- Autenticación corporativa o autoridad confiable para `source_client`.

## Preguntas Abiertas

No hay preguntas abiertas que bloqueen la implementación del MVP. La integración de identidad y el CLI universal se mantienen fuera de alcance y se documentan como próximos pasos.
