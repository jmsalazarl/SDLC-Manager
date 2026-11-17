# Integración con OpenCode

## Estado

- MCP local: **IMPLEMENTADO**.
- Instrucciones persistentes: **IMPLEMENTADO** mediante `instructions` y la
  guía común.
- Wrapper manual de eventos: **PROBADO CON MOCK**.
- Cliente OpenCode real: **NO VALIDADO EN CLIENTE REAL**.
- Plugin local y activación `execute.after`: **IMPLEMENTADO**; cliente real
  **NO VALIDADO EN CLIENTE REAL**.

## Instalación MCP

Revisar `opencode.config.example.jsonc` y combinarlo con la configuración del
usuario sin sobrescribir claves existentes. La configuración usa la estructura
actual `mcp.servers` y un servidor `local` con comando stdio.

También puede revisarse el comando interactivo:

```bash
opencode mcp add
opencode mcp list
```

La instalación por proyecto usa `opencode.json` y un plugin local:

```bash
uv run sdlc-manager integrations plan opencode
uv run sdlc-manager integrations install opencode --project-id UUID_DEL_PROYECTO
```

Si solo existe `opencode.jsonc`, el instalador no lo reescribe y solicita un
merge manual. El plugin usa la API `@opencode/plugin` y `execute.after`; su
ejecución contra un cliente instalado debe verificarse por separado.

## Instrucciones y eventos

OpenCode puede cargar archivos mediante `instructions`. La guía común indica
cuándo consultar workflows, políticas, prácticas y memoria. El plugin local
observa `execute.after`, traduce entradas de archivos y agrega la respuesta al
metadata del resultado. La ejecución del plugin contra un cliente instalado
continúa sin validación real en este entorno.

## Referencias oficiales

- [OpenCode MCP servers](https://opencode.ai/docs/mcp-servers)
- [OpenCode instructions](https://opencode.ai/docs/instructions/)
- [OpenCode plugins](https://opencode.ai/docs/plugins/)
