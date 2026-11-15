# ADR 0001: Elección de MCP

## Estado

Aceptada

## Decisión

El MVP usa el SDK oficial de MCP para Python `2.3.0`, `MCPServer` y transporte `stdio`.

## Motivo

MCP proporciona descubrimiento e invocación estándar. `stdio` evita puertos y reduce la superficie de red de la ejecución local.

## Impacto

`stdout` queda reservado para MCP, los logs van a `stderr` y la versión queda fijada en `pyproject.toml` y `uv.lock`.

