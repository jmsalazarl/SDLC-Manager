# ADR 0005: Docker y ejecución local

## Estado

Aceptada

## Decisión

Se distribuye una imagen Docker multi-stage sin puertos expuestos, con usuario no root y volumen `/app/data`.

## Motivo

El usuario final puede ejecutar el servidor sin instalar Python ni las dependencias, conservando una base local persistente.

## Consecuencia

La configuración MCP debe invocar Docker con `-i`. La conectividad de red se desactiva durante la ejecución de demostración.

