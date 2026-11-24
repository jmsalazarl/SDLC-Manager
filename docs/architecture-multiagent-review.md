# Auditoría Arquitectónica Para Integración Multiagente

> Documento histórico de la revisión inicial. El estado vigente y el mapa de
> cumplimiento se encuentran en
> [framework-architecture-audit.md](framework-architecture-audit.md). Las
> afirmaciones de "NO IMPLEMENTADO" de este documento describen el punto de
> partida anterior y no el estado actual.

## 1. Resumen ejecutivo

**Estado:** auditoría de solo lectura. No se modificaron código fuente, modelos, migraciones ni configuraciones.

SDLC Manager tiene un núcleo reutilizable e independiente de Kiro en lo esencial. El transporte MCP se registra en src/sdlc_manager/mcp/server.py, mientras los casos de uso y motores viven fuera de MCP en src/sdlc_manager/application/services/ y src/sdlc_manager/engines/. La ejecución normal usa MCP sobre stdio, Python 3.12+ y MCP SDK 2.3.0, según pyproject.toml, src/sdlc_manager/__main__.py e integrations/kiro/mcp.native.example.json.

Conclusión:

- **IMPLEMENTADO:** servidor MCP local, contratos Pydantic, herramientas de lectura/escritura, evaluación determinista PASS/WARN/BLOCK, SQLite, Alembic, workflow predeterminado, memoria técnica, prácticas y evidencias.
- **PARCIAL:** personalización ejecutable de workflows, preferencias por alcance, aislamiento de prácticas, auditoría, aprobación de excepciones, recuperación contextual y compatibilidad específica con cada cliente.
- **NO IMPLEMENTADO:** contrato normalizado de eventos, EventDispatcher/SDLCEventProcessor, adaptador CLI de evaluación, hooks de cliente, enforcement automático antes de comandos y deduplicación de eventos.
- **NO VERIFICADO:** ejecución real con Kiro, Codex, OpenCode o Claude Code instalados. El repositorio solo contiene configuración de ejemplo para Kiro.

MCP proporciona conectividad y descubrimiento; no garantiza que un cliente invoque una herramienta ante cada evento ni que un resultado BLOCK detenga una operación externa. La activación automática y el bloqueo efectivo requieren un adaptador del cliente, un hook, una integración CI/CD o un CLI local. Esta limitación está documentada en integrations/kiro/README.md, pero todavía no hay adaptadores implementados.

La primera tarea recomendada es la Fase A: contrato de eventos normalizado y procesador independiente del cliente. La Fase B, un CLI local, debe seguir inmediatamente para permitir enforcement desde hooks sin depender de un LLM.

## 2. Arquitectura actual

### 2.1 Capas observadas

| Capa | Estado | Evidencia |
| --- | --- | --- |
| Domain | IMPLEMENTADO | src/sdlc_manager/domain/models.py, enums.py y ports/repositories.py contienen entidades, enums y protocolos sin dependencia de MCP ni SQLAlchemy. |
| Application | IMPLEMENTADO | src/sdlc_manager/application/services/sdlc_service.py concentra proyectos, HU, gates, evidencias, memoria y prácticas. workflow_service.py gestiona workflows. |
| Engines | IMPLEMENTADO | policy_engine.py, practice_engine.py, experience_engine.py y evidence_engine.py contienen lógica reutilizable. |
| Infrastructure | IMPLEMENTADO | infrastructure/container.py, database/, repositories/, policy_loader/ y workflow/ conectan SQLite, Alembic, YAML y repositorios. |
| MCP Interface | IMPLEMENTADO | mcp/server.py crea MCPServer, registra herramientas y adapta DTOs. |
| Event layer | NO IMPLEMENTADO | No existe EventDispatcher, SDLCEventProcessor, bus, inbox, outbox ni contrato de evento. |
| CLI de enforcement | NO IMPLEMENTADO | pyproject.toml expone sdlc-manager para iniciar MCP; no existe subcomando para evaluar un evento sin MCP. |

### 2.2 Transporte MCP

src/sdlc_manager/mcp/server.py crea MCPServer("sdlc-manager", version="0.1.0") y ejecuta run(). src/sdlc_manager/__main__.py ejecuta migraciones, construye el contenedor e inicia el servidor. No existe HTTP, SSE, WebSocket ni puerto TCP propio.

**Estado: IMPLEMENTADO para MCP sobre stdio; NO IMPLEMENTADO para otros transportes.**

Los ejemplos nativos y Docker están en integrations/kiro/mcp.native.example.json e integrations/kiro/mcp.docker.example.json. El servidor no importa SDKs privados de Kiro ni contiene lógica específica de otro cliente.

### 2.3 Separación entre MCP y núcleo

La separación es adecuada:

- SdlcService no importa el SDK MCP.
- WorkflowService no importa el SDK MCP.
- Los engines reciben modelos y contexto Python.
- Los repositorios se inyectan mediante protocolos.
- tests/integration/test_application.py prueba casos de uso sin cliente MCP.
- tests/integration/test_mcp_protocol.py prueba descubrimiento, stdio e invocación MCP.

**Estado: IMPLEMENTADO.**

