# Integración con Codex

## Estado

- MCP stdio: **IMPLEMENTADO**.
- Instrucciones persistentes: **IMPLEMENTADO** mediante plantilla `AGENTS.md`.
- Wrapper manual de eventos: **PROBADO CON MOCK**.
- Cliente Codex real: **NO VALIDADO EN CLIENTE REAL**.
- Activación automática y enforcement: **NO VERIFICADO**; no se activa.

## Instalación MCP

La configuración de ejemplo está en `mcp.config.example.toml`. Para una
instalación interactiva, revisar la sintaxis soportada por la versión instalada
y agregar un servidor local equivalente a:

```bash
codex mcp add sdlc-manager -- uv run --frozen sdlc-manager
```

La configuración debe permanecer en el alcance elegido por el usuario. No se
copian archivos ni se modifican configuraciones automáticamente.

El instalador opcional por proyecto copia un paquete identificable y no
modifica `AGENTS.md` existente:

```bash
uv run sdlc-manager integrations plan codex
uv run sdlc-manager integrations install codex --project-id UUID_DEL_PROYECTO
```

El runtime puede requerir que el usuario revise y confíe explícitamente el
plugin. Esto no se declara validado hasta ejecutar el cliente real. La retirada
selectiva es:

```bash
uv run sdlc-manager integrations uninstall codex
```

## Instrucciones

Incorporar el contenido de `AGENTS.sdlc-manager.md` al `AGENTS.md` del proyecto
después de revisar conflictos con instrucciones existentes.

## Eventos

No se afirma un contrato de hooks de ciclo de vida para esta entrega. El
wrapper procesa eventos ya normalizados y fija `source_client` a `codex` como
metadato de transporte, no como identidad confiable.

## Referencias oficiales

- [Codex MCP](https://developers.openai.com/codex/mcp)
- [Codex Skills](https://developers.openai.com/plugins/concepts/skills)
- [Codex Plugins](https://developers.openai.com/plugins/concepts/plugins)
