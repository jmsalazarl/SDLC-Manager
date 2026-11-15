# ADR 0002: Elección de Python

## Estado

Aceptada

## Decisión

El proyecto usa Python 3.12+ con Pydantic, SQLAlchemy y pytest.

## Motivo

Python ofrece soporte oficial del SDK MCP, tipado gradual y un ecosistema adecuado para validación, persistencia y herramientas de desarrollo.

## Consecuencia

Las versiones y dependencias se fijan mediante `uv.lock`. El código se mantiene con mypy estricto y Ruff.

