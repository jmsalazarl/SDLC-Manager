# SDLC Manager — Guía de desarrollo

## Propósito

SDLC Manager es un servidor MCP local para gobernanza del SDLC. El repositorio debe mantenerse ejecutable sin servicios externos y sin información corporativa real.

## Flujo SDD

La estructura canónica de especificaciones es `.sdd/`. La spec activa es `.sdd/specs/mcp-server-mvp/`. Respetar el orden `requirements.md` → `design.md` → `tasks.md` antes de implementar cambios nuevos.

- `.sdd/config.yaml`: configuración y reglas del flujo.
- `.sdd/specs/`: requisitos, diseño y tareas por funcionalidad.
- `.sdd/agents/`, `.sdd/prompts/` y `.sdd/skills/`: capacidades reutilizables.
- `.sdd/hooks/`: catálogo de automatizaciones documentadas.
- `.sdd/adrs/`: decisiones de arquitectura.
- `.sdd/traceability.yaml`: relación entre requisitos, diseño, tareas, código y pruebas.
- `.sdd/audit/`: evidencia de validaciones y estados de la spec.

`.codex/` es una superficie externa existente y no es fuente canónica SDD; no modificarla ni migrarla sin autorización explícita.

## Arquitectura

- `src/sdlc_manager/domain/`: entidades, enumeraciones y contratos sin dependencias de MCP o SQLAlchemy.
- `src/sdlc_manager/application/`: casos de uso y esquemas de entrada.
- `src/sdlc_manager/engines/`: motores deterministas reutilizables fuera de MCP.
- `src/sdlc_manager/infrastructure/`: SQLite, SQLAlchemy, Alembic y carga de YAML.
- `src/sdlc_manager/mcp/`: adaptación de casos de uso a MCP y transporte `stdio`.
- `knowledge/`: paquetes de políticas versionados y ficticios.
- `knowledge/sdlc/`: plantillas versionadas del workflow SDLC.
- `tests/`: pruebas unitarias, de integración y de protocolo.

La interfaz MCP no contiene reglas de negocio. Toda regla nueva debe declararse en YAML con el esquema validado o, si requiere una capacidad nueva del motor, acompañarse de una decisión técnica y pruebas.

El workflow, la memoria y las prácticas son capacidades separadas. Las prácticas aprobadas solo generan recomendaciones y no pueden producir `BLOCK`. La plantilla SDLC se instala de forma idempotente y las personalizaciones se crean por copia.

## Convenciones Python

- Python 3.12+ y nombres de código en inglés.
- Tipado estricto en `src`.
- Pydantic para entradas externas y validación de YAML.
- No usar `eval`, `exec`, shell ni acceso arbitrario a archivos desde parámetros del cliente.
- Los logs deben ir a `stderr`; `stdout` pertenece al protocolo MCP.
- Mantener métodos pequeños, dependencias inyectadas y repositorios aislados por `project_id`.

## Persistencia y migraciones

Los nombres físicos de SQLite siguen la convención en español (`TPROYECTO`, `TEVIDENCIA`, etc.) y el código los mapea explícitamente con SQLAlchemy. Toda modificación de esquema requiere una migración Alembic versionada.

La migración `0002_knowledge_architecture` es aditiva: no elimina datos ni reinicializa SQLite. Las actualizaciones deben probarse desde `0001_initial` y verificar preservación de identificadores y contenido.

```bash
uv run alembic upgrade head
```

No eliminar datos, migraciones ni archivos de conocimiento sin confirmación explícita.

## Testing

Cada regla nueva debe incluir casos de aplicabilidad, no aplicabilidad y resultado. Toda modificación en el protocolo debe incluir una prueba MCP en memoria o por `stdio`.

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

## Restricciones de seguridad

- El estado `VERIFIED` requiere una aprobación humana registrada.
- Experiencias pendientes no activan bloqueos.
- Las políticas no aprobadas nunca bloquean.
- No agregar integraciones corporativas, telemetría ni red al MVP.
- No afirmar validaciones que no hayan sido ejecutadas.

