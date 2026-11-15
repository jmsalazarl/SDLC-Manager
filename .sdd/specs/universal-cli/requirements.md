# Requirements Document

## Introduction

SDLC Manager necesita una interfaz de línea de comandos que permita a Hooks, plugins, scripts y pipelines invocar el mismo `SdlcEventProcessor` sin iniciar MCP ni depender de un modelo de IA. La interfaz debe conservar el servidor MCP existente, producir JSON limpio por `stdout` y comunicar una clasificación operativa mediante códigos de salida estables.

## Glossary

- **CLI universal**: comando local `sdlc-manager event process --stdin` para procesar un evento JSON.
- **Evento informativo**: evento procesado sin una decisión de gate; su `decision` es `null`.
- **Adaptador**: cliente externo que traduce sus eventos y códigos de salida a los contratos de SDLC Manager.
- **Salida limpia**: `stdout` contiene únicamente un objeto JSON y `stderr` contiene logs operativos.

## Requirements

### Requirement 1: Comando CLI

**User Story:** Como adaptador local, quiero enviar un evento JSON por stdin, para invocar el procesador sin iniciar MCP.

#### Acceptance Criteria

1. WHEN se ejecuta `sdlc-manager event process --stdin`, THE Universal_CLI SHALL leer un único evento JSON desde stdin.
2. WHEN el evento es válido, THE Universal_CLI SHALL delegar en `SdlcEventProcessor` y devolver `EventProcessingResult` como JSON.
3. WHERE no se proporcionan argumentos, THE Application_Entry_Point SHALL conservar el inicio del servidor MCP existente.
4. WHEN el CLI procesa un evento, THE Universal_CLI SHALL no iniciar una sesión ni un transporte MCP.

### Requirement 2: Salida y códigos de estado

**User Story:** Como Hook o pipeline, quiero interpretar decisiones y errores de forma estable, para decidir cómo presentar o detener una operación.

#### Acceptance Criteria

1. WHEN la respuesta tiene decisión `PASS`, THE Universal_CLI SHALL devolver el código estable de PASS.
2. WHEN la respuesta tiene decisión `WARN`, THE Universal_CLI SHALL devolver el código estable de WARN.
3. WHEN la respuesta tiene decisión `BLOCK`, THE Universal_CLI SHALL devolver el código estable de BLOCK.
4. WHEN la respuesta tiene `decision: null` y estado procesado, THE Universal_CLI SHALL devolver el código de evento informativo y no SHALL tratarlo como PASS.
5. IF el evento es inválido o rechazado, THEN THE Universal_CLI SHALL devolver el código de entrada rechazada.
6. IF ocurre un error técnico, THEN THE Universal_CLI SHALL distinguir errores reintentables de errores no reintentables y no SHALL devolver un código de éxito.
7. WHEN se produce una respuesta, THE Universal_CLI SHALL escribir JSON válido únicamente en stdout.

### Requirement 3: Persistencia e idempotencia

**User Story:** Como operador local, quiero que las invocaciones separadas compartan el almacenamiento existente, para evitar duplicar evaluaciones.

#### Acceptance Criteria

1. WHEN se recibe un evento, THE Universal_CLI SHALL conservar `event_id` y delegar la huella al procesador existente.
2. WHEN el mismo evento se ejecuta en dos procesos, THE Universal_CLI SHALL devolver `DUPLICATE` en la segunda ejecución sin repetir efectos.
3. IF el mismo `event_id` tiene otro payload, THEN THE Universal_CLI SHALL devolver `EVENT_ID_REUSED` sin sobrescribir el resultado original.
4. WHEN se inicia el CLI, THE Universal_CLI SHALL ejecutar migraciones idempotentes sin reinicializar la base existente.

### Requirement 4: Seguridad y límites

**User Story:** Como responsable de seguridad, quiero controlar la entrada y el canal de salida, para reducir riesgos de ejecución desde automatizaciones.

#### Acceptance Criteria

1. WHEN stdin supera el límite configurado del CLI, THE Universal_CLI SHALL rechazar la entrada sin procesarla.
2. IF stdin no contiene UTF-8 o JSON válido, THEN THE Universal_CLI SHALL devolver una respuesta estructurada de rechazo.
3. WHEN se procesa el payload, THE Universal_CLI SHALL conservar las validaciones de Pydantic y no SHALL ejecutar comandos, expresiones ni rutas recibidas.
4. WHEN se registran logs, THE Universal_CLI SHALL escribirlos en stderr y no SHALL incluir el payload completo ni secretos.
5. WHERE el CLI se ejecuta en Docker, THE Runtime SHALL documentar los permisos necesarios del volumen SQLite.

### Requirement 5: Compatibilidad operativa

**User Story:** Como mantenedor, quiero conservar MCP y soportar ejecución nativa y Docker, para no romper integraciones existentes.

#### Acceptance Criteria

1. WHEN se ejecutan las herramientas MCP existentes, THE MCP_Interface SHALL conservar sus contratos y comportamiento.
2. WHEN se ejecuta el CLI nativo con uv, THE Universal_CLI SHALL utilizar el mismo bootstrap de configuración, Alembic y SQLite.
3. WHEN se ejecuta el CLI dentro de Docker, THE Universal_CLI SHALL procesar stdin sin abrir puertos ni requerir red.
4. WHERE un adaptador consume un código de salida, THE Documentation SHALL indicar que cada cliente define cómo convertirlo en advertencia o bloqueo efectivo.

### Requirement 6: Validación

**User Story:** Como equipo de mantenimiento, quiero pruebas automatizadas de la frontera CLI, para detectar regresiones de protocolo y persistencia.

#### Acceptance Criteria

1. WHEN se ejecutan las pruebas, THE Project SHALL cubrir PASS, WARN, BLOCK, eventos informativos, entradas inválidas, duplicados y conflictos.
2. WHEN se ejecuta una invocación en proceso separado, THE Project SHALL comprobar persistencia SQLite y salida JSON limpia.
3. WHEN se construye Docker, THE Project SHALL comprobar ejecución CLI y compatibilidad MCP anterior.
