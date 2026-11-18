# Requirements Document

## Introduction

SDLC Manager necesita conectar su procesador de eventos con clientes de desarrollo y con etapas de integración continua sin duplicar motores de dominio. Esta especificación define los contratos, límites y criterios para emitir eventos normalizados, recuperar experiencias contextuales y registrar resultados como evidencia pendiente de verificación humana.

La integración es opcional por proveedor. SDLC Manager debe continuar funcionando mediante MCP y CLI aunque ningún proveedor externo esté instalado. Las capacidades automáticas se deben clasificar según el contrato oficial verificable de cada proveedor y no se deben inferir a partir de archivos de ejemplo o instrucciones Markdown.

## Glosario

- **Proveedor:** cliente o sistema que produce un evento y consume el resultado de SDLC Manager.
- **Adaptador:** componente externo al núcleo que traduce un evento del proveedor al contrato `SdlcEvent` y el resultado al formato visible del proveedor.
- **Evento normalizado:** evento validado por `SdlcEventProcessor`, con `event_id` estable y contexto limitado.
- **Evidencia pendiente:** registro de resultado que permanece en estado `PENDING` hasta una verificación humana autorizada.
- **Contrato oficial verificable:** documentación pública del proveedor que define eventos, entrada, salida, tiempos o control de decisión de una integración.
- **Visibilidad:** condición en la que la recomendación llega al contexto que el agente o usuario puede consultar, no solamente a SQLite.
- **Activación automática:** ejecución iniciada por un hook, plugin o etapa de CI sin una invocación manual de una herramienta MCP.
- **Estado de capacidad:** `IMPLEMENTADO`, `PROBADO CON MOCK`, `VALIDADO EN CLIENTE REAL`, `PARTIAL`, `NOT_VERIFIED` o `UNSUPPORTED`.

## Requirements

### Requirement 1: Contrato común de eventos

**User Story:** Como mantenedor, quiero que todos los proveedores emitan el mismo evento normalizado, para conservar un único procesador de políticas, workflow, prácticas y experiencias.

#### Acceptance Criteria

1. WHEN un adaptador recibe una señal del proveedor, THE Provider_Adapter SHALL construir un `SdlcEvent` válido sin importar dependencias del proveedor dentro de `src/sdlc_manager`.
2. WHEN un evento se reintenta, THE Provider_Adapter SHALL conservar el mismo `event_id` y el mismo contenido normalizado.
3. IF la señal no contiene los datos mínimos para el evento, THEN THE Provider_Adapter SHALL devolver un rechazo estructurado y SHALL NOT convertirlo en `PASS`.
4. WHEN el evento llega al núcleo, THE SdlcEventProcessor SHALL reutilizar sus validaciones, idempotencia y servicios existentes.

### Requirement 2: Activación por proveedor

**User Story:** Como usuario, quiero instalar únicamente la integración del proveedor que utilizo, para recibir recomendaciones automáticas sin modificar otras configuraciones.

#### Acceptance Criteria

1. WHEN se selecciona un proveedor, THE Integration_Installer SHALL planificar e instalar solamente los recursos de ese proveedor.
2. WHEN un proveedor tiene un contrato oficial verificable, THE Provider_Adapter SHALL documentar sus eventos, formato de entrada, formato de salida y límites de enforcement.
3. IF un proveedor no tiene un contrato oficial verificable para una señal, THEN THE Integration_Installer SHALL marcar esa capacidad como `NOT_VERIFIED` o `UNSUPPORTED` y SHALL NOT simular una activación automática.
4. WHEN el proveedor no está instalado, THE Sdlc_Manager SHALL continuar operando mediante MCP, CLI y procesamiento explícito de eventos.

### Requirement 3: MCP e instrucciones persistentes

**User Story:** Como desarrollador, quiero consultar memoria, prácticas y políticas desde cada cliente, para mantener una experiencia consistente entre sesiones.

#### Acceptance Criteria

1. WHEN se configura MCP, THE Provider_Adapter SHALL usar el servidor `sdlc-manager` y el transporte local `stdio` ya soportado.
2. WHEN el proveedor admite instrucciones persistentes, THE Provider_Adapter SHALL entregar instrucciones que indiquen cuándo consultar experiencias, prácticas, workflow y evidencias.
3. IF una respuesta tiene `decision: null`, THEN THE Persistent_Instructions SHALL prohibit interpretarla como `PASS`.
4. IF una respuesta es `ERROR`, `REJECTED` o `NOT_VERIFIED`, THEN THE Provider_Adapter SHALL presentarla como error o estado no evaluable y SHALL NOT ocultarla como advertencia satisfecha.

