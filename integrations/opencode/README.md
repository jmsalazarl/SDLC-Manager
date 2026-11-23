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
observa `execute.after`, identifica entradas de archivo, envía el payload nativo
al adaptador `process_event.py` y agrega la respuesta del procesador al campo
`metadata.sdlcManager` del resultado de la herramienta. La ejecución del
plugin contra un cliente instalado continúa sin validación real en este
entorno.

El adaptador normaliza el evento con el directorio del workspace como raíz del
proyecto. El identificador del proyecto se obtiene de
`.sdlc-manager/config.json` o de `SDLC_MANAGER_PROJECT_ID`; no se utiliza la
identidad de OpenCode como aprobación confiable.

## Referencias oficiales

- [OpenCode MCP servers](https://opencode.ai/docs/mcp-servers)
- [OpenCode instructions](https://opencode.ai/docs/instructions/)
- [OpenCode plugins](https://opencode.ai/docs/plugins/)
- [OpenCode server plugins](https://opencode.ai/docs/build/plugins/server)
