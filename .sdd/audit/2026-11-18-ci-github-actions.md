# Evidencia de validación de CI con GitHub Actions

## Alcance

Esta evidencia cierra la tarea 5 de SPEC-009 y registra las validaciones locales y remotas disponibles para el workflow de integración continua.

## Evidencia remota

| Evidencia | Resultado | Fuente |
|---|---|---|
| PR #1, creación del pipeline | Fusionado el 2026-11-17; commit `95117464dd717907c0373fd9daec8e4493601dd0` | [PR #1](https://github.com/jmsalazarl/SDLC-Manager/pull/1) |
| PR #13, actualización de Trivy | Fusionado el 2026-11-18; commit `1c1bf6a77b8b46f17b07a84649a0749a7252f994` | [PR #13](https://github.com/jmsalazarl/SDLC-Manager/pull/13) |
| Ejecución CI sobre `main` | Ocho jobs completados correctamente: `validate`, `test`, `quality`, `security`, `sonar`, `build`, `image_security` y `sbom` | [Ejecución CI](https://github.com/jmsalazarl/SDLC-Manager/actions/runs/44329961923) |
| Quality Gate | `OK` en la rama `main`; todas las condiciones reportadas están en estado `OK` | [Quality Gate de SonarCloud](https://sonarcloud.io/project/overview?id=jorge-salazar-github_sdlc-manager) |
| Trivy | Cero hallazgos bloqueantes en los jobs de filesystem e imagen de la ejecución de `main` | Jobs `security` e `image_security` de la [ejecución CI](https://github.com/jmsalazarl/SDLC-Manager/actions/runs/44329961923) |

La API pública de GitHub confirmó que los artefactos `trivy-fs` y `trivy-image` fueron generados y que ambos jobs finalizaron correctamente. El detalle JSON de los artefactos requiere autenticación y no se incluyó en este repositorio.

## Validación local

Las siguientes validaciones se ejecutaron con `uv 0.13.7`, Python 3.12 y el entorno aislado configurado para esta comprobación:

```text
uv sync --frozen --no-build                 PASS
uv run --frozen --no-build ruff check .    PASS
uv run --frozen --no-build ruff format --check . PASS
uv run --frozen --no-build mypy src        PASS
uv run --frozen --no-build pytest          73 passed, 1 skipped
YAML de .github/workflows/ci.yml           PASS
git diff --check                            PASS
```

La prueba omitida corresponde a la prueba Docker que solo se habilita con `SDLC_MANAGER_RUN_DOCKER_TESTS=1`. No se ejecutó `alembic upgrade` localmente porque `alembic.ini` apunta a la base de datos física del desarrollador.

## Trazabilidad

- Requisitos: `.sdd/specs/ci-github-actions/requirements.md`.
- Diseño: `.sdd/specs/ci-github-actions/design.md`.
- Tareas: `.sdd/specs/ci-github-actions/tasks.md`.
- Implementación: `.github/workflows/ci.yml` y `.github/dependabot.yml`.
- Documentación: `docs/ci.md`.
