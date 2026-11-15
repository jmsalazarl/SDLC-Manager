# Docker

## Construcción

```bash
docker build -t sdlc-manager:latest .
```

La imagen usa Python 3.12 slim, un build multi-stage, dependencias fijadas por `uv.lock` y un usuario sin privilegios. No expone puertos.

## Ejecución

```bash
docker run --rm -i \
  --network none \
  -v sdlc-manager-data:/app/data \
  sdlc-manager:latest
```

El proceso ejecuta `alembic upgrade head`, instala de forma idempotente la plantilla SDLC predeterminada y después inicia `stdio`. La migración usa el mismo archivo SQLite persistente del volumen.

## Persistencia y configuración

`/app/data` contiene la base SQLite y debe montarse como volumen. Las variables principales son:

| Variable | Valor predeterminado |
| --- | --- |
| `SDLC_MANAGER_DATABASE_URL` | `sqlite:////app/data/sdlc_manager.db` en Docker |
| `SDLC_MANAGER_POLICY_PATHS` | `['/app/knowledge/rules']` |
| `SDLC_MANAGER_AUTO_MIGRATE` | `true` |

No se agregan servicios externos. `network none` es compatible con el alcance offline del MVP.

La imagen contiene la plantilla YAML, pero no contiene archivos SQLite, proyectos, historias, experiencias ni evidencias. La base de cada instalación vive exclusivamente en el volumen `/app/data`.

Las actualizaciones no ejecutan `drop_all`, no recrean la base y no sobrescriben workflows existentes. La migración `0002_knowledge_architecture` agrega las estructuras nuevas y conserva los registros legacy.

## Configuración MCP

El ejemplo de Docker en `integrations/kiro/mcp.docker.example.json` utiliza `docker run -i`, `--network none` y el volumen persistente. El ejemplo nativo ejecuta el entry point mediante `uv`.

## Ejecución del CLI

El mismo contenedor puede procesar eventos sin iniciar MCP. El volumen debe ser escribible por el usuario no root de la imagen:

```bash
printf '%s\n' '{"event_id":"22222222-2222-4222-8222-222222222222","event_type":"session_started","source_client":"pipeline","timestamp":"2026-11-15T00:00:00Z","context":{}}' \
  | docker run --rm -i --network none \
      -v sdlc-manager-data:/app/data \
      sdlc-manager:latest event process --stdin
```

La respuesta JSON se escribe en `stdout`; los logs de migración se escriben en `stderr`. Los códigos de salida del CLI no garantizan por sí solos que un cliente externo bloquee una operación; cada adaptador debe interpretar la respuesta y el código según su contrato.

## Limitaciones

El contenedor necesita que Docker esté instalado en la computadora del cliente. El servidor no publica HTTP; un cliente debe soportar transporte `stdio`. La primera construcción requiere acceso al registro de imágenes y al índice de paquetes, pero la ejecución posterior no necesita red.

