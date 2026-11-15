# ADR-0007: Separacion De Workflow, Memoria Y Practicas

## Estado

Aceptada

## Contexto

El MVP utilizaba experiencias como una entidad general y políticas YAML como mecanismo para reglas obligatorias y recomendaciones. La evolución del producto requiere distinguir el proceso SDLC, la memoria técnica y las prácticas derivadas sin perder compatibilidad ni datos.

## Decisión

Se mantiene `TEXPERIENCIA` con metadatos de clasificación para conservar datos legacy, se crean tablas específicas para workflows versionados y prácticas, y se mantiene `PolicyEngine` como único componente capaz de producir bloqueos obligatorios.

La plantilla predeterminada se instala de manera idempotente desde YAML. Las personalizaciones se crean por copia y versión; las actualizaciones no modifican la plantilla ni reinicializan SQLite.

## Consecuencias

- Las políticas existentes conservan su comportamiento `PASS/WARN/BLOCK`.
- Las prácticas requieren revisión y solo producen recomendaciones.
- Las migraciones son aditivas y deben probarse contra una base `0001_initial`.
- Se agrega una superficie persistente para workflows, gates y excepciones.
- Las experiencias legacy sin clasificación se consideran `LESSON_LEARNED` y mantienen sus identificadores.
