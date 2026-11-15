# ADR 0001: Elección de MCP

## Estado

Aceptada

## Decisión

El MVP expone sus capacidades mediante el SDK oficial de MCP para Python 2.3.0 y transporte `stdio`.

## Motivo

MCP ofrece un contrato estándar para descubrimiento e invocación de herramientas desde clientes compatibles. `stdio` evita puertos, reduce superficie de red y funciona bien para procesos locales.

## Consecuencia

El servidor debe reservar `stdout` para el protocolo y usar `stderr` para logs. La versión queda fijada en `pyproject.toml` y `uv.lock`.

