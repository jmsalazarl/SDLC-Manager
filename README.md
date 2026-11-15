# SDLC Manager

Servidor MCP local para gobernanza del ciclo de vida de desarrollo de software, memoria técnica y evaluación determinista de políticas.

## Descripción

SDLC Manager permite consultar experiencias técnicas, detectar riesgos, registrar evidencias y evaluar gates con decisiones `PASS`, `WARN` o `BLOCK`. El MVP funciona sin servicios externos, credenciales corporativas ni conectividad de red durante su ejecución.

Las políticas se declaran en YAML y se validan con Pydantic. El motor de políticas no usa `eval`, `exec`, LLM ni acceso a sistemas de producción.

## Características

- Servidor MCP con transporte `stdio` basado en MCP Python SDK `2.3.0`.
- Persistencia local SQLite mediante SQLAlchemy 2.x y migraciones Alembic.
- Reglas deterministas con operadores cerrados.
- Memoria de experiencias con búsqueda textual local.
- Workflow SDLC predeterminado, versionado y personalizable por proyecto.
- Memoria clasificada y prácticas de ingeniería separadas de las políticas obligatorias.
- Evidencias `PENDING`, `VERIFIED` o `REJECTED` con verificación humana explícita.
- Aislamiento de datos por proyecto.
- Procesamiento idempotente de eventos SDLC normalizados.
- CLI universal para procesar eventos desde stdin sin iniciar MCP.
- Paquetes de conocimiento genéricos y de demostración.
- Imagen Docker multi-stage con volumen persistente en `/app/data`.

## Arquitectura

```text
Cliente MCP --stdio--> MCP Interface --> Application Services
                                             |        |
                                      Policy Engine  Experience/Evidence
                                             |        |
                                      SQLite + Alembic
```

La lógica de negocio se ejecuta desde servicios Python independientes del transporte MCP. Los detalles están en [docs/architecture.md](docs/architecture.md).

## Requisitos

- Python 3.12 o superior.
- `uv`.
- Docker, únicamente para la ejecución contenedorizada.

## Instalación nativa

```bash
uv sync
cp .env.example .env
uv run alembic upgrade head
```

La instalación crea únicamente el esquema y la plantilla SDLC predeterminada. La memoria, los proyectos, las historias y las evidencias comienzan vacíos.

## Ejecución nativa

El servidor usa `stdio`; no abre puertos y reserva `stdout` para el protocolo MCP.

```bash
uv run sdlc-manager
```

El directorio de datos predeterminado es `./data`. Se puede cambiar mediante `SDLC_MANAGER_DATABASE_URL`.

Para procesar un evento desde un Hook, script o pipeline:

```bash
printf '%s\n' '{"event_id":"22222222-2222-4222-8222-222222222222","event_type":"session_started","source_client":"pipeline","timestamp":"2026-11-15T00:00:00Z","context":{}}' \
  | uv run sdlc-manager event process --stdin
```

El CLI escribe la respuesta JSON en `stdout` y los logs en `stderr`. Sus códigos de salida están documentados en [docs/universal-cli-validation.md](docs/universal-cli-validation.md).

## Ejecución con Docker

```bash
docker build -t sdlc-manager:latest .
docker run --rm -i \
  --network none \
  -v sdlc-manager-data:/app/data \
  sdlc-manager:latest
```

Docker Compose está disponible para desarrollo local, pero no es necesario para conectar un cliente MCP:

```bash
docker compose run --rm sdlc-manager
```

Consulta [docs/docker.md](docs/docker.md) para persistencia y migraciones.

## Configuración MCP

Hay ejemplos para ejecución nativa y Docker en [integrations/kiro/](integrations/kiro/). La configuración nativa esperada es:

```json
{
  "mcpServers": {
    "sdlc-manager": {
      "command": "uv",
      "args": ["run", "--frozen", "sdlc-manager"],
      "disabled": false
    }
  }
}
```

Conectar el servidor no activa invocaciones automáticas. Los Hooks o integraciones explícitas deben decidir cuándo llamar cada herramienta.

## Ejemplo de uso

1. Invocar `create_project` y `create_user_story` para preparar datos locales.
2. Invocar `get_applicable_rules` con `event=file_change` y un archivo `.wpx`.
3. Invocar `evaluate_gate` en `task_completion`.
4. Registrar cada evidencia requerida con `register_evidence`.
5. Verificarla mediante `verify_evidence` y repetir la evaluación.
6. Consultar `get_sdlc_workflow` para revisar etapas y gates del proyecto.

## Pruebas y calidad

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

La suite cubre el motor de políticas, persistencia SQLite, aislamiento por proyecto, ciclo de evidencias, memoria de experiencias e invocaciones MCP en memoria y por `stdio`.

## Documentación

- [Arquitectura](docs/architecture.md)
- [Motor de políticas](docs/policy-engine.md)
- [Herramientas MCP](docs/mcp-tools.md)
- [Validación del Event Processor](docs/event-processor-validation.md)
- [Validación del CLI universal](docs/universal-cli-validation.md)
- [Validación de Workflow Enforcement](docs/workflow-enforcement-validation.md)
- [Docker](docs/docker.md)
- [Roadmap](docs/roadmap.md)
- [Spec de arquitectura de conocimiento](.sdd/specs/knowledge-architecture/requirements.md)
- [AGENTS.md](AGENTS.md)

## Limitaciones del MVP

- No incluye embeddings ni búsqueda semántica.
- No integra Azure DevOps, producción, servicios cloud ni autenticación empresarial.
- La aprobación de evidencias es local y requiere una llamada explícita.
- Las prácticas requieren revisión explícita y no producen bloqueos por sí mismas.
- El CLI no implementa Hooks ni adaptadores específicos de clientes.
- Los paquetes de conocimiento de demostración contienen únicamente datos ficticios.

## Seguridad

El servidor no ejecuta comandos desde YAML, no lee rutas arbitrarias, no modifica código mediante herramientas MCP, no realiza llamadas externas y no registra secretos. Las decisiones se almacenan con su evaluación y las evidencias mantienen su estado de verificación.

