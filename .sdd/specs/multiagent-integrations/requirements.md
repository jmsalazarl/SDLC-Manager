# Requirements Document

## Introduction

SDLC Manager debe poder instalarse desde distintos clientes compatibles con MCP
sin introducir dependencias de esos clientes en el núcleo. Esta especificación
define las superficies de integración, los adaptadores mínimos y las garantías
que se pueden afirmar con base en capacidades oficiales verificables.

## Glosario

- **Cliente:** herramienta que inicia MCP, ejecuta un hook o invoca el CLI.
- **Adaptador:** archivos de configuración, instrucciones y wrapper local que
  traducen una entrada del cliente al contrato existente de SDLC Manager.
- **Evento normalizado:** instancia válida de `SdlcEvent` procesada por el
  núcleo.
- **Enforcement:** capacidad del cliente para impedir una operación después de
  recibir un resultado `BLOCK`.
- **Validado en cliente real:** prueba ejecutada contra la instalación real del
  cliente, no solamente contra archivos o mocks.

## Requisitos

### Requirement 1: Integración independiente del núcleo

**User Story:** Como responsable de arquitectura, quiero integrar cada cliente
sin modificar los motores de dominio, para conservar un único comportamiento de
políticas y workflows.

#### Acceptance Criteria

1. WHEN un cliente instala su integración, THE `SdlcEventProcessor` SHALL
   mantenerse independiente de SDKs, plugins y APIs privadas del cliente.
2. WHERE una integración procesa un evento, THE adapter SHALL reutilizar el CLI
   o MCP existente y no duplicar reglas de Workflow, Policy, Practice o
   Experience Engine.
3. IF un cliente no tiene un contrato de eventos oficial verificado, THEN THE
   integration SHALL documentar la activación automática como no disponible.

### Requirement 2: Configuración MCP por cliente

**User Story:** Como desarrollador, quiero una configuración MCP específica por
cliente, para instalar solo la integración que utilizo.

#### Acceptance Criteria

1. WHEN se instala la integración, THE project SHALL provide a client-specific
   MCP configuration using the local stdio command.
2. WHEN el cliente consulta el servidor, THE integration SHALL expose the same
   tools and contracts definidos por el servidor MCP.
3. IF la configuración requiere copiar un archivo, THEN THE documentation SHALL
   indicar una operación que no sobrescriba archivos de usuario sin respaldo.

### Requirement 3: Instrucciones persistentes

**User Story:** Como usuario, quiero instrucciones persistentes sobre cuándo
consultar el sistema, para reducir omisiones sin convertir instrucciones en una
garantía de enforcement.

#### Acceptance Criteria

1. WHEN el cliente admite instrucciones persistentes, THE adapter SHALL provide
   un archivo de instrucciones con las herramientas y reglas de uso.
2. IF una instrucción recibe `decision: null` o un error técnico, THEN THE
   instructions SHALL prohibit treating that result as `PASS`.
3. WHERE una aprobación de evidencia o excepción sea requerida, THE instructions
   SHALL prohibit trusting the model or `source_client` as the approver.

### Requirement 4: Eventos y códigos de salida

**User Story:** Como integrador, quiero traducir eventos y códigos de salida de
forma estable, para reutilizar los mismos resultados en hooks o scripts.

#### Acceptance Criteria

1. WHEN un wrapper recibe un evento normalizado, THE adapter SHALL preserve
   `event_id` during retries and invoke `sdlc-manager event process --stdin`.
2. WHEN el CLI devuelve 0, 10, 20, 30, 40, 50 o 51, THE documentation SHALL
   mapear cada código a una semántica explícita del cliente.
3. IF un cliente no expone un mecanismo documentado para bloquear, THEN THE
   adapter SHALL present warnings and SHALL NOT claim effective `BLOCK`.

### Requirement 5: Seguridad y aislamiento

**User Story:** Como responsable de seguridad, quiero evitar que una integración
otorgue autoridad al modelo o ejecute payloads, para preservar la trazabilidad.

#### Acceptance Criteria

1. WHEN un adapter recibe JSON, THE adapter SHALL validate its size and structure
   without executing commands from the payload.
2. WHEN un adapter invokes the CLI, THE adapter SHALL use argument arrays and
   SHALL write only structured JSON to stdout.
3. IF una integración no puede verificarse contra el cliente real, THEN THE
   documentation SHALL mark it as `PROBADO CON MOCK` o `NO VERIFICADO`.

### Requirement 6: Instalación opcional y sin datos de demostración

**User Story:** Como operador, quiero instalar una sola integración sin alterar
la base de datos ni cargar datos ficticios.

#### Acceptance Criteria

1. WHEN se instala cualquier integración, THE adapter SHALL use the existing
   SQLite volume and SHALL NOT initialize demo experiences, projects or evidence.
2. WHEN se desinstala una integración, THE adapter SHALL leave the SDLC Manager
   database and user configuration intact.
3. WHERE la integración use el CLI, THE documentation SHALL describe la
   persistencia y las limitaciones de concurrencia de SQLite.

## Alcance MVP

- Configuración MCP local para Kiro, Codex, OpenCode y Claude Code.
- Instrucciones persistentes por cliente cuando la superficie oficial está
  documentada.
- Wrapper común de CLI y adaptador de ejemplo para `PostFileSave` de Kiro.
- Wrappers manuales de eventos normalizados para los otros clientes.
- Pruebas de contrato de archivos, normalización, códigos de salida y CLI.
- Matriz explícita de capacidades y estado de verificación.

## Fuera De Alcance Inicial

- Plugins o hooks corporativos específicos instalados automáticamente.
- Integración real ejecutada contra instalaciones de Kiro, Codex, OpenCode o
  Claude Code en este entorno.
- Identidad corporativa, aprobación de evidencias o excepciones.
- Bloqueo automático para clientes cuya semántica no haya sido verificada.

## Preguntas Abiertas

No existen preguntas que bloqueen la implementación de este alcance. La
validación en cliente real queda como criterio operativo posterior y se marca
explícitamente en el informe.
