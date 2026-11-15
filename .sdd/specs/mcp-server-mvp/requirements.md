# Documento de Requerimientos

## Introducción

SDLC Manager es un servidor MCP local que conserva conocimiento técnico, evalúa políticas de ingeniería y entrega decisiones trazables durante el ciclo de vida de desarrollo. El MVP opera sin credenciales corporativas, servicios de IA externos, sistemas de producción, base de datos remota ni conectividad obligatoria durante su ejecución.

El producto complementa a los clientes MCP y a Kiro; no reemplaza al asistente, al repositorio ni a los Hooks. Las decisiones obligatorias deben depender de reglas verificables y aprobadas.

## Glosario

| Término | Definición |
| --- | --- |
| Cliente MCP | Aplicación que descubre e invoca herramientas del servidor mediante `stdio`. |
| Política | Regla versionada en YAML con alcance, condiciones, evidencias, gate y acción. |
| Gate | Punto de control del SDLC que recibe `PASS`, `WARN` o `BLOCK`. |
| Evidencia | Registro asociado a una HU y política que demuestra un control. |
| Experiencia | Lección técnica persistente pendiente o aprobada. |
| HU | Historia de usuario con descripción, criterios y dependencias. |
| Knowledge Pack | Conjunto versionado de políticas para un contexto de uso. |
| Verificación humana | Aprobación explícita con identificador y fecha; no se infiere de texto generado. |

## Alcance MVP

- Servidor MCP local con transporte `stdio`.
- Políticas YAML genéricas y de demostración.
- Evaluación determinista de reglas con operadores cerrados.
- Proyectos, sprints e historias de usuario locales.
- Registro y búsqueda textual de experiencias.
- Registro, verificación y consulta de evidencias.
- Persistencia SQLite con SQLAlchemy y Alembic.
- Distribución mediante `uv` y Docker.
- Configuraciones de ejemplo para Kiro.

## Fuera de Alcance Inicial

- Frontend, microservicios y despliegues productivos.
- PostgreSQL, vector database y embeddings.
- Azure DevOps, sistemas corporativos y acceso a producción.
- Autenticación empresarial, notificaciones remotas y telemetría.
- Hooks corporativos automáticos.
- Interpretación semántica avanzada basada en LLM.

## Actores

1. **Desarrollador o líder técnico:** consulta reglas, registra experiencias y evidencias.
2. **Cliente MCP:** inicia el proceso y consume herramientas estructuradas.
3. **Revisor autorizado:** verifica o rechaza evidencias mediante una operación explícita.
4. **Mantenedor del paquete:** versiona y aprueba políticas YAML.

## Requerimientos

### Requirement 1: Servidor MCP local

**User Story:** Como usuario de un cliente MCP, quiero descubrir e invocar capacidades de SDLC Manager localmente, para consultar conocimiento y ejecutar controles sin depender de servicios externos.

#### Acceptance Criteria

1. WHEN el proceso inicia mediante el entry point nativo o Docker, THE MCP_Server SHALL usar transporte `stdio` y reservar `stdout` para mensajes MCP.
2. WHEN un cliente MCP solicita las herramientas, THE MCP_Server SHALL publicar todas las herramientas del MVP con entradas tipadas y salidas estructuradas.
3. WHEN el cliente invoca una herramienta con datos inválidos, THE MCP_Server SHALL devolver un error identificable sin ejecutar el caso de uso.
4. WHERE la ejecución está desconectada de la red, THE MCP_Server SHALL continuar operando con SQLite y políticas locales.

### Requirement 2: Políticas deterministas

**User Story:** Como mantenedor de ingeniería, quiero definir reglas en YAML sin modificar el adaptador MCP, para agregar controles verificables de forma versionada.

#### Acceptance Criteria

1. WHEN el servidor carga un archivo YAML, THE Policy_Loader SHALL validarlo con un esquema estricto y rechazar campos desconocidos o estructuras inválidas.
2. WHEN una política contiene un operador no permitido, THE Policy_Engine SHALL devolver un error identificable y SHALL NOT ejecutar código arbitrario.
3. WHEN un evento coincide con trigger, scope y condiciones, THE Policy_Engine SHALL identificar la política aplicable junto con su severidad, acción y gate.
4. WHEN una regla `block` activa y aprobada tiene una condición incumplida o evidencia obligatoria faltante, THE Policy_Engine SHALL emitir `BLOCK`.
5. WHEN una regla de recomendación aplicable no bloquea el flujo, THE Policy_Engine SHALL emitir `WARN`.
6. WHEN no existe un incumplimiento obligatorio, THE Policy_Engine SHALL emitir `PASS`.
7. WHERE una política está deshabilitada o no aprobada, THE Policy_Engine SHALL NOT usarla para un bloqueo obligatorio.

### Requirement 3: Reglas de demostración

**User Story:** Como equipo que valida el MVP, quiero reproducir controles ficticios de formularios, rendimiento y preparación de HU, para comprobar el motor sin información corporativa.

#### Acceptance Criteria