### Requirement 4: Eventos de CI y hooks

**User Story:** Como mantenedor, quiero emitir eventos desde cada etapa de CI y desde hooks compatibles, para conservar trazabilidad de las comprobaciones ejecutadas.

#### Acceptance Criteria

1. WHEN una etapa de CI inicia o termina una comprobación definida, THE CI_Adapter SHALL emitir un evento normalizado con la etapa, el resultado disponible y un `event_id` estable.
2. WHEN un hook oficial del proveedor se ejecuta, THE Provider_Adapter SHALL traducir únicamente los campos definidos por el contrato oficial del proveedor.
3. WHEN una fuente no permite distinguir inicio y finalización, THE Adapter SHALL registrar el evento disponible y SHALL documentar la limitación sin inventar una transición.
4. IF el proveedor no entrega un canal de salida visible para el agente, THEN THE Adapter SHALL marcar la propagación como `NOT_VERIFIED` y SHALL preserve el registro local sin afirmar visibilidad.

### Requirement 5: Evidencias pendientes y verificación humana

**User Story:** Como responsable de ingeniería, quiero que los resultados automáticos queden pendientes, para que ningún modelo o proveedor se convierta en aprobador confiable.

#### Acceptance Criteria

1. WHEN un evento produce un resultado que se usa como evidencia, THE Evidence_Manager SHALL registrar la evidencia en estado `PENDING`.
2. WHEN un proveedor o modelo solicita marcar una evidencia como verificada, THE Evidence_Manager SHALL rechazar la operación si no existe una aprobación humana autorizada y trazable.
3. WHEN una evidencia está `PENDING` o `REJECTED`, THE Policy_Engine SHALL conservar el comportamiento actual para requisitos obligatorios y SHALL NOT tratarla como verificada.
4. WHEN una persona autorizada verifica una evidencia, THE Audit_Repository SHALL registrar el identificador de evidencia, proyecto, HU, regla, responsable y fecha sin guardar secretos ni el payload completo.

### Requirement 6: Visibilidad y semántica de decisiones

**User Story:** Como usuario, quiero distinguir recomendaciones de bloqueos efectivos, para no asumir que un código o mensaje modifica el comportamiento del cliente.

#### Acceptance Criteria

1. WHEN el procesador devuelve `WARN`, THE Adapter SHALL mostrar la recomendación sin bloquear una operación.
2. WHEN el procesador devuelve `BLOCK`, THE Adapter SHALL aplicar el bloqueo solamente si el contrato oficial del proveedor permite enforcement para ese evento.
3. IF el proveedor no permite enforcement, THEN THE Adapter SHALL mostrar `BLOCK` como advertencia no ejecutable y SHALL reportar la capacidad como `PARTIAL` o `UNSUPPORTED`.
4. WHEN ocurre un error técnico, THE Adapter SHALL distinguirlo de un bloqueo funcional y SHALL preserve `retryable` y `error_code`.

### Requirement 7: Instalación no destructiva

**User Story:** Como usuario, quiero instalar y retirar integraciones sin perder configuraciones, para convivir con otras herramientas.

#### Acceptance Criteria

1. WHEN se ejecuta `integrations plan`, THE Integration_Installer SHALL mostrar los cambios sin escribir archivos.
2. WHEN se ejecuta `integrations install`, THE Integration_Installer SHALL hacer merge o escritura aditiva únicamente en recursos administrados por SDLC Manager.
3. IF existe un conflicto no fusionable, THEN THE Integration_Installer SHALL rechazar el cambio, conservar el archivo original y reportar el conflicto.
4. WHEN se ejecuta `integrations uninstall`, THE Integration_Installer SHALL retirar solamente recursos identificados como propios y SHALL conservar SQLite, instrucciones y configuraciones ajenas.
5. WHEN se modifica un archivo existente, THE Integration_Installer SHALL crear un backup y usar una escritura atómica cuando el formato lo permita.

### Requirement 8: Seguridad, aislamiento y límites

**User Story:** Como responsable de seguridad, quiero que los adaptadores no ejecuten payloads ni crucen proyectos, para reducir riesgos de automatización.

#### Acceptance Criteria

