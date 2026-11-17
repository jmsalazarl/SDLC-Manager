# Integración con Kiro

## Estado

- MCP stdio: **IMPLEMENTADO**.
- Adaptador `PostFileSave` de ejemplo: **PROBADO CON MOCK**.
- Cliente Kiro real: **NO VALIDADO EN CLIENTE REAL** en este entorno.
- Enforcement automático: **NO ACTIVADO**.

Kiro documenta hooks de archivo y hooks de herramienta. El archivo incluido usa
`PostFileSave`, que solo presenta una recomendación y no debe interpretarse como
un bloqueo. El payload real del hook debe verificarse antes de habilitarlo.

## MCP

Los ejemplos existentes son:

- `mcp.native.example.json`
- `mcp.docker.example.json`

Copiar el contenido a la configuración del proyecto solo después de revisar si
el archivo de destino ya existe. No sobrescribir configuraciones del usuario.

Para instalar solo la superficie de este proyecto:

```bash
uv run sdlc-manager integrations plan kiro
uv run sdlc-manager integrations install kiro --project-id UUID_DEL_PROYECTO
```

El instalador conserva `mcpServers` existentes y el hook instalado es
informativo. Para retirarlo:

```bash
uv run sdlc-manager integrations uninstall kiro
```

## Hook opcional

1. Definir `SDLC_MANAGER_PROJECT_ID` con un UUID del proyecto local.
2. Revisar `hooks/sdlc-file-save.example.json`.
3. Copiarlo a `.kiro/hooks/` con un nombre elegido por el usuario.
4. Verificar que el comando se ejecute desde la raíz del repositorio.
5. Activarlo únicamente después de probar el payload real.

El adaptador lee `path`, `file_path` o `filePath`, genera un `event_id` estable
y ejecuta `sdlc-manager event process --stdin`. No accede a producción ni lee
el contenido del archivo.

## Códigos de salida

`PostFileSave` no bloquea. Para una futura integración `PreToolUse`, el cliente
debe mapear 30 a bloqueo únicamente después de una prueba autorizada. Los
códigos 40, 50 y 51 se reportan como rechazo o error; nunca como éxito.

## Referencias oficiales

- [Kiro Hooks](https://kiro.dev/docs/hooks/)
- [Kiro MCP en CLI](https://kiro.dev/docs/cli/mcp/)
