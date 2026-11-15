# ADR 0003: Uso inicial de SQLite

## Estado

Aceptada

## Decisión

El MVP persiste en SQLite con SQLAlchemy y Alembic.

## Motivo

La base embebida permite ejecución offline, distribución simple y persistencia local sin administrar un servicio adicional.

## Consecuencia

El diseño conserva repositorios y migraciones para facilitar una futura adaptación a otra base sin cambiar los casos de uso.

