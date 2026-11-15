# Hook documentado: Validar cambios SDD

## Objetivo

Detectar desalineaciones entre la spec activa y los cambios del repositorio antes de aceptar una tarea.

## Disparador

Cambio en cualquiera de:

- `.sdd/specs/**/requirements.md`
- `.sdd/specs/**/design.md`
- `.sdd/specs/**/tasks.md`
- `src/**`
- `tests/**`
- `migrations/**`
- `knowledge/**`

## Acción esperada

1. Identificar la spec relacionada.
2. Ejecutar la skill `validacion-sdd`.
3. Ejecutar los comandos de calidad definidos en la tarea.
4. Reportar diferencias de trazabilidad.

Este archivo documenta el hook; no implica que una herramienta externa lo ejecute automáticamente.

