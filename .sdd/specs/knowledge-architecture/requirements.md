# Requirements Document

## Introduction

Esta especificación evoluciona SDLC Manager para separar el workflow configurable del SDLC, la memoria de ingeniería, las prácticas técnicas y las políticas obligatorias. La migración debe preservar los datos existentes, mantener la compatibilidad MCP y permitir una instalación limpia con una plantilla SDLC predeterminada.

## Glossary

| Término | Definición |
| --- | --- |
| Workflow | Flujo versionado de etapas, gates, verificaciones y excepciones del SDLC. |
| Etapa | Momento ordenado del workflow, como desarrollo o testing. |
| Gate | Punto de control que puede producir PASS, WARN o BLOCK. |
| Memoria | Registro de incidente, bug, lección, recomendación o preferencia. |
| Práctica | Recomendación contextual que no bloquea por defecto. |
| Plantilla | Versión instalable e inmutable del workflow predeterminado. |
| Personalización | Copia versionada de un workflow para un proyecto o alcance superior. |

## Requirements

### Requirement 1: Workflow SDLC predeterminado

**User Story:** Como equipo de desarrollo, quiero disponer de un workflow SDLC inicial, para aplicar controles consistentes sin configurar el sistema manualmente.

#### Acceptance Criteria

1. WHEN se inicializa una base de datos nueva, THE Workflow_Initializer SHALL instalar una única versión identificable de la plantilla predeterminada.
2. WHERE la instalación es nueva, THE Default_Workflow SHALL incluir refinamiento de HU, criterios de aceptación, dependencias, diseño, desarrollo, revisión técnica, testing, preparación de despliegue y cierre.
3. WHEN se reinicia el servidor, THE Workflow_Initializer SHALL conservar la plantilla existente sin duplicarla ni sobrescribirla.
4. WHEN se ejecuta una actualización, THE Migration SHALL conservar plantillas, proyectos y datos existentes.

### Requirement 2: Workflow configurable

**User Story:** Como responsable de un proyecto, quiero personalizar etapas, gates, verificaciones y excepciones, para adaptar el SDLC sin modificar la plantilla global.

#### Acceptance Criteria

1. WHEN un proyecto personaliza el workflow, THE Workflow_Service SHALL crear una versión derivada sin modificar la plantilla de origen.
2. WHEN se consulta un workflow, THE Workflow_Service SHALL devolver etapas ordenadas, gates, verificaciones obligatorias y excepciones autorizadas.
3. IF una excepción no tiene aprobación registrada, THEN THE Workflow_Service SHALL conservarla como no autorizada.

### Requirement 3: Engineering Memory

**User Story:** Como desarrollador o QA, quiero registrar memoria técnica clasificada, para recuperar experiencias sin convertirlas automáticamente en controles obligatorios.

#### Acceptance Criteria

1. WHEN se registra memoria, THE Memory_Service SHALL conservar su tipo, contexto, componente, tecnología, categoría, alcance, autor, fecha y estado de revisión.
2. WHERE una instalación es nueva, THE Memory_Repository SHALL permanecer vacío.
3. WHEN se registra una memoria, THE Memory_Service SHALL dejarla pendiente de revisión.
4. WHEN una memoria pendiente se consulta normalmente, THE Memory_Service SHALL excluirla de resultados aprobados.
5. WHEN una memoria se relaciona con otra memoria, THE Memory_Service SHALL persistir la relación sin duplicar el contenido principal.

### Requirement 4: Engineering Practices

**User Story:** Como líder técnico, quiero registrar prácticas contextuales, para emitir recomendaciones sin convertir preferencias en bloqueos.

#### Acceptance Criteria

1. WHEN se registra una práctica, THE Practice_Service SHALL conservar contexto, activadores, mensaje, severidad, alcance, origen y aprobación.
2. WHEN una práctica aplicable se evalúa, THE Practice_Engine SHALL emitir una recomendación o WARN y SHALL NOT emitir BLOCK por sí misma.
3. WHERE una práctica tiene origen en memoria no aprobada, THE Practice_Service SHALL impedir que se convierta en política obligatoria.
4. WHEN se aprueba una práctica, THE Practice_Service SHALL registrar quién y cuándo la aprobó.

### Requirement 5: Separación de políticas

**User Story:** Como mantenedor de controles, quiero separar reglas obligatorias de prácticas recomendadas, para preservar la trazabilidad de los bloqueos.

#### Acceptance Criteria

1. WHEN se evalúa un gate, THE Policy_Engine SHALL conservar PASS, WARN y BLOCK para políticas YAML aprobadas.
2. WHEN se evalúa una práctica, THE Policy_Engine SHALL NOT tratarla como regla obligatoria sin una aprobación explícita y una conversión documentada.
3. WHERE una política obligatoria existente es aplicable, THE Policy_Engine SHALL conservar su comportamiento anterior.

### Requirement 6: Persistencia y migración segura

**User Story:** Como operador, quiero actualizar una instalación existente sin pérdida de datos, para adoptar la nueva arquitectura de conocimiento de forma segura.

#### Acceptance Criteria

1. WHEN se ejecuta la migración desde `0001_initial`, THE Migration SHALL crear las nuevas estructuras mediante cambios aditivos.
2. WHEN existen proyectos, experiencias o evidencias, THE Migration SHALL conservar sus identificadores y contenido.
3. WHEN se ejecuta la inicialización más de una vez, THE Initializer SHALL ser idempotente.
4. WHERE se construye Docker, THE Image SHALL incluir plantillas pero SHALL NOT incluir archivos SQLite ni datos privados.
5. WHEN se elimina y recrea el contenedor con el mismo volumen, THE Runtime SHALL conservar la base de datos y sus datos.

### Requirement 7: Compatibilidad MCP y calidad

**User Story:** Como cliente MCP, quiero conservar las herramientas actuales y consultar las nuevas capacidades, para actualizar el servidor sin romper integraciones.

#### Acceptance Criteria

1. WHEN un cliente invoca las herramientas MCP existentes, THE MCP_Interface SHALL mantener sus contratos actuales.
2. WHEN un cliente consulta el workflow, memoria o prácticas, THE MCP_Interface SHALL validar entradas y devolver salidas estructuradas.
3. WHEN se ejecutan las pruebas de regresión, THE Project SHALL conservar los resultados PASS, WARN y BLOCK.
4. WHEN se ejecuta una actualización de esquema, THE Test_Suite SHALL verificar migración, persistencia, idempotencia y aislamiento.
