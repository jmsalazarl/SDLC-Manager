# ADR 0002: Elección de Python

## Estado

Aceptada

## Decisión

El proyecto usa Python `>=3.12` con Pydantic, SQLAlchemy, pytest, Ruff y mypy.

## Motivo

El SDK oficial, la validación tipada y las herramientas de calidad cubren el MVP sin dependencias innecesarias.

## Impacto

El lockfile fija la resolución y el código mantiene tipado estricto en `src`.

