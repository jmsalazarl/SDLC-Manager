# Integración con Claude Code

## Estado

- MCP stdio: **IMPLEMENTADO**.
- Instrucciones persistentes: **IMPLEMENTADO** mediante plantilla `CLAUDE.md`.
- Wrapper manual de eventos: **PROBADO CON MOCK**.
- Cliente Claude Code real: **NO VALIDADO EN CLIENTE REAL**.
- Hook `PreToolUse` y enforcement: **NO ACTIVADO**.

## Instalación MCP

Revisar `.mcp.json.example` y combinarlo con el `.mcp.json` del proyecto sin
sobrescribir entradas existentes. La instalación interactiva equivalente es:

```bash
claude mcp add sdlc-manager -- uv run --frozen sdlc-manager
```

La instalación aditiva del proyecto puede realizarse con:

```bash
uv run sdlc-manager integrations plan claude-code
uv run sdlc-manager integrations install claude-code --project-id UUID_DEL_PROYECTO
```

El hook `PostToolUse` entrega el resultado como `hookSpecificOutput` con
`additionalContext`. No bloquea operaciones; para retirarlo se usa
`uv run sdlc-manager integrations uninstall claude-code`.

## Instrucciones y hooks

Copiar selectivamente `CLAUDE.md.example` a las instrucciones del proyecto.
Claude Code documenta hooks `PreToolUse` capaces de bloquear, pero esta entrega
no incluye una configuración ejecutable porque no fue probada contra una
instalación real. Una futura configuración debe traducir 30 a bloqueo y 50/51 a
error, sin convertirlos en éxito.

## Referencias oficiales

- [Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [Claude Code hooks](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Claude Code memory](https://docs.anthropic.com/en/docs/claude-code/memory)
- [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code/skills)
