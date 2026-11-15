# ADR 0006: Independencia de Kiro

## Estado

Aceptada

## Decisión

Los casos de uso y el motor de políticas no dependen de Kiro. Kiro se conecta mediante una configuración MCP externa.

## Motivo

La gobernanza debe poder ejecutarse desde Python, Hooks futuros y CI/CD sin iniciar necesariamente el transporte MCP.

## Impacto

El adaptador MCP solo traduce entradas y salidas. Registrar el servidor no activa eventos automáticos.

