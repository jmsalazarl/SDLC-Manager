# Plan de Implementación: Servidor MCP MVP

## Resumen

Este plan registra la implementación ejecutada del MVP. Todas las tareas están marcadas como completadas porque el código, las migraciones, las políticas, las pruebas, Docker y la documentación fueron creados y verificados en el checkout actual.

## Tareas

### 1. Inicialización del proyecto Python

- [x] 1.1 Crear `pyproject.toml` con Python 3.12+, MCP SDK 2.3.0, Pydantic, SQLAlchemy, Alembic, pytest, Ruff y mypy.
  - _Requerimiento: Requirement 1, Requirement 7_
  - _Capa: Backend / Docs_
  - _Depende de: Ninguna_
- [x] 1.2 Generar `uv.lock` y habilitar instalación reproducible mediante `uv sync`.
  - _Requerimiento: Requirement 7_
  - _Capa: Backend / CI-CD_
  - _Depende de: 1.1_
- [x] 1.3 Crear configuración `.env.example`, `.gitignore` y `.dockerignore` sin secretos.
  - _Requerimiento: Requirement 7_
  - _Capa: Seguridad / Docs_
  - _Depende de: 1.1_

### 2. Dominio y casos de uso

- [x] 2.1 Crear entidades `Project`, `Sprint`, `UserStory`, `PolicyRule`, `EngineeringExperience`, `Evidence`, `PolicyEvaluation` y `GateDecision`.
  - _Requerimiento: Requirement 2, Requirement 4, Requirement 5, Requirement 6_
  - _Capa: Domain_
  - _Depende de: 1.1_
- [x] 2.2 Crear enums de resultados, verificación, revisión y aprobación de políticas.
  - _Requerimiento: Requirement 2, Requirement 5_
  - _Capa: Domain_
  - _Depende de: 2.1_
- [x] 2.3 Crear protocolos de repositorio independientes de SQLAlchemy.
  - _Requerimiento: Requirement 4, Requirement 5, Requirement 6_
  - _Capa: Domain / Architecture_
  - _Depende de: 2.1_
- [x] 2.4 Implementar `SdlcService` para proyectos, sprints, historias, experiencias, evidencias, gates y análisis de sprint.
  - _Requerimiento: Requirement 4, Requirement 5, Requirement 6_
  - _Capa: Application_
  - _Depende de: 2.3, 3.3, 4.1_

### 3. Persistencia y migraciones

- [x] 3.1 Crear modelos SQLAlchemy con nombres físicos en español y llaves de aislamiento por proyecto.
  - _Requerimiento: Requirement 5, Requirement 6, Requirement 7_
  - _Capa: Base de Datos_
  - _Depende de: 2.1_
- [x] 3.2 Crear la migración Alembic `0001_initial` para proyectos, sprints, historias, experiencias, evidencias, evaluaciones y auditoría.
  - _Requerimiento: Requirement 7_
  - _Capa: Base de Datos_
  - _Depende de: 3.1_
- [x] 3.3 Implementar repositorios SQLAlchemy con conversión de modelos y filtros de proyecto.
  - _Requerimiento: Requirement 4, Requirement 5, Requirement 6_
  - _Capa: Infrastructure_
  - _Depende de: 3.1_
- [x] 3.4 Implementar inicialización segura de SQLite y ejecución de migraciones al arrancar.
  - _Requerimiento: Requirement 1, Requirement 7_
  - _Capa: Infrastructure_
  - _Depende de: 3.2_

### 4. Motor de políticas y conocimiento

- [x] 4.1 Implementar carga YAML estricta con `safe_load`, validación Pydantic, duplicados y estados de aprobación.
  - _Requerimiento: Requirement 2_
  - _Capa: Infrastructure / Engines_
  - _Depende de: 1.1_
- [x] 4.2 Implementar operadores cerrados, aplicabilidad por evento, etapa, extensión y componente.
  - _Requerimiento: Requirement 2_
  - _Capa: Engines_
  - _Depende de: 4.1_
- [x] 4.3 Implementar precedencia `BLOCK` > `WARN` > `PASS` y validación de evidencias verificadas.
  - _Requerimiento: Requirement 2, Requirement 5_
  - _Capa: Engines / Application_
  - _Depende de: 4.2, 3.3_
- [x] 4.4 Crear `SDLC-001`, `SDLC-002` y `SDLC-003` en paquetes YAML genéricos y de demostración.
  - _Requerimiento: Requirement 3_
  - _Capa: Knowledge_
  - _Depende de: 4.1_
- [x] 4.5 Implementar búsqueda de experiencias y validación de referencias de evidencia sin lectura de archivos.
  - _Requerimiento: Requirement 4, Requirement 5_
  - _Capa: Engines / Infrastructure_
  - _Depende de: 3.3_

### 5. Interfaz MCP

- [x] 5.1 Implementar `MCPServer` con transporte `stdio`, logs en `stderr` y entry point protegido.
  - _Requerimiento: Requirement 1, Requirement 7_
  - _Capa: MCP_
  - _Depende de: 2.4, 4.3_
- [x] 5.2 Registrar herramientas de salud, políticas, reglas, gates, experiencias, evidencias, historias y sprints.
  - _Requerimiento: Requirement 1, Requirement 4, Requirement 5, Requirement 6_
  - _Capa: MCP_
  - _Depende de: 5.1_
- [x] 5.3 Mantener separación entre validación de entrada MCP y reglas de negocio.
  - _Requerimiento: Requirement 1, Requirement 2_
  - _Capa: MCP / Application_
  - _Depende de: 5.2_

