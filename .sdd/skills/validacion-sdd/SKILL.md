# Skill: Validación SDD

## Propósito

Validar que una spec `.sdd` sea ejecutable, trazable y consistente con el código implementado.

## Cuándo usarla

- Antes de iniciar implementación.
- Después de cambiar requirements o design.
- Antes de marcar una spec como `implemented`.
- Durante una revisión de calidad del repositorio.

## Entradas

- `.sdd/config.yaml`.
- `.sdd/specs/<nombre>/spec.yaml`.
- `requirements.md`, `design.md` y `tasks.md`.
- Código, pruebas y migraciones relacionadas.

## Salidas

- Lista de inconsistencias y rutas afectadas.
- Matriz de trazabilidad actualizada cuando corresponda.
- Resultado de comandos de validación.

## Pasos

1. Confirmar la estructura y estado de `spec.yaml`.
2. Verificar historias de usuario y criterios EARS en requirements.
3. Verificar que design cubra arquitectura, datos, interfaces, seguridad y pruebas.
4. Verificar subtareas checkbox numeradas y dependencias en tasks.
5. Comparar requisitos con tareas, pruebas y archivos implementados.
6. Ejecutar `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` y `uv run mypy src`.
7. Reportar el resultado sin inventar funcionalidades.

## Checklist

- [ ] Existe `.sdd/config.yaml`.
- [ ] Existe `spec.yaml` con estado válido.
- [ ] Existen los tres documentos de la spec.
- [ ] Requirements usa criterios verificables.
- [ ] Design tiene trazabilidad hacia requirements.
- [ ] Tasks usa checkboxes ejecutables.
- [ ] Las pruebas y comandos reportados fueron ejecutados.
- [ ] No hay secretos ni rutas sensibles en documentación.

## Límites

La skill no modifica requisitos por inferencia, no aprueba decisiones de negocio y no convierte `.codex` u otra superficie externa en estructura canónica.