Para futuros adaptadores se necesita un composition root y una API de aplicación explícita para eventos. Actualmente el ensamblaje de producción está orientado principalmente al servidor MCP.

### 2.4 Duplicación y acoplamiento

No se observa duplicación importante de reglas de negocio entre MCP y Application. Los handlers MCP son delgados: validan con Pydantic, llaman servicios y serializan.

Limitaciones:

1. Los DTO de personalización usan list[dict[str, Any]] para etapas, gates y excepciones. El YAML usa modelos estrictos, pero los payloads MCP no tienen validación anidada equivalente.
2. Los serializadores privados _experience_to_dict, _practice_to_dict y _evidence_to_dict están en mcp/server.py. Con CLI y adaptadores conviene compartir DTOs de salida.

## 3. Herramientas MCP existentes y sus contratos

Las herramientas se registran en src/sdlc_manager/mcp/server.py y los DTO están en src/sdlc_manager/application/schemas.py. UuidInput convierte strings JSON a UUID y conserva strict=True para el resto de los campos. tests/integration/test_mcp_protocol.py valida el esquema JSON y la invocación por stdio.

| Herramienta | Entrada principal | Salida/efecto | Estado |
| --- | --- | --- | --- |
| health_check | Sin entrada | Estado local, base, transporte y cantidad de políticas. | IMPLEMENTADO |
| list_policies | status, severity opcionales | Políticas YAML filtradas. | IMPLEMENTADO |
| get_applicable_rules | project_id, user_story_id opcional, event, stage, changed_files, component, context | Reglas aplicables; no persiste evaluación. | IMPLEMENTADO |
| evaluate_gate | project_id, user_story_id, gate, context | PASS/WARN/BLOCK y PolicyEvaluation persistida. | IMPLEMENTADO |
| register_experience | Contenido, tags, tipo, alcance, autor y relaciones | Experiencia PENDING. | IMPLEMENTADO |
| search_experiences | Texto, componente, tags, include_unreviewed | Experiencias; pendientes ocultas por defecto. | IMPLEMENTADO |
| review_experience | experience_id, status, reviewed_by | Revisión y fecha. | IMPLEMENTADO |
| register_evidence | Proyecto, HU, política, tipo y referencia | Evidencia PENDING; valida referencia. | IMPLEMENTADO |
| verify_evidence | Proyecto, evidencia, verified_by, approved | VERIFIED o REJECTED. | IMPLEMENTADO, identidad no autenticada |
| analyze_user_story | Proyecto y HU | Descripción, criterios, dependencias y reglas. | IMPLEMENTADO |
| start_sprint | Proyecto y sprint opcional | Preparación, riesgos y conteos. | IMPLEMENTADO |
| create_project | Nombre y descripción | Proyecto con workflow predeterminado. | IMPLEMENTADO |
| create_sprint | Proyecto, nombre, fechas y estado | Sprint persistido. | IMPLEMENTADO |
| create_user_story | Proyecto, sprint, título, descripción, criterios, dependencias, estado | HU persistida. | IMPLEMENTADO |
| get_sdlc_workflow | project_id | Workflow, etapas, gates y excepciones. | IMPLEMENTADO |
| customize_sdlc_workflow | Proyecto, nombre, versión, etapas, gates y excepciones | Copia derivada; excepciones PENDING. | IMPLEMENTADO, aprobación incompleta |
| register_practice | Contexto, activadores, mensaje, severidad, alcance, experiencia origen | Práctica PENDING. | IMPLEMENTADO |
| list_practices | include_unapproved | Prácticas aprobadas o todas. | IMPLEMENTADO |
| review_practice | practice_id, status, reviewed_by | Aprueba/rechaza práctica. | IMPLEMENTADO, identidad no autenticada |
| get_applicable_practices | event, stage, changed_files, component, context | Recomendaciones aprobadas, sin BLOCK. | IMPLEMENTADO |

No se registran prompts, resources ni templates MCP en mcp/server.py. Las herramientas existentes conservan sus nombres y contratos principales; las nuevas se agregan sin reemplazar las anteriores.

Los errores de validación vienen del esquema MCP y los errores de dominio de los servicios/repositorios. No existe un envelope común con error_code, retryable, event_id y trace_id.

Un BLOCK es una decisión devuelta por evaluate_gate. No detiene por sí mismo un comando, escritura, tarea o merge del cliente. El adaptador externo debe interpretar la decisión.

## 4. Modelo de dominio y persistencia

### 4.1 Entidades

src/sdlc_manager/domain/models.py contiene:

- Project, Sprint y UserStory.
- PolicyRule.
- EngineeringExperience.
- SdlcWorkflow, SdlcStage, SdlcGate y SdlcException.
- EngineeringPractice.
- Evidence y PolicyEvaluation.
- GateDecision como objeto de salida no persistente.

### 4.2 Tablas y migraciones

migrations/versions/0001_initial.py crea TPROYECTO, TSPRINT, THISTORIAUSUARIO, TEXPERIENCIA, TEVIDENCIA, TEVALUACIONPOLITICA y TAUDITORIA.