### 6. Pruebas y calidad

- [x] 6.1 Crear pruebas unitarias para carga YAML, operadores, aplicabilidad y resultados `PASS`, `WARN` y `BLOCK`.
  - _Requerimiento: Requirement 2, Requirement 3_
  - _Capa: QA_
  - _Depende de: 4.4_
- [x] 6.2 Crear pruebas de integración para SQLite, evidencias, experiencias, HU, sprints y aislamiento.
  - _Requerimiento: Requirement 4, Requirement 5, Requirement 6_
  - _Capa: QA_
  - _Depende de: 2.4, 3.3, 4.5_
- [x] 6.3 Crear pruebas MCP en memoria y por transporte `stdio`.
  - _Requerimiento: Requirement 1, Requirement 7_
  - _Capa: QA / MCP_
  - _Depende de: 5.2_
- [x] 6.4 Ejecutar pytest, Ruff, formato y mypy; corregir errores encontrados.
  - _Requerimiento: Requirement 7_
  - _Capa: QA_
  - _Depende de: 6.1, 6.2, 6.3_

### 7. Distribución y documentación

- [x] 7.1 Crear Dockerfile multi-stage con usuario no root, dependencias de runtime, volumen `/app/data` y sin puertos.
  - _Requerimiento: Requirement 7_
  - _Capa: Docker_
  - _Depende de: 1.2, 3.4, 5.1_
- [x] 7.2 Crear `compose.yaml` únicamente para desarrollo y persistencia local.
  - _Requerimiento: Requirement 7_
  - _Capa: Docker_
  - _Depende de: 7.1_
- [x] 7.3 Crear configuraciones MCP nativa y Docker para Kiro y documentar límites de Hooks.
  - _Requerimiento: Requirement 1, Requirement 7_
  - _Capa: Integración / Docs_
  - _Depende de: 5.1, 7.1_
- [x] 7.4 Crear README, AGENTS, arquitectura, motor de políticas, herramientas, Docker, roadmap y ADRs.
  - _Requerimiento: Requirement 7_
  - _Capa: Docs_
  - _Depende de: Todas las tareas funcionales_

### 8. Inicialización SDDNXP

- [x] 8.1 Crear `.sdd/config.yaml` como estructura canónica del proyecto.
  - _Requerimiento: Todos_
  - _Capa: SDD_
  - _Depende de: 7.4_
- [x] 8.2 Crear `spec.yaml`, `requirements.md`, `design.md` y `tasks.md` para este MVP.
  - _Requerimiento: Todos_
  - _Capa: SDD_
  - _Depende de: 8.1_
- [x] 8.3 Crear trazabilidad, agentes, prompts, skill de validación, hooks, settings, auditoría y ADRs dentro de `.sdd`.
  - _Requerimiento: Todos_
  - _Capa: SDD_
  - _Depende de: 8.2_

### 9. Corrección de UUID en la interfaz MCP

- [x] 9.1 Identificar que `ConfigDict(strict=True)` rechaza cadenas JSON para campos anotados directamente como `UUID` antes de llegar al servicio.
  - _Requerimiento: Requirement 8_
  - _Capa: MCP / Application_
  - _Depende de: 5.3_
- [x] 9.2 Crear un validador de frontera que convierta cadenas UUID válidas a `uuid.UUID` y rechace valores vacíos o mal formados.
  - _Requerimiento: Requirement 8_
  - _Capa: Application_
  - _Depende de: 9.1_
- [x] 9.3 Aplicar el tipo validado a todos los DTO MCP que reciben identificadores UUID sin modificar el motor de políticas.
  - _Requerimiento: Requirement 8_
  - _Capa: MCP / Application_
  - _Depende de: 9.2_
- [x] 9.4 Verificar el JSON Schema y agregar pruebas unitarias de DTO e integración MCP real por `stdio` con payload JSON positivo y negativo.
  - _Requerimiento: Requirement 8_
  - _Capa: QA / MCP_
  - _Depende de: 9.3_
- [x] 9.5 Ejecutar pytest, Ruff, formato y mypy, y documentar causa raíz, archivos y resultados.
  - _Requerimiento: Requirement 8_
  - _Capa: QA / Docs_
  - _Depende de: 9.4_

## Notas

- El estado `implemented` representa el estado observado del checkout, no una aprobación corporativa futura.
- `.codex/` existe como superficie externa previa y no fue modificada ni convertida en estructura canónica.
- El paquete de políticas usa datos ficticios y no contiene credenciales ni información de producción.
- La búsqueda de experiencias usa `LIKE`; FTS5 y embeddings quedan fuera del MVP.
- La verificación Docker se realizó con construcción de imagen y descubrimiento MCP por `stdio`.

## Grafo de dependencias

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.3"] },
    { "id": 1, "tasks": ["2.1", "2.2", "3.1", "4.1"] },
    { "id": 2, "tasks": ["2.3", "3.2", "3.3", "4.2", "4.4"] },
    { "id": 3, "tasks": ["2.4", "3.4", "4.3", "4.5"] },
    { "id": 4, "tasks": ["5.1", "5.2", "6.1", "6.2"] },
    { "id": 5, "tasks": ["5.3", "6.3", "7.1"] },
    { "id": 6, "tasks": ["6.4", "7.2", "7.3", "7.4"] },
    { "id": 7, "tasks": ["8.1", "8.2", "8.3"] },
    { "id": 8, "tasks": ["9.1", "9.2", "9.3"] },
    { "id": 9, "tasks": ["9.4", "9.5"] }
  ]
}
```