1. WHEN un adaptador recibe JSON, THE Adapter SHALL validar tamaño, estructura, rutas y UUID antes de invocar el CLI.
2. WHEN un adaptador ejecuta el CLI, THE Adapter SHALL utilizar argumentos estructurados y SHALL NOT concatenar comandos de shell.
3. WHEN un evento contiene `project_id`, THE SdlcEventProcessor SHALL conservar el aislamiento por proyecto de los repositorios existentes.
4. THE Provider_Adapter SHALL NOT tratar `source_client`, el modelo o un payload como identidad confiable para aprobar evidencias o excepciones.
5. WHEN se registran logs, THE Integration SHALL omitir secretos, contenido completo de archivos y payloads completos.

### Requirement 9: Compatibilidad y migración progresiva

**User Story:** Como mantenedor, quiero agregar proveedores sin romper MCP, CLI ni eventos existentes, para evolucionar la integración gradualmente.

#### Acceptance Criteria

1. WHEN se instala una integración nueva, THE MCP_Interface SHALL conservar las herramientas y esquemas existentes.
2. WHEN un adaptador usa el CLI, THE Adapter SHALL invocar `sdlc-manager event process --stdin` y SHALL conservar los códigos `0`, `10`, `20`, `30`, `40`, `50` y `51`.
3. WHEN se actualiza una integración, THE Installer SHALL preservar el estado de SQLite, las experiencias y las evidencias existentes.
4. WHEN una capacidad solo se probó con mocks, THE Documentation SHALL marcarla como `PROBADO CON MOCK` y SHALL NOT declararla validada en cliente real.

### Requirement 10: Validación por proveedor

**User Story:** Como equipo de mantenimiento, quiero una matriz verificable por proveedor, para separar hechos comprobados de capacidades pendientes.

#### Acceptance Criteria

1. WHEN se valida una integración, THE Test_Suite SHALL comprobar configuración, emisión, procesamiento, visibilidad y preservación de archivos.
2. WHEN no existe una instalación real del proveedor, THE Validation_Report SHALL marcar la capacidad como `NOT_TESTED` o `PROBADO CON MOCK`.
3. THE Validation_Report SHALL distinguir `IMPLEMENTADO`, `PROBADO CON MOCK`, `VALIDADO EN CLIENTE REAL`, `PARTIAL`, `NOT_VERIFIED` y `UNSUPPORTED`.

## Matriz inicial de capacidades verificadas

| Proveedor | Capacidades oficiales verificables para esta spec | Estado inicial de diseño |
|---|---|---|
| Kiro | MCP local `stdio`; configuración de usuario/proyecto; hooks como `SessionStart`, `PreToolUse`, `PostToolUse`, `FileSave` y `Pre Task Execution` en superficies/versiones documentadas | `PARTIAL`: requiere validar versión instalada, stdin/stdout y propagación real |
| Codex | MCP; `AGENTS.md`; plugins con MCP y hooks de ciclo de vida en plugins de escritorio instalados manualmente | `PARTIAL`: no se asume un contrato de hooks CLI estable; la ruta base es MCP y `AGENTS.md` |
| OpenCode | MCP; plugins locales o publicados; API de hooks de plugin y configuración `opencode.json(c)` | `PARTIAL`: requiere fijar versión y probar eventos, salida visible y enforcement |
| Claude Code | MCP local `stdio`; hooks con eventos documentados, JSON de salida, `PreToolUse` y códigos de salida; `FileChanged` es informativo y no bloquea | `PARTIAL`: validar versiones y ejecución real del cliente |

## Alcance MVP de la especificación

- Contrato de evento estable para CI y proveedores.
- Reutilización de `SdlcEventProcessor`, CLI, MCP e `IntegrationInstaller` existentes.
- Registro de resultados automáticos como evidencias `PENDING`.
- Configuración e instrucciones aditivas por proveedor.
- Matriz de capacidades con estados verificables.
- Pruebas con fixtures, mocks y clientes reales cuando estén instalados.

## Fuera De Alcance Inicial

- Cambios en los motores Policy, Workflow, Practice o Experience sin incompatibilidad demostrada.
- Aprobación automática de evidencias o excepciones.
- Dependencias específicas de proveedores dentro de `src/sdlc_manager`.
- Integraciones remotas, credenciales permanentes, brokers o bases de datos adicionales.
- Declarar validado un proveedor que no se haya ejecutado realmente.

## Preguntas Abiertas

1. ¿Qué versión mínima de cada proveedor se debe soportar en la primera implementación real?
2. ¿Qué etapas concretas de CI deben producir evidencia en el primer adaptador?
3. ¿Qué rol humano o mecanismo local autorizado puede verificar evidencias sin introducir todavía identidad externa?
