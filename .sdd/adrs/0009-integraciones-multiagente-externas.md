# ADR 0009: Integraciones Multiagente Fuera Del Núcleo

## Estado

Aceptada

## Contexto

SDLC Manager necesita conectarse con varios clientes MCP y con futuros hooks
sin duplicar la evaluación de workflows, políticas, prácticas o experiencias.
Los contratos de eventos y hooks varían por cliente y algunas capacidades no
pueden verificarse sin instalar el cliente real.

## Decisión

Las integraciones viven en `integrations/` y solo consumen MCP stdio o el CLI
universal. Se incluyen configuraciones, instrucciones persistentes, wrappers
sin shell y un adaptador Kiro `PostFileSave` desactivado por defecto. No se
incorporan dependencias de clientes al paquete principal ni se activa
enforcement no verificado.

## Consecuencias

- Un cliente puede instalarse sin cambiar el núcleo ni la base de datos.
- La misma decisión determinista se reutiliza desde MCP y CLI.
- La activación automática se declara por cliente y por estado de verificación.
- La validación en cliente real sigue siendo necesaria para afirmar enforcement.
- Los wrappers deben preservar `event_id` y respetar las limitaciones de SQLite.
