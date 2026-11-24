# ADR-0012: Bootstrap automático de integraciones por proveedor

## Estado

Aceptada.

## Contexto

El MCP expone herramientas, pero por sí solo no provoca consultas durante una
sesión del agente. Para que SDLC Manager participe automáticamente se necesita
instalar el MCP, los hooks o plugins y los adaptadores correspondientes sin
modificar perfiles globales de forma implícita.

## Decisión

SDLC Manager se mantiene como un framework local compuesto por:

- un núcleo de dominio y persistencia;
- un servidor MCP;
- un CLI de administración;
- adaptadores y superficies de integración por proveedor.

El comando `sdlc-manager init <proveedor>` será la fachada de bootstrap para un
proyecto. En Codex configura de forma aditiva el MCP en `.codex/config.toml`,
un plugin local registrado mediante `.agents/plugins/marketplace.json`, con los
hooks y recursos propios bajo `.sdlc-manager/`.
La configuración global solo se modifica mediante una acción explícita de
alcance `user`.

`sdlc-manager integrations plan|install|uninstall` permanece como API detallada
para automatización, revisión de cambios, rollback y operación avanzada.

## Consecuencias

- El usuario instala una integración completa, no solamente un servidor MCP.
- MCP, hooks y plugins siguen siendo capas separadas con responsabilidades
  verificables.
- El alcance predeterminado de `init` es el proyecto actual.
- Las configuraciones externas se preservan y los conflictos se rechazan.
- La visibilidad contextual se valida por proveedor y no se presume por la
  existencia de archivos instalados.
- La misma fachada puede extenderse a Kiro, OpenCode y Claude Code sin copiar
  la lógica del procesador de eventos.

## Alternativas descartadas

- Tratar MCP como mecanismo suficiente de activación automática.
- Modificar siempre `~/.codex/config.toml` durante una instalación de proyecto.
- Crear un instalador independiente por proveedor sin reutilizar
  `IntegrationInstaller`.