migrations/versions/0002_knowledge_architecture.py agrega TFLUJOSDLC, TETAPASDLC, TGATESDLC, TEXCEPCIONDLC y TPRACTICA; agrega la referencia de workflow a TPROYECTO y metadatos a TEXPERIENCIA.

Las correspondencias están en src/sdlc_manager/infrastructure/database/models.py.

### 4.3 Capacidades y limitaciones

| Capacidad | Estado | Diagnóstico |
| --- | --- | --- |
| Preferencias personales | PARCIAL | Se representan con memory_type=PREFERENCE y scope=PERSONAL, pero no hay PreferenceService, consulta efectiva ni propietario autenticado. |
| Prácticas por proyecto | PARCIAL | Existe scope=PROJECT, pero TPRACTICA no tiene proyecto y PracticeEngine no filtra por proyecto. |
| Experiencias técnicas | IMPLEMENTADO | TEXPERIENCIA persiste clasificación, metadatos y revisión; la instalación nueva permanece vacía. |
| Políticas aprobadas | IMPLEMENTADO para YAML | PolicyLoader valida aprobación y PolicyEngine solo bloquea reglas aprobadas. No hay administración persistente de políticas. |
| Workflow personalizado | IMPLEMENTADO | Proyecto, workflow, etapas, gates y excepciones están persistidos y se usa copy-on-write. |
| Historial de evaluaciones | PARCIAL | TEVALUACIONPOLITICA almacena decisiones, pero no hay repositorio de lectura ni herramienta de consulta. |
| Excepciones | PARCIAL | Se almacenan y nacen PENDING, pero no hay caso de uso de aprobación y evaluate_gate no las aplica. |
| Evidencias | IMPLEMENTADO | Se asocian a proyecto, HU y política; solo VERIFIED cuenta. |
| Auditoría | PARCIAL | Existe TAUDITORIA, pero no AuditRepository ni escrituras desde casos de uso. |
| Recuperación contextual | PARCIAL | ExperienceRepository usa LIKE, componente y tags; no filtra por tecnología, categoría, alcance o proyecto. |
| Instalación limpia | IMPLEMENTADO | tests/integration/test_knowledge_architecture.py verifica cero proyectos, HU, experiencias y evidencias y un workflow instalado. |

No hay una necesidad concreta de una base vectorial en esta fase. Primero deben agregarse filtros estructurados, alcance, ranking local y trazabilidad de recuperación.

### 4.4 Inicialización

src/sdlc_manager/__main__.py ejecuta Alembic cuando auto_migrate está activo. Luego infrastructure/container.py instala idempotentemente knowledge/sdlc/default.yaml.

Existe un segundo camino: mcp/server.py puede crear el servidor con initialize_schema=True y infrastructure/database/db.py usa Base.metadata.create_all. Es útil para pruebas, pero los futuros adaptadores deben usar un bootstrap común basado en migraciones para evitar esquemas divergentes.

## 5. Workflow SDD actual: etapas y gates

knowledge/sdlc/default.yaml define default-sdlc, versión 1.0.0, estado ACTIVE y nueve etapas:

| Orden | Etapa | Gate | Obligatorio | Checks/condiciones |
| ---: | --- | --- | --- | --- |
| 1 | story_refinement, Refinamiento de HU | refinement_complete | Sí | description_present |
| 2 | acceptance_criteria, Criterios de aceptación | acceptance_ready | Sí | acceptance_criteria_present |
| 3 | dependency_review, Revisión de dependencias | dependencies_ready | Sí | dependencies_resolved |
| 4 | design_approval, Aprobación de diseño | design_approved | No | design_evidence; design_required=true |
| 5 | development, Desarrollo | development_start | Sí | story_ready |
| 6 | technical_review, Revisión técnica | technical_review | Sí | review_evidence |
| 7 | testing, Testing | testing_complete | Sí | test_evidence |
| 8 | deployment_preparation, Preparación para despliegue | deployment_ready | Sí | deployment_evidence |
| 9 | closure, Cierre | task_completion | Sí | closure_evidence |

Todas las etapas están habilitadas y obligatorias salvo el gate de diseño, que es opcional. La plantilla no declara excepciones iniciales.

### Runtime

- infrastructure/workflow/loader.py valida YAML con Pydantic.
- WorkflowInitializer instala versiones ausentes y asigna el workflow a proyectos no asignados.
- application/services/workflow_service.py consulta y personaliza mediante copia.
- Project guarda CFLUJOSDLC.
- Las pruebas cubren instalación, idempotencia, migración y copy-on-write.

**Estado: IMPLEMENTADO como configuración y persistencia.**

### Brecha

Los checks y condiciones se almacenan, pero SdlcService.evaluate_gate evalúa principalmente políticas YAML mediante PolicyEngine. No ejecuta automáticamente los checks de TGATESDLC ni aplica TEXCEPCIONDLC.

Por tanto, el workflow actual funciona como catálogo/configuración consultable, mientras los bloqueos reales provienen de knowledge/rules/. Personalizar un check no cambia todavía evaluate_gate.

**Estado: PARCIAL como motor de workflow ejecutable.**

### Relación con el SDD del cliente

El SDD del repositorio está en .sdd/, según .sdd/config.yaml y AGENTS.md. Las specs documentan el desarrollo del producto.

