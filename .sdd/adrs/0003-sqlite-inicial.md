# ADR 0003: SQLite inicial

## Estado

Aceptada

## Decisión

El MVP usa SQLite con SQLAlchemy y Alembic.

## Motivo

SQLite permite operación offline, distribución sencilla y persistencia local sin administrar otro servicio.

## Impacto

Los repositorios y migraciones aíslan la persistencia para facilitar una adaptación futura sin cambiar los casos de uso.

