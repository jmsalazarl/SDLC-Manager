# Implementation Plan: CI con GitHub Actions

## Overview

Se agrega un workflow y la configuración de Dependabot. No se modifica código de `src/`, migraciones ni el contrato MCP.

## Tasks

- [x] 1. Definir la especificación
  - Crear requirements, design y tasks.
  - _Requerimiento: Requirement 1, Requirement 2, Requirement 3, Requirement 4_
  - _Capa: Docs_

- [x] 2. Crear el workflow `ci.yml`
  - Jobs `validate`, `test`, `quality`, `security`, `build`, `image_security`, `sbom`.
  - _Requerimiento: Requirement 1, Requirement 2, Requirement 3, Requirement 4_
  - _Capa: CI_
  - _Depende de: 1_

- [x] 3. Crear `dependabot.yml`
  - Ecosistemas `pip`, `docker` y `github-actions`, frecuencia semanal.
  - _Requerimiento: Requirement 2_
  - _Capa: CI_
  - _Depende de: 1_

- [x] 4. Documentar el pipeline
  - Agregar sección en `README.md` y `docs/ci.md`.
  - _Requerimiento: Requirement 4_
  - _Capa: Docs_
  - _Depende de: 2_

- [ ] 5. Validar
  - Validar sintaxis YAML; ejecutar `ruff` y `mypy` locales; registrar evidencia en `.sdd/audit/`.
  - _Requerimiento: Requirement 1_
  - _Capa: Validación_
  - _Depende de: 2, 3, 4_