No existe integración runtime que lea requirements.md, design.md o tasks.md externos. Tampoco existe mapeo entre una tarea SDD externa y UserStory, SdlcStage o PolicyEvaluation.

La separación recomendada es:

- SDD del cliente: archivos y convenciones del agente.
- Workflow administrado: controles y eventos normalizados.
- Adaptador: traducción del cliente al evento común.
- Núcleo: independiente del cliente.

**Estado: PARCIAL.**

### Metodologías y variantes

El loader acepta código, versión, etapas, gates y excepciones. La clave natural código-versión y el copy-on-write permiten variantes sin modificar el núcleo, según infrastructure/workflow/loader.py y workflow_service.py.

**Estado: IMPLEMENTADO como almacenamiento; PARCIAL como ejecución**, porque las condiciones no están conectadas al evaluador.

## 6. Gestión de experiencias, preferencias y prácticas

### Experience Engine

engines/experience_engine.py delega la búsqueda a ExperienceRepository. La persistencia y filtros están en infrastructure/repositories/sqlalchemy_repositories.py.

Implementado:

- Registro PENDING.
- MemoryType.
- Tecnología, categoría, alcance, autor.
- Revisión aprobada/rechazada.
- Relaciones por UUID.
- Búsqueda por texto, componente y tags.
- Pendientes ocultas por defecto.

Limitaciones:

- Sin búsqueda por proyecto o identidad.
- Sin ranking.
- Sin filtros de tecnología, categoría o scope.
- Sin FTS5.
- Relaciones almacenadas como JSON, no tabla relacional.
- Sin promoción automática o explícita a política YAML.

**Estado: IMPLEMENTADO para memoria local básica; PARCIAL para contexto relevante.**

### Preferencias

La preferencia se representa como EngineeringExperience con memory_type=PREFERENCE y scope=PERSONAL. No existe entidad de preferencias, resolución de conflictos, prioridad, vigencia ni identidad del propietario.

**Estado: PARCIAL.**

### Practice Engine

engines/practice_engine.py activa prácticas aprobadas por evento, etapa, componente y extensión. SdlcService.get_applicable_practices carga solo aprobadas.

La separación es correcta:

- TPRACTICA es independiente.
- La práctica requiere revisión.
- La experiencia origen debe estar aprobada.
- El engine no tiene camino de BLOCK.
- PolicyEngine sigue separado.

**Estado: IMPLEMENTADO para recomendación contextual global.**

El alcance PROJECT no es seguro porque no guarda project_id ni filtra por él.

### Policy Engine

engines/policy_engine.py evalúa triggers, scope y condiciones cerradas. No usa eval ni exec. Soporta all, any, equals, not_equals, exists, contains, in y file_extension_matches. Solo bloquea acciones block aprobadas.

**Estado: IMPLEMENTADO y reutilizable.**

Limitaciones:

- No consulta workflow asignado.
- No aplica excepciones.
- Políticas no se administran persistentemente.
- El cliente puede no invocar evaluate_gate.
- get_applicable_rules informa y no impone.

## 7. Mecanismos de intervención actualmente disponibles

| Mecanismo | Capacidad | Estado |
| --- | --- | --- |
| Consulta explícita MCP | Invoca reglas, gates, análisis y sprint. | IMPLEMENTADO |
| WARN | Devuelve advertencia/recomendación. | IMPLEMENTADO |
| BLOCK | Devuelve decisión explicada. | IMPLEMENTADO como decisión |
| Persistencia de decisión | TEVALUACIONPOLITICA. | IMPLEMENTADO |
| Evidencia humana | PENDING/VERIFIED/REJECTED. | IMPLEMENTADO |
| Workflow consultable | Etapas, gates y excepciones. | IMPLEMENTADO |
| Hook de cliente | Invocación automática antes/después de acción. | NO IMPLEMENTADO |
| CLI pre-acción | Evaluación sin MCP. | NO IMPLEMENTADO |
| Event dispatcher | Normalización multiagente. | NO IMPLEMENTADO |
| Bloqueo de shell/escritura/PR | Detención directa de operación. | NO IMPLEMENTADO |
| Auditoría | Registro sistemático de intervención. | PARCIAL |

Diferencias:

1. Conectividad MCP: el cliente descubre y llama herramientas.
2. Instrucciones persistentes: AGENTS.md, Steering, Skills o CLAUDE.md guían al modelo.
3. Activación automática: hook, plugin, CLI, CI o evento externo invoca el servidor.
4. Bloqueo efectivo: el mecanismo que controla la operación niega la acción tras recibir BLOCK.

El MVP alcanza el punto 1 y parte del 2. No alcanza de forma nativa los puntos 3 y 4. Una instrucción persistente nunca debe presentarse como una garantía de enforcement.

## 8. Compatibilidad con Kiro, Codex, OpenCode y Claude Code

No se ejecutó ningún cliente externo desde este entorno. La compatibilidad concreta de cada instalación es NO VERIFICADA.

### 8.1 Kiro

Repositorio:

