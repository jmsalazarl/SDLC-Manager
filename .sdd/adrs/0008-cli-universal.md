# ADR 0008: CLI universal sobre el procesador de eventos

## Estado

Aceptada

## Contexto

Los adaptadores locales necesitan invocar el mismo `SdlcEventProcessor` sin iniciar MCP. La solución debe conservar SQLite, Alembic, Docker y el comando existente del servidor.

## Decisión

Se implementa `sdlc-manager event process --stdin` con `argparse` de la biblioteca estándar. El CLI construye el contenedor mediante el bootstrap Alembic existente, delega en `process_payload`, escribe JSON únicamente en stdout y reserva stderr para logs. La ejecución sin argumentos mantiene el servidor MCP.

## Consecuencias

- No se agrega una dependencia de CLI.
- MCP y CLI comparten reglas, persistencia y respuestas.
- Los códigos de salida distinguen decisiones, información y errores.
- Los adaptadores deben traducir explícitamente los códigos a la semántica de cada cliente.
- SQLite conserva sus límites de concurrencia del MVP.
