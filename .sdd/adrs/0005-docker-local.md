# ADR 0005: Docker local

## Estado

Aceptada

## Decisión

La distribución incluye una imagen Docker multi-stage, sin puertos, con usuario no root y volumen `/app/data`.

## Motivo

El consumidor puede ejecutar el servidor sin instalar Python ni dependencias del proyecto.

## Impacto

El cliente MCP debe usar `-i` y el volumen persistente. La ejecución de demostración usa `--network none`.