- Configuración MCP nativa y Docker en integrations/kiro/.
- Guía en integrations/kiro/README.md.
- Sin .kiro/settings/mcp.json.
- Sin .kiro/hooks/*.json.
- Sin adaptador de eventos.

Documentación oficial verificada:

- Kiro documenta MCP local stdio, JSON, tools, prompts y resources: [Kiro MCP](https://kiro.dev/docs/cli/mcp/).
- Kiro documenta Session Start, File Save, Pre Task Execution, Pre Tool Use y Post Tool Use. Pre Tool Use puede validar y bloquear herramientas MCP: [Kiro Hooks](https://kiro.dev/docs/hooks/types/).
- Kiro documenta IDs MCP internos como mcp_<server>_<tool> para Hooks V3: [Kiro MCP tool hooks](https://kiro.dev/docs/hooks/types/).

| Capacidad | Estado |
| --- | --- |
| MCP | IMPLEMENTADO mediante ejemplos; cliente real NO VERIFICADO |
| Steering/SDD | NO IMPLEMENTADO como adaptador |
| Hooks | NO IMPLEMENTADO |
| Eventos automáticos | NO IMPLEMENTADO |
| Advertencias | Disponibles si se llama MCP; automáticas NO IMPLEMENTADAS |
| Bloqueos | No implementados en el repositorio; Kiro ofrece el punto de extensión |
| Memoria/experiencias | Herramientas IMPLEMENTADAS |

### 8.2 OpenAI Codex

Repositorio:

- AGENTS.md existe.
- No existe configuración específica Codex.
- No existe plugin, hooks/hooks.json, skill ni adaptador Codex.
- El proceso stdio es reutilizable técnicamente.

Documentación oficial verificada:

- Codex reconoce AGENTS.md como guía persistente del repositorio: [Codex AGENTS.md](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex).
- OpenAI documenta MCP stdio como proceso dentro del entorno de sesión: [OpenAI MCP connections](https://developers.openai.com/api/docs/guides/agents-api/tools/mcp).
- Plugins pueden incluir Skills, MCP y lifecycle hooks, pero los scripts deben existir en el entorno y los hooks requieren confianza/revisión: [OpenAI plugin architecture](https://developers.openai.com/plugins/concepts/plugins) y [OpenAI plugin hooks](https://developers.openai.com/plugins/build/plugins).

| Capacidad | Estado |
| --- | --- |
| MCP | PARCIAL; no probado con Codex instalado |
| AGENTS.md | IMPLEMENTADO |
| Skills | NO IMPLEMENTADO como skill de cliente |
| Hooks/plugins | NO IMPLEMENTADO |
| Eventos automáticos | NO VERIFICADO |
| Bloqueos | Dependen de hook externo; MCP no garantiza bloqueo |
| Memoria | Herramientas disponibles si se configura MCP |

AGENTS.md orienta al agente; no convierte por sí mismo una respuesta BLOCK en una política de ejecución.

### 8.3 OpenCode

Repositorio:

- AGENTS.md existe.
- No existe opencode.json, opencode.jsonc ni .opencode/.
- No existe plugin ni hook OpenCode.

Documentación oficial verificada:

- OpenCode configura MCP local con mcp.servers, type local, command, cwd y environment: [OpenCode MCP servers](https://opencode.ai/docs/mcp-servers).
- OpenCode carga AGENTS.md como guía persistente y jerárquica: [OpenCode instructions](https://opencode.ai/docs/instructions).
- OpenCode V2 no usa CLAUDE.md como fallback: [OpenCode instructions](https://opencode.ai/docs/instructions).
- Plugins pueden agregar herramientas, hooks, integraciones, comandos y agentes: [OpenCode plugins](https://opencode.ai/docs/build/plugins/).

| Capacidad | Estado |
| --- | --- |
| MCP | PARCIAL; configuración no creada ni probada |
| AGENTS.md | IMPLEMENTADO |
| Plugins/hooks | NO IMPLEMENTADO |
| Eventos automáticos | NO IMPLEMENTADO |
| Bloqueos | Dependen de plugin/hook externo |
| Memoria | Herramientas disponibles si se configura MCP |

### 8.4 Claude Code

Repositorio:

- AGENTS.md existe.
- No existe CLAUDE.md.
- No existe .mcp.json, .claude/settings.json ni .claude/hooks/.
- No existe skill ni hook específico.

Documentación oficial verificada:

- Claude Code soporta MCP y servidores locales stdio: [Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp).
- Puede usar CLAUDE.md o AGENTS.md como instrucciones persistentes: [Claude Code memory](https://docs.anthropic.com/en/docs/claude-code/memory).
- Usa SKILL.md para Skills: [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code/skills).
- PreToolUse puede devolver permissionDecision=deny; también existen FileChanged y TaskCompleted: [Claude Code hooks](https://docs.anthropic.com/en/docs/claude-code/hooks).

| Capacidad | Estado |
| --- | --- |
| MCP | PARCIAL; soporte oficial, cliente no probado |
| AGENTS.md | IMPLEMENTADO |
| CLAUDE.md/Skills | NO IMPLEMENTADO |
| Hooks | NO IMPLEMENTADO |
| Eventos automáticos | NO IMPLEMENTADO |
| Bloqueos | Posibles por Hooks, no configurados |
| Memoria | Herramientas disponibles si se configura MCP |

### Conclusión multiagente

MCP es el punto común. Los archivos de instrucciones son complementarios:

- MCP descubre y ejecuta.
- Skills/Steering/AGENTS/CLAUDE explican cuándo usar.
- Hooks/plugins generan eventos.
- CLI o hook interpreta BLOCK y detiene la operación.

## 9. Brechas arquitectónicas identificadas

### B1 — Contrato de eventos común

**NO IMPLEMENTADO.** No existe envoltura con event_id, source_client, timestamp y contexto. Los eventos son strings en DTOs MCP. Evidencia: ausencia de módulo de eventos e integrations, y schemas.py.

### B2 — Activación automática y bloqueo externo

**NO IMPLEMENTADO.** No hay hooks ni CLI que evalúen antes de archivo, comando, tarea o PR. PolicyEngine no controla el sistema de archivos ni procesos. Evidencia: mcp/server.py, __main__.py e integrations/kiro/README.md.

### B3 — Workflow no conectado al evaluador

**PARCIAL.** Los datos de TGATESDLC/TEXCEPCIONDLC se consultan, pero evaluate_gate usa reglas YAML y no ejecuta checks ni excepciones. Evidencia: workflow_service.py, sdlc_service.py y policy_engine.py.

### B4 — Alcances incompletos

**PARCIAL.** scope=PROJECT existe, pero TPRACTICA no tiene proyecto y la búsqueda de memoria no filtra alcance/propietario. Evidencia: domain/models.py, database/models.py, practice_engine.py y repositories/sqlalchemy_repositories.py.

### B5 — Aprobación sin identidad confiable

**PARCIAL.** reviewed_by, verified_by y approved_by son textos de entrada sin autenticación/autorización. Evidencia: application/schemas.py, sdlc_service.py y repositorios.

### B6 — Auditoría sin emisión

**PARCIAL.** TAUDITORIA existe, pero no hay AuditRepository ni escrituras. Evidencia: database/models.py y 0001_initial.py.

### B7 — Recuperación contextual limitada

**PARCIAL.** LIKE, componente y tags no proporcionan ranking, tecnología, categoría, alcance, proyecto ni explicación de relevancia. Evidencia: repositories/sqlalchemy_repositories.py y experience_engine.py.

### B8 — DTOs anidados débiles

**PARCIAL.** Personalización y activadores aceptan dict[str, Any], mientras loader.py sí tiene modelos estrictos.

### B9 — Bootstrap divergente

**PARCIAL.** __main__.py usa Alembic, mientras create_server puede usar create_all. Evidencia: __main__.py, mcp/server.py, db.py y migrations.py.

## 10. Arquitectura objetivo con Mermaid

La arquitectura recomendada mantiene un único núcleo y coloca la variación en adaptadores delgados:

~~~mermaid
flowchart LR
    K[Kiro MCP Hooks Steering]
    C[Codex MCP AGENTS Plugins]
    O[OpenCode MCP AGENTS Plugins]
    A[Claude Code MCP CLAUDE Hooks]
    X[Otros clientes MCP]
    CLI[CLI local para Hooks y CI]

    K --> AD[Client Adapters]
    C --> AD
    O --> AD
    A --> AD
    X --> AD
    CLI --> AD

    AD --> EV[EventDispatcher / SDLCEventProcessor]
    EV --> N[Normalizador y validador]
    N --> DEDUP[Idempotencia]
    DEDUP --> APP[Application Services]

    APP --> WF[Workflow Service]
    APP --> POL[Policy Engine]
    APP --> MEM[Experience Engine]
    APP --> PRA[Practice Engine]
    APP --> EVI[Evidence Engine]
    APP --> AUD[Audit Service]

    WF --> DOM[Domain Models and Ports]
    POL --> DOM
    MEM --> DOM
    PRA --> DOM
    EVI --> DOM
    AUD --> DOM

    DOM --> REPO[SQLAlchemy Repositories]
    REPO --> DB[(SQLite)]
    DB --> MIG[Alembic]

    APP --> OUT[Decision Envelope]
    OUT --> AD
~~~

### Contrato de evento propuesto

Debe vivir en dominio/aplicación y no depender de MCP:

~~~text
EventEnvelope
- event_id: UUID
- event_type: EventType
- source_client: string
- project_id: UUID
- user_story_id: UUID | null
- stage: string | null
- timestamp: datetime UTC
- affected_files: list[string]
- context: object
~~~

Tipos iniciales sugeridos:

~~~text
session_started
sprint_started
user_story_started
sdd_task_started
file_changed
critical_component_changed
task_completed
gate_evaluation_requested
pull_request_ready
incident_recorded
~~~

Reglas:

1. Validar event_id, tipo, timestamp y UUID.
2. Exigir project_id para eventos de workflow.
3. Resolver proyecto, HU y workflow antes de llamar engines.
4. Normalizar contexto sin ejecutar expresiones.
5. Seleccionar caso de uso por event_type.
6. Registrar auditoría y resultado.
7. Devolver decisión, reglas, prácticas, evidencias faltantes, errores y estado.

Duplicados deben resolverse por event_id y devolver el resultado previo o DUPLICATE sin efectos repetidos. Eventos incompletos deben ser REJECTED o DEFERRED, nunca interpretados de forma ambigua. Los errores transitorios deben ser RETRYABLE_ERROR; los errores de política no deben degradarse silenciosamente a PASS.

No se requiere broker ni microservicio. Una tabla de recepción/idempotencia o ampliación controlada de TAUDITORIA, un servicio de aplicación y SQLite son suficientes inicialmente.

## 11. Roadmap recomendado

### Fase A — Contrato de eventos y procesador independiente

**Estado actual:** NO IMPLEMENTADO.

**Dependencias:** servicios, repositorios y evaluación existentes.

**Entregables:** EventEnvelope, enum de eventos, EventDispatcher/SDLCEventProcessor, validación, idempotencia, envelope de decisión/error, auditoría y tests sin MCP.

**Criterios de aceptación:**

- WHEN se recibe un evento válido, THE EventProcessor SHALL normalizarlo y seleccionar el caso de uso.
- IF se repite event_id, THEN THE EventProcessor SHALL devolver el resultado previo sin duplicar efectos.
- IF falta un campo requerido, THEN THE EventProcessor SHALL rechazar con código estructurado.
- WHEN una política aprobada incumple un gate, THE EventProcessor SHALL devolver BLOCK con trazabilidad.
- WHEN una práctica aplica, THE EventProcessor SHALL devolver recomendación sin BLOCK.

**Riesgos:** exceso de eventos iniciales y ambigüedad entre etapa y gate.

### Fase B — Adaptador CLI local

**Estado actual:** NO IMPLEMENTADO.

**Dependencias:** Fase A.

**Entregables:** JSON por stdin/argumentos, evaluación de evento/gate, códigos de salida estables, JSON por stdout, logs por stderr, modo diagnóstico y guía para Hooks/CI.

**Criterios de aceptación:**

- WHEN un Hook invoca el CLI con evento válido, THE CLI SHALL devolver JSON sin iniciar MCP.
- IF el resultado es BLOCK, THEN THE CLI SHALL devolver un código de salida bloqueante.
- IF el JSON es inválido, THEN THE CLI SHALL no ejecutar reglas ni guardar datos parciales.
- WHEN se repite event_id, THE CLI SHALL conservar idempotencia.

**Riesgos:** permisos, SQLite concurrente y decisiones incorrectas por indisponibilidad.

### Fase C — Integración con Kiro

**Estado actual:** MCP de ejemplo IMPLEMENTADO; Hooks NO IMPLEMENTADOS.

**Dependencias:** A y B.

**Entregables:** MCP opcional por workspace, Hooks para eventos soportados, traducción a EventEnvelope, Steering informativo y pruebas en las superficies Kiro objetivo.

**Criterios:** emitir evento al iniciar tareas, bloquear Pre Tool Use cuando la superficie lo soporte y documentar que MCP aislado no activa llamadas.

**Riesgos:** diferencias IDE/CLI/Web/Mobile y cambios de IDs internos.

### Fase D — Integración con Codex

**Estado actual:** AGENTS.md IMPLEMENTADO; MCP/plugin/hooks NO IMPLEMENTADOS.

**Dependencias:** A y B; validar la superficie Codex objetivo.

**Entregables:** configuración MCP, Skill opcional, plugin/hook si el entorno permite scripts confiables, adaptación de eventos disponibles y documentación por runtime.

**Criterios:** descubrir herramientas, emitir source_client=codex, clasificar como no disponible cualquier evento no verificado y mapear BLOCK solo a un mecanismo documentado.

**Riesgos:** diferencias CLI/plugins/entornos gestionados y confianza de scripts.

### Fase E — Integración con OpenCode

**Estado actual:** AGENTS.md IMPLEMENTADO; MCP/plugin/hooks NO IMPLEMENTADOS.

**Dependencias:** A y B.

**Entregables:** opencode.jsonc opcional, mcp.servers local, plugin si se necesita interceptar operaciones, adaptación y tests de versión.

**Criterios:** cargar MCP local, emitir source_client=opencode y declarar no disponible el enforcement sin plugin/hook.

**Riesgos:** cambios V1/V2, Code Mode y permisos.

### Fase F — Integración con Claude Code

**Estado actual:** MCP genérico reutilizable; CLAUDE.md, Skills y Hooks NO IMPLEMENTADOS.

**Dependencias:** A y B.

**Entregables:** configuración MCP, CLAUDE.md solo si agrega valor, Skill, PreToolUse para puntos bloqueables y adaptación de eventos soportados.

**Criterios:** enviar evento desde hook, devolver deny en BLOCK y declarar instrucciones como guidance si no existe Hook.

**Riesgos:** runtimes MCP v1/v2, permisos y cambios de versión.

### Fase G — Compatibilidad y documentación

**Estado actual:** NO IMPLEMENTADO como matriz.

**Dependencias:** C, D, E y F.

**Entregables:** matriz por cliente/versión/transporte/evento/bloqueo, contract tests MCP, fixtures de adaptadores, duplicados, errores, guías y limitaciones verificadas.

**Criterios:** cada cliente debe tener prueba de descubrimiento, indicar automatización y bloqueo, y producir la misma decisión ante el mismo evento normalizado.

## 12. Riesgos y decisiones pendientes

### Riesgos

1. Bloqueo ilusorio si el cliente muestra BLOCK pero continúa.
2. Bypass si el agente no envía el evento.
3. Aprobaciones no confiables por identidad textual.
4. Prácticas PROJECT aplicadas fuera del proyecto.
5. Workflow declarativo no ejecutado.
6. Duplicados sin event_id.
7. Auditoría incompleta.
8. Bootstrap divergente.
9. DTOs anidados permisivos.
10. Diferencias entre clientes.

### Decisiones pendientes

1. ¿Workflow o YAML será el único origen de checks?
2. ¿Dónde se aplicarán excepciones?
3. ¿Prácticas PROJECT requieren project_id?
4. ¿Quién puede aprobar memorias, prácticas, evidencias y excepciones?
5. ¿Cómo se verifica identidad?
6. ¿Qué política rige ante error: fail-open, fail-closed o UNKNOWN?
7. ¿Qué eventos son obligatorios?
8. ¿Se auditan todos los eventos o solo decisiones?
9. ¿Qué versiones concretas de clientes se soportarán?
10. ¿Dónde se ejecutará el CLI: Hooks, CI, wrappers o todos?
11. ¿Una base por workspace o una base multi-proyecto?
12. ¿Qué filtros de privacidad se requieren para memoria?

## 13. Archivos del repositorio que deberían revisarse en profundidad

### Núcleo y contratos

- src/sdlc_manager/domain/models.py
- src/sdlc_manager/domain/enums.py
- src/sdlc_manager/domain/ports/repositories.py
- src/sdlc_manager/application/schemas.py
- src/sdlc_manager/application/services/sdlc_service.py
- src/sdlc_manager/application/services/workflow_service.py

### Engines

- src/sdlc_manager/engines/policy_engine.py
- src/sdlc_manager/engines/practice_engine.py
- src/sdlc_manager/engines/experience_engine.py
- src/sdlc_manager/engines/evidence_engine.py

### MCP y bootstrap

- src/sdlc_manager/mcp/server.py
- src/sdlc_manager/__main__.py
- src/sdlc_manager/config.py
- src/sdlc_manager/infrastructure/container.py
- src/sdlc_manager/infrastructure/database/db.py
- src/sdlc_manager/infrastructure/database/migrations.py

### Persistencia

- src/sdlc_manager/infrastructure/database/models.py
- src/sdlc_manager/infrastructure/repositories/sqlalchemy_repositories.py
- migrations/versions/0001_initial.py
- migrations/versions/0002_knowledge_architecture.py

### Workflow y conocimiento

- knowledge/sdlc/default.yaml
- src/sdlc_manager/infrastructure/workflow/loader.py
- knowledge/rules/generic/sprint.yaml
- knowledge/rules/generic/performance.yaml
- knowledge/rules/demo/forms.yaml

### Pruebas y documentación

- tests/integration/test_mcp_protocol.py
- tests/integration/test_application.py
- tests/integration/test_knowledge_architecture.py
- tests/unit/test_policy_engine.py
- tests/unit/test_input_schemas.py
- docs/architecture.md
- docs/mcp-tools.md
- docs/docker.md
- integrations/kiro/README.md
- AGENTS.md
- .sdd/config.yaml
- .sdd/specs/mcp-server-mvp/
- .sdd/specs/knowledge-architecture/

## 14. Conclusión arquitectónica

SDLC Manager está bien posicionado como núcleo local de políticas, memoria, evidencias y workflow, no como integración específica de un solo asistente. La separación actual permite agregar adaptadores sin duplicar el motor determinista.

Debe considerarse un MVP MCP reutilizable, pero todavía no un sistema multiagente con enforcement automático.

Garantías reales actuales:

- Validación de entradas MCP.
- Evaluación determinista cuando se invoca el caso de uso.
- BLOCK para reglas YAML aprobadas.
- Verificación explícita de evidencias.
- Persistencia local.
- Separación de prácticas no bloqueantes.

Garantías ausentes:

- Invocación automática.
- Bloqueo de comandos, archivos, tareas o PR.
- Identidad confiable del aprobador.
- Aplicación de excepciones.
- Ámbito por proyecto de prácticas.
- Auditoría completa.
- Compatibilidad ejecutada con cada cliente.

La evolución recomendada conserva MCP como adaptador de conectividad y agrega contrato de eventos, procesador de aplicación y CLI local. Después se conectan Kiro, Codex, OpenCode y Claude Code mediante adaptadores delgados.

La regla arquitectónica debe ser:

~~~text
Cliente/agente = origen de eventos e interfaz
Adaptador = traducción y control de integración
SDLCEventProcessor = coordinación normalizada
Policy/Workflow/Practice/Evidence engines = decisión de dominio
Persistencia = estado y trazabilidad
~~~

Así, un cambio de cliente no modifica el núcleo ni convierte instrucciones persistentes en controles de seguridad falsos.

