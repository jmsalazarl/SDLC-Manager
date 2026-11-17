# Requirements Document

## Introduction

SDLC Manager debe acompañar automáticamente el trabajo de ingeniería cuando un
cliente compatible emita un evento verificable. La funcionalidad debe reutilizar
el `SdlcEventProcessor`, mantener la memoria de experiencias contextual y
permitir instalar integraciones propias sin alterar configuraciones de terceros.

La integración con SDDNXP es opcional y únicamente de lectura. SDDNXP conserva
la responsabilidad sobre el gobierno SDD, sus artefactos, aprobaciones y
transiciones.

## Glosario

- **Engineering Companion:** capacidad de SDLC Manager que recupera contexto,
  experiencias y recomendaciones durante una sesión de desarrollo.
- **Adaptador:** integración específica de un proveedor que traduce un evento
  nativo al contrato `SdlcEvent`.
- **Instalador:** servicio que planifica, instala, verifica y retira únicamente
  recursos administrados por SDLC Manager.
- **Contexto visible:** salida que el cliente agrega a la conversación o al
  resultado de la operación, no solamente un evento persistido.
- **Reader SDDNXP:** lector opcional de información SDDNXP que no ejecuta
  transiciones ni modifica archivos.

## Requisitos

### Requirement 1: Procesamiento contextual

**User Story:** Como desarrollador, quiero recibir experiencias y prácticas
relevantes cuando modifico un componente, para prevenir errores recurrentes sin
recibir ruido innecesario.

#### Acceptance Criteria

1. WHEN un evento contiene un componente o archivos afectados, THE
   `SdlcEventProcessor` SHALL buscar únicamente experiencias aprobadas y
   aplicables al proyecto o alcance permitido.
2. WHEN una experiencia contextual es encontrada, THE adapter SHALL entregar su
   referencia y explicación al contexto visible del cliente.
3. IF no existe contexto suficiente, THEN THE processor SHALL procesar el evento
   sin exponer todas las experiencias almacenadas.
4. WHEN se repite el mismo evento, THE processor SHALL devolver el resultado
   idempotente sin repetir efectos persistentes.

### Requirement 2: Contrato de hooks

**User Story:** Como integrador, quiero traducir eventos nativos de cada cliente
al contrato común, para mantener una sola implementación de reglas.

#### Acceptance Criteria

1. WHEN un hook recibe JSON, THE adapter SHALL validar tamaño, estructura,
   rutas y UUID antes de invocar el CLI.
2. WHEN el cliente admite salida de hooks, THE adapter SHALL escribir una salida
   estructurada y visible para el agente.
3. IF un evento no puede normalizarse, THEN THE adapter SHALL devolver un
   rechazo estructurado y nunca `PASS`.

### Requirement 3: Instalación no destructiva

**User Story:** Como usuario, quiero instalar la integración de un proveedor sin
perder configuraciones existentes, para convivir con otros frameworks.

#### Acceptance Criteria

1. WHEN se ejecuta `integrations plan`, THE installer SHALL mostrar cambios
   previstos sin escribir archivos.
2. WHEN se ejecuta `integrations install`, THE installer SHALL crear o fusionar
   únicamente entradas con namespace de SDLC Manager.
3. IF existe un conflicto que no puede fusionarse de forma segura, THEN THE
   installer SHALL rechazar el cambio y conservar el archivo original.
4. WHEN se ejecuta `integrations uninstall`, THE installer SHALL retirar solo
   recursos identificados como administrados por SDLC Manager.
5. WHEN una escritura modifica un archivo existente, THE installer SHALL crear
   un backup y realizar una escritura atómica.

### Requirement 4: Proveedores independientes

**User Story:** Como usuario, quiero elegir el proveedor que utilizo, para no
instalar integraciones innecesarias.

#### Acceptance Criteria

1. WHEN se selecciona Kiro, Codex, OpenCode o Claude Code, THE installer SHALL
   generar únicamente recursos del proveedor seleccionado.
2. IF el proveedor no tiene un mecanismo de activación verificable en el
   entorno, THEN THE installer SHALL reportar `NOT_VERIFIED` o `PARTIAL` sin
   simular una activación automática.
3. WHEN el usuario configura MCP, THE provider SHALL usar el servidor
   `sdlc-manager` y el transporte stdio local.

### Requirement 5: SDDNXP opcional

**User Story:** Como equipo que usa SDDNXP, quiero que SDLC Manager use su
estado como contexto sin duplicar su governance.

#### Acceptance Criteria

1. WHEN existe `.sdd/config.yaml`, THE reader SHALL leer su identidad y estado
   de forma local y de solo lectura.
2. IF SDDNXP no está instalado o el archivo es inválido, THEN SDLC Manager SHALL
   continuar operando con sus propios motores.
3. THE reader SHALL NOT ejecutar aprobaciones, transiciones, migraciones ni
   comandos externos.

### Requirement 6: Seguridad y observabilidad

**User Story:** Como responsable de seguridad, quiero evitar ejecución de
payloads y filtración de secretos en hooks, para preservar el control del
entorno.

#### Acceptance Criteria

1. WHEN un adapter ejecuta el CLI, THE adapter SHALL usar argumentos
   estructurados y no shell concatenado.
2. WHEN una recomendación es WARN, THE adapter SHALL continuar sin bloquear.
3. IF un error técnico ocurre, THEN THE adapter SHALL distinguirlo de BLOCK y
   no convertirlo en `PASS`.
4. THE system SHALL registrar únicamente metadatos necesarios y SHALL NOT
   escribir secretos o contenido completo de archivos en logs.

## Alcance MVP

- Recuperación contextual automática basada en componente, archivos y contexto.
- Lector local opcional de `.sdd/config.yaml`.
- Wrappers visibles para hooks de Kiro y Claude Code.
- Plugin de observación para OpenCode.
- Paquete de integración Codex con MCP, skill y hook revisable.
- Instalador con `list`, `plan`, `install`, `status` y `uninstall`.
- Pruebas de instalación, idempotencia, preservación y propagación visible.

## Fuera De Alcance Inicial

- Cambios en SDDNXP.
- Aprobaciones automáticas.
- Enforcement global por defecto.
- Servicios externos, brokers o telemetría.
- Validación en clientes reales no instalados en el entorno.

## Preguntas Abiertas

La validación real de cada proveedor queda documentada como estado operativo y
no bloquea la implementación local de los adaptadores.
