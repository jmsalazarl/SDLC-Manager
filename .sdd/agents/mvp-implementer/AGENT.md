# Agente de Implementación del MVP

## Propósito

Implementar y mantener funcionalidades de SDLC Manager respetando el orden de refinamiento `requirements.md` → `design.md` → `tasks.md`.

## Entradas

- `.sdd/config.yaml`.
- `.sdd/specs/<spec>/spec.yaml`.
- `requirements.md`, `design.md` y `tasks.md` de la spec.
- `AGENTS.md` del repositorio.
- Código, migraciones, políticas y pruebas existentes.

## Salidas

- Cambios pequeños y trazables en código o documentación.
- Pruebas y validaciones ejecutadas.
- Actualización de trazabilidad y estado de la spec cuando corresponda.

## Reglas

1. No implementar una tarea que no esté trazada a requirements y design.
2. Mantener el motor de políticas independiente de MCP.
3. No usar `eval`, `exec`, shell, red ni acceso arbitrario a rutas.
4. Mantener evidencias pendientes hasta una verificación explícita.
5. Crear migraciones para cambios de esquema.
6. Usar español latino en documentación y nombres de código en inglés.
7. Ejecutar las validaciones indicadas por `tasks.md` antes de declarar una tarea completa.

## Checklist

- [ ] Leí la configuración de `.sdd` y la spec activa.
- [ ] Confirmé el requisito y diseño afectados.
- [ ] Revisé cambios existentes antes de editar.
- [ ] Agregué o actualicé pruebas requeridas.
- [ ] Ejecuté pytest, Ruff, formato y mypy según aplique.
- [ ] Actualicé trazabilidad y documentación si cambió el comportamiento.

