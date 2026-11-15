# Integración con OpenCode

## Estado

- MCP local: **IMPLEMENTADO**.
- Instrucciones persistentes: **IMPLEMENTADO** mediante `instructions` y la
  guía común.
- Wrapper manual de eventos: **PROBADO CON MOCK**.
- Cliente OpenCode real: **NO VALIDADO EN CLIENTE REAL**.
- Plugins, activación automática y enforcement: **NO VERIFICADO**; no se
  activan.

## Instalación MCP

Revisar `opencode.config.example.jsonc` y combinarlo con la configuración del
usuario sin sobrescribir claves existentes. La configuración usa la estructura
actual `mcp.servers` y un servidor `local` con comando stdio.

También puede revisarse el comando interactivo:

```bash
opencode mcp add
opencode mcp list
```

## Instrucciones y eventos

OpenCode puede cargar archivos mediante `instructions`. La guía común indica
cuándo consultar workflows, políticas, prácticas y memoria. El wrapper
`process_event.py` recibe un `SdlcEvent` serializado; no inventa eventos nativos
ni ejecuta plugins.

## Referencias oficiales

- [OpenCode MCP servers](https://opencode.ai/docs/mcp-servers)
- [OpenCode instructions](https://opencode.ai/docs/instructions/)
- [OpenCode plugins](https://opencode.ai/docs/plugins/)
