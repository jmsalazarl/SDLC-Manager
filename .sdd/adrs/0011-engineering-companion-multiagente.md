# ADR-0011: Engineering Companion independiente del proveedor

## Estado

Aceptada.

## Contexto

SDLC Manager necesita recibir señales de distintos clientes sin copiar la
lógica de políticas, memoria, prácticas o workflow en cada integración.
Además, los archivos de configuración de un proyecto pueden pertenecer a
otros productos y no deben sobrescribirse.

## Decisión

Se conserva `SdlcEventProcessor` como núcleo único y se agregan adaptadores
delgados fuera de `src/sdlc_manager`. Los adaptadores usan stdin/stdout,
MCP o la API oficial del proveedor cuando corresponda. La instalación se
realiza por proyecto mediante `IntegrationInstaller`, con namespace propio,
plan previo, backups, escritura atómica, conflictos explícitos y retiro
selectivo.

La consulta de SDDNXP se limita a un reader local de solo lectura. No se
ejecutan sus transiciones, aprobaciones ni comandos externos.

## Consecuencias

- Una decisión de dominio produce el mismo resultado desde MCP, CLI o hook.
- La ausencia de un proveedor o de SDDNXP no impide el funcionamiento local.
- La propagación contextual depende del contrato de cada proveedor y se debe
  clasificar separadamente de la existencia del adaptador.
- Los clientes no probados no se declaran validados.
- SQLite mantiene sus límites de concurrencia, por lo que los reintentos
  conservan el `event_id` y la huella del evento.

## Alternativas descartadas

- Incorporar SDKs de todos los proveedores al núcleo.
- Duplicar el motor de políticas en cada plugin.
- Reescribir JSONC con un parser JSON que elimine comentarios.
- Instalar hooks globales sin una autorización explícita del usuario.
