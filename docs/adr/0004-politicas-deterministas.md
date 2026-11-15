# ADR 0004: Separación entre políticas y razonamiento LLM

## Estado

Aceptada

## Decisión

Los bloqueos y las decisiones obligatorias dependen exclusivamente de políticas YAML aprobadas y operadores deterministas.

## Motivo

Un modelo puede ayudar a interpretar contexto, pero no debe convertir texto libre en una condición ejecutable ni aprobar evidencias automáticamente.

## Consecuencia

Las reglas nuevas se agregan como YAML validado. Las capacidades semánticas avanzadas quedan fuera del MVP.

