# ADR 0006: Arquitectura independiente de Kiro

## Estado

Aceptada

## Decisión

Los casos de uso y el motor de políticas no dependen de Kiro. Kiro se integra como cliente MCP mediante una configuración externa.

## Motivo

La misma gobernanza debe poder ejecutarse desde Python, Hooks futuros y CI/CD sin iniciar el servidor MCP.

## Consecuencia

La interfaz MCP solo adapta entradas y salidas. Las automatizaciones no se consideran activas por el hecho de registrar el servidor.

