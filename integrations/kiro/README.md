# Integración con Kiro

## Estado

- MCP stdio: **IMPLEMENTADO**.
- Adaptador `PostFileSave` instalado: **VALIDADO CON PRUEBA DE CONTRATO REAL**.
- Cliente Kiro real: **PARTIAL**; una sesión autenticada ejecutó el hook real,
  recuperó una experiencia y produjo stdout contextual con código 0, pero la
  respuesta final no confirmó que el agente lo hubiera recibido.
- Enforcement automático: **NO ACTIVADO**.

Kiro documenta hooks de archivo y hooks de herramienta. El instalador agrega un
hook `PostFileSave` valido en JSON. El hook ejecuta el adaptador con el Python
administrado por `uv`; su salida estandar se agrega al contexto del agente y
solo presenta recomendaciones. No debe interpretarse como un bloqueo.

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

## Hook instalado

1. Definir `SDLC_MANAGER_PROJECT_ID` con un UUID del proyecto local.
2. Ejecutar `integrations plan` y revisar el cambio antes de instalarlo.
3. Instalar la integración desde la raíz del proyecto destino.
4. Verificar que el comando se ejecute desde la raíz del repositorio y que el
   proyecto tenga `uv.lock` disponible para `--frozen`.
5. Confirmar el comportamiento en una sesión Kiro antes de considerarlo
   validado en cliente real.

El archivo `hooks/sdlc-file-save.example.json` continúa desactivado y sirve
como referencia manual. El archivo instalado por el integrador se escribe en
`.kiro/hooks/sdlc-manager-file-save.json` y se retira de forma selectiva.

El adaptador acepta el JSON del hook, lee `path`, `file_path` o `filePath`,
genera un `event_id` estable y ejecuta `sdlc-manager event process --stdin`.
Cuando existen recomendaciones, imprime texto contextual por `stdout` y
termina con código 0. En la prueba real el hook produjo la recomendación y
Kiro marcó la ejecución como completada, pero la respuesta final no confirmó
la recepción del contexto. No accede a producción ni lee el contenido del
archivo.

## Códigos de salida

`PostFileSave` no bloquea. El adaptador convierte los códigos 10, 20 y 30 en
código 0 para que Kiro pueda agregar el texto de `stdout` al contexto. Los
códigos 40, 50 y 51 se conservan como rechazo o error; nunca como éxito. Para
una futura integración `PreToolUse`, el cliente debe mapear 30 a bloqueo
únicamente después de una prueba autorizada.

## Referencias oficiales

- [Kiro Hooks](https://kiro.dev/docs/hooks/)
- [Kiro acciones de hooks](https://kiro.dev/docs/hooks/actions/)
- [Kiro tipos de hooks](https://kiro.dev/docs/hooks/types/)
- [Kiro MCP en CLI](https://kiro.dev/docs/cli/mcp/)