1. WHEN un evento de cambio incluye un archivo `.wpx`, THE Policy_Engine SHALL aplicar `SDLC-001` en `task_completion` y SHALL requerir `production_version`, `comparison_result` y `compatibility_validation`.
2. WHEN `SDLC-001` no tiene todas sus evidencias verificadas, THE Policy_Engine SHALL emitir `BLOCK`.
3. WHEN `SDLC-001` tiene todas sus evidencias verificadas, THE Policy_Engine SHALL permitir `PASS` si no hay otra infracción.
4. WHEN un evento `report_change` afecta los componentes `reporting` o `database`, THE Policy_Engine SHALL aplicar `SDLC-002` y emitir `WARN`.
5. WHEN inicia el desarrollo de una HU sin criterios de aceptación o con dependencias no resueltas, THE Policy_Engine SHALL aplicar `SDLC-003` y emitir `BLOCK` en `development_start`.

### Requirement 4: Memoria de experiencias

**User Story:** Como líder técnico, quiero registrar y buscar experiencias revisadas, para prevenir la repetición de incidentes.

#### Acceptance Criteria

1. WHEN se registra una experiencia, THE Experience_Service SHALL persistirla en estado `PENDING` con fecha, componente, etiquetas y políticas relacionadas.
2. WHEN se busca por texto, componente o etiquetas, THE Experience_Service SHALL devolver coincidencias desde SQLite sin usar embeddings.
3. WHERE una experiencia permanece `PENDING` o `REJECTED`, THE Experience_Service SHALL excluirla de búsquedas normales.
4. WHEN una experiencia se registra o consulta, THE Experience_Service SHALL NOT activar ni modificar automáticamente una política.

### Requirement 5: Evidencias y decisiones

**User Story:** Como revisor autorizado, quiero registrar y verificar evidencias, para que las decisiones de gate sean trazables y no dependan de una afirmación no verificada.

#### Acceptance Criteria

1. WHEN se registra una evidencia, THE Evidence_Service SHALL asociarla con proyecto, HU y política en estado `PENDING`.
2. WHEN una evidencia recibe aprobación humana explícita, THE Evidence_Service SHALL cambiarla a `VERIFIED` y almacenar identificador y fecha de verificación.
3. WHEN una evidencia es rechazada, THE Evidence_Service SHALL cambiarla a `REJECTED` y SHALL NOT considerarla satisfecha.
4. WHEN se evalúa un gate, THE Policy_Engine SHALL considerar únicamente evidencias `VERIFIED` del mismo proyecto, HU y política.
5. WHEN se completa una evaluación, THE Evaluation_Service SHALL persistir resultado, gate, reglas activadas, evidencias faltantes, explicación y fecha.
6. WHEN se recibe una referencia de evidencia con una ruta local absoluta o segmento `..`, THE Evidence_Service SHALL rechazarla sin leer el sistema anfitrión.

### Requirement 6: Contexto de SDLC

**User Story:** Como equipo de desarrollo, quiero analizar historias y sprints, para detectar riesgos antes de iniciar trabajo.

#### Acceptance Criteria

1. WHEN se analiza una HU, THE Story_Service SHALL detectar descripción ausente, criterios de aceptación ausentes y dependencias pendientes.
2. WHEN se inicia el análisis de un sprint, THE Sprint_Service SHALL revisar todas las HUs del proyecto o sprint solicitado y devolver preparación, riesgos y dependencias.
3. WHERE una HU pertenece a otro proyecto, THE Story_Service SHALL impedir su consulta o evaluación desde el proyecto actual.

### Requirement 7: Distribución, seguridad y calidad

**User Story:** Como mantenedor del producto, quiero instalar, probar y distribuir el MVP reproduciblemente, para que otro desarrollador pueda ejecutarlo sin configurar infraestructura corporativa.

#### Acceptance Criteria

1. WHEN se ejecuta `uv sync`, THE Project SHALL instalar las dependencias fijadas por `uv.lock`.
2. WHEN se ejecuta la imagen Docker, THE Runtime SHALL usar un usuario no root, persistir SQLite en `/app/data` y ejecutar migraciones compatibles al inicio.
3. WHERE el contenedor se ejecuta con `--network none`, THE Runtime SHALL iniciar el servidor sin servicios externos.
4. WHEN se ejecutan pytest, Ruff y mypy, THE Project SHALL validar las pruebas, formato, lint y tipado configurados.
5. WHERE un cliente invoca herramientas MCP, THE Runtime SHALL NOT ejecutar comandos, `eval`, `exec`, telemetría externa ni modificaciones de código.

### Requirement 8: UUID en la frontera MCP

**User Story:** Como cliente MCP, quiero enviar identificadores UUID válidos como cadenas JSON, para invocar las herramientas sin conocer la representación interna de Python.

#### Acceptance Criteria

1. WHEN una herramienta MCP recibe un UUID válido serializado como cadena JSON, THE MCP_Interface SHALL convertirlo a `uuid.UUID` antes de invocar el servicio de aplicación.
2. WHEN una herramienta MCP recibe un UUID vacío, mal formado o de tipo no permitido, THE MCP_Interface SHALL rechazar la entrada con un error de validación.
3. WHERE un DTO MCP declara un UUID, THE MCP_Interface SHALL publicar en JSON Schema `type: string` y `format: uuid`.
4. WHEN se revisan las herramientas que reciben identificadores, THE MCP_Interface SHALL aplicar el mismo contrato a proyectos, historias, sprints y evidencias.
5. WHERE se corrige la conversión de entrada, THE Policy_Engine SHALL permanecer sin cambios funcionales.

## Trazabilidad funcional

La relación detallada entre requisitos, diseño, tareas y pruebas se encuentra en `.sdd/traceability.yaml`.

