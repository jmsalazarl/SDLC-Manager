# Integración con Codex

## Estado

- MCP stdio: **IMPLEMENTADO**.
- Instrucciones persistentes: **IMPLEMENTADO** mediante plantilla `AGENTS.md`.
- Plugin local con hooks administrados para `SessionStart`, `UserPromptSubmit` y
  `PostToolUse`: **IMPLEMENTADO**.
- Propagación de recomendaciones mediante `hookSpecificOutput.additionalContext`:
  **PROBADO CON MOCK**.
- Cliente Codex real: **PARTIAL**. La sesión real creó `index.html`, pero no
  mostró contexto de SDLC Manager porque el plugin local no quedó instalado en
  el runtime de esta versión del CLI.
- Enforcement: **NO IMPLEMENTADO**; los hooks son informativos y no bloquean.

## Instalación automática

La instalación recomendada registra un plugin local de Codex en alcance de
proyecto en una sola operación:

```bash
sdlc-manager init codex \
  --project-root /ruta/al/proyecto \
  --project-id UUID_DEL_PROYECTO
```

El comando agrega de forma idempotente:

- `.agents/plugins/marketplace.json` con la fuente local del plugin.
- `.codex/config.toml` con el plugin `sdlc-manager@sdlc-manager-local` habilitado.
- `.sdlc-manager/providers/codex-plugin/` con el adaptador administrado.

El alcance de proyecto evita modificar `~/.codex/config.toml`. El proyecto debe
ser confiable para que Codex permita cargar la configuracion y los hooks del
plugin local. El plugin contiene su propio `plugin.json`, servidor MCP, skill y
hooks, por lo que no depende de `.codex/hooks.json`.
Para revisar antes de modificar archivos:

```bash
uv run sdlc-manager integrations plan codex \
  --project-root /ruta/al/proyecto \
  --project-id UUID_DEL_PROYECTO
```

Para retirar únicamente los recursos propios:

```bash
uv run sdlc-manager integrations uninstall codex \
  --project-root /ruta/al/proyecto
```

## Instalación MCP manual

La configuración de ejemplo está en `mcp.config.example.toml`. Si se requiere
registrar el servidor fuera de un proyecto administrado por el instalador:

```bash
codex mcp add sdlc-manager -- uv --project /ruta/al/SDLC-Manager run --frozen sdlc-manager
```

Antes de `install`, se debe revisar el JSON devuelto por `plan`. Codex puede
requerir confianza explícita del proyecto y habilitación del plugin local.

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
opcional. La instalación por proyecto no modifica el perfil global: instala el
plugin bajo `.sdlc-manager/` y registra únicamente su marketplace local en el
proyecto.

## Referencias oficiales

- [Codex MCP](https://developers.openai.com/codex/mcp)
- [Codex Skills](https://developers.openai.com/plugins/concepts/skills)
- [Codex Plugins](https://developers.openai.com/plugins/concepts/plugins)
- [Codex: empaquetado y hooks](https://developers.openai.com/plugins/build/plugins)
