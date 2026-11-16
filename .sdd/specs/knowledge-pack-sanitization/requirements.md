# Requirements Document

## Introduction

El núcleo debe permanecer genérico y no incorporar extensiones, nombres de
archivos, componentes ni controles pertenecientes a una organización concreta.
Las reglas deben provenir de los paquetes de conocimiento configurados y no de
condiciones codificadas en los servicios.

## Requisitos

### Requirement 1: Núcleo independiente del conocimiento

**User Story:** Como responsable del producto, quiero que el núcleo no conozca
reglas corporativas específicas, para poder distribuirlo sin información
interna.

#### Acceptance Criteria

1. WHEN el servicio infiere un evento de archivo, THE SdlcService SHALL basarse
   en el contexto del caso de uso y no en una extensión corporativa codificada.
2. WHERE una regla depende de una extensión, THE PolicyEngine SHALL obtenerla
   exclusivamente desde el paquete YAML cargado.
3. IF no se proporciona un evento explícito, THEN THE SdlcService SHALL usar un
   evento genérico derivado de la existencia de archivos modificados.

### Requirement 2: Ejemplos ficticios

**User Story:** Como mantenedor, quiero que las demostraciones utilicen nombres
genéricos, para no revelar procesos o artefactos internos.

#### Acceptance Criteria

1. WHEN la documentación presenta un archivo de ejemplo, THE Documentation
   SHALL use a generic fictional artifact name.
2. WHEN las pruebas cargan una regla de demostración, THE Tests SHALL use
   neutral identifiers and evidence names.
3. WHERE se distribuye un paquete demo, THE Package SHALL NOT reference
   production systems, corporate components or organization-specific formats.

### Requirement 3: Trazabilidad

**User Story:** Como auditor, quiero que el cambio quede documentado, para
confirmar que la lógica permanece configurable y que no se agregaron secretos.

#### Acceptance Criteria

1. WHEN se completa la sanitización, THE Repository SHALL documentar el diseño,
   tareas, decisión y resultados de validación.
2. WHEN se ejecutan las pruebas, THE Validation SHALL confirm that no
   organization-specific extension reference remains in source, docs or tests.

## Alcance MVP

- Eliminar inferencias codificadas basadas en una extensión específica.
- Reemplazar ejemplos, fixtures y evidencias por nombres genéricos.
- Mantener las capacidades configurables del Policy Engine.
- Actualizar documentación y trazabilidad SDD.

## Fuera De Alcance Inicial

- Agregar nuevas reglas corporativas.
- Conectar paquetes privados.
- Cambiar el contrato MCP o el esquema de persistencia.

## Preguntas Abiertas

No hay preguntas abiertas para este alcance.
