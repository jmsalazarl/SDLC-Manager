# Requirements Document

## Introduction

SDLC Manager debe validar cada cambio con un pipeline de GitHub Actions que cubra calidad de código, pruebas, seguridad, vulnerabilidades, build y SBOM, sin agregar servicios externos obligatorios ni referencias a organizaciones. Las etapas replican el orden de una librería de templates CI personal (`validate`, `test`, `quality`, `security`, `build`, `image_security`, `sbom`) para que el modelo mental sea el mismo en GitLab y GitHub.

## Glosario

- **Pipeline:** workflow `.github/workflows/ci.yml`.
- **Etapa:** conjunto de jobs que corresponde a una fase del SDLC.
- **Gate de bloqueo:** job cuyo fallo impide el merge.
- **Hallazgo bloqueante:** vulnerabilidad, secreto o misconfiguración de severidad `CRITICAL`.

## Requisitos

### Requirement 1: Calidad y pruebas

**User Story:** Como desarrollador, quiero que cada push y pull request ejecute las verificaciones locales documentadas, para detectar regresiones antes del merge.

#### Acceptance Criteria

1. WHEN se abre un pull request o se hace push a `main`, THE Pipeline SHALL ejecutar `ruff check`, `ruff format --check` y `mypy src`.
2. WHEN se ejecuta la etapa de pruebas, THE Pipeline SHALL ejecutar `pytest` y una migración Alembic completa desde `0001_initial` sobre una base SQLite temporal.
3. IF alguna verificación falla, THEN THE Pipeline SHALL marcar el job como fallido.

### Requirement 2: Seguridad y vulnerabilidades

**User Story:** Como desarrollador, quiero detectar secretos, dependencias vulnerables y misconfiguraciones, para no integrar riesgos conocidos.

#### Acceptance Criteria

1. WHEN corre la etapa de seguridad, THE Pipeline SHALL ejecutar un escaneo de sistema de archivos con los escáneres `vuln`, `secret` y `misconfig`.
2. IF existe un hallazgo `CRITICAL`, THEN THE Pipeline SHALL fallar el job.
3. THE Pipeline SHALL reportar hallazgos `HIGH` sin bloquear.
4. THE Pipeline SHALL publicar el reporte JSON como artefacto.

### Requirement 3: Build, imagen y SBOM

**User Story:** Como desarrollador, quiero validar que la imagen Docker se construya y no tenga vulnerabilidades críticas, y obtener un SBOM, para tener evidencia de distribución.

#### Acceptance Criteria

1. WHEN se construye la imagen, THE Pipeline SHALL usar el `Dockerfile` existente sin publicar la imagen.
2. IF la imagen contiene hallazgos `CRITICAL`, THEN THE Pipeline SHALL fallar el job de seguridad de imagen.
3. THE Pipeline SHALL generar un SBOM CycloneDX y publicarlo como artefacto.

### Requirement 4: Mínimo privilegio y neutralidad

**User Story:** Como mantenedor, quiero un pipeline mínimo y neutral, para que el repositorio siga siendo ejecutable sin servicios externos ni información corporativa.

#### Acceptance Criteria

1. THE Pipeline SHALL declarar `permissions: contents: read` y no usar secretos para sus etapas obligatorias.
2. THE Pipeline SHALL fijar las versiones de las herramientas externas (Trivy y `uv`).
3. THE Pipeline MUST NOT referenciar organizaciones, hosts ni registros privados.
4. WHERE `SONAR_TOKEN`, `SONAR_ORGANIZATION` y `SONAR_PROJECT_KEY` estén configurados, THE Pipeline SHALL ejecutar SonarCloud y esperar el Quality Gate; en su ausencia SHALL omitir el análisis sin fallar.
5. WHEN se ejecuta `pytest` en CI, THE Pipeline SHALL generar `coverage.xml` y entregarlo a SonarCloud.
6. THE Pipeline MUST NOT escribir el token, la organización ni la clave del proyecto en el repositorio.

## Fuera de alcance

- DAST (`zap`) y Dependency-Track: este proyecto no expone un servicio web.
- Conexión con proveedores y ejecución automática de eventos SDLC: se especificará en un PR posterior.
- Publicación de imágenes y despliegues.
