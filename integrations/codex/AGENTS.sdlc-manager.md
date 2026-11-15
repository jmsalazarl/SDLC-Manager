# Uso de SDLC Manager

Consultar SDLC Manager antes de iniciar una HU, comenzar una tarea SDD,
modificar un componente sensible o cerrar un gate. Usar `get_sdlc_workflow`,
`get_applicable_rules`, `get_applicable_practices`, `search_experiences` y
`evaluate_gate` según el contexto.

No tratar `decision: null`, errores ni rechazos como `PASS`. Las prácticas solo
advierten. Las evidencias requieren verificación humana y `source_client` no es
una identidad de aprobación.

Para automatización sin sesión MCP, usar el wrapper:

```bash
uv run python integrations/codex/process_event.py < evento.json
```

Mantener `event_id` en los reintentos y no incluir secretos en el evento.
