# Integración con Codex

## Estado

- MCP stdio: **IMPLEMENTADO**.
- Instrucciones persistentes: **IMPLEMENTADO** mediante plantilla `AGENTS.md`.
- Hooks de proyecto para `SessionStart`, `UserPromptSubmit` y `PostToolUse`:
  **IMPLEMENTADO**.
- Propagación de recomendaciones mediante `hookSpecificOutput.additionalContext`:
  **PROBADO CON MOCK**.
- Cliente Codex real: **VALIDADO EN CLIENTE REAL** en un proyecto temporal con
  Codex CLI 0.171.0.
- Enforcement: **NO IMPLEMENTADO**; los hooks son informativos y no bloquean.

## Instalación MCP

La configuración de ejemplo está en `mcp.config.example.toml`. Para una
instalación interactiva, revisar la sintaxis soportada por la versión instalada
y agregar un servidor local equivalente a:

```bash
codex mcp add sdlc-manager -- uv --directory /ruta/al/SDLC-Manager run --frozen sdlc-manager
```

La configuración MCP permanece en el alcance elegido por el usuario. El
instalador de integraciones no modifica el perfil global.

El instalador opcional por proyecto agrega un paquete propio bajo
`.sdlc-manager/` y hooks aditivos en `.codex/hooks.json`. Conserva los hooks y
archivos existentes:

```bash
uv run sdlc-manager integrations plan codex \
  --project-root /ruta/al/proyecto

uv run sdlc-manager integrations install codex \
  --project-root /ruta/al/proyecto \
  --project-id UUID_DEL_PROYECTO
```

Antes de `install`, se debe revisar el JSON devuelto por `plan`. Codex puede
requerir que el usuario confíe explícitamente los hooks del proyecto. La
retirada selectiva es:

```bash
uv run sdlc-manager integrations uninstall codex \
  --project-root /ruta/al/proyecto
```

La instalación no agrega experiencias, proyectos ficticios ni evidencias. El
contenido de `AGENTS.md` se entrega como referencia en
`.sdlc-manager/instructions/codex.md`; no se sobrescribe automáticamente.

## Instrucciones

Incorporar el contenido de `AGENTS.sdlc-manager.md` al `AGENTS.md` del proyecto
después de revisar conflictos con instrucciones existentes.

## Eventos

El instalador usa los eventos de hooks documentados por Codex:
`SessionStart`, `UserPromptSubmit` y `PostToolUse`. El adaptador convierte el
payload nativo a `SdlcEvent`, fija `source_client` a `codex` como metadato de
transporte y no lo usa como identidad confiable.

`TaskCompleted` no se declara porque no forma parte del contrato de eventos
verificado de Codex. La respuesta del motor se transforma en
`hookSpecificOutput.additionalContext`; una recomendación no bloquea la
operación. Los errores mantienen un código de salida distinto de PASS y no se
convierten en éxito.

El paquete bajo `integrations/codex/plugin/` es un recurso distribuible
opcional. La instalación por proyecto no registra plugins en el perfil global:
instala recursos propios bajo `.sdlc-manager/` y agrega hooks al nivel del
proyecto.

## Referencias oficiales

- [Codex MCP](https://developers.openai.com/codex/mcp)
- [Codex Skills](https://developers.openai.com/plugins/concepts/skills)
- [Codex Plugins](https://developers.openai.com/plugins/concepts/plugins)
- [Codex: empaquetado y hooks](https://developers.openai.com/plugins/build/plugins)
