# CI con GitHub Actions

El workflow `.github/workflows/ci.yml` valida cada pull request y cada push a `main`. No usa secretos ni servicios externos.

| Job | Etapa | Qué ejecuta | Bloquea |
|-----|-------|-------------|---------|
| `validate` | validate | `ruff check`, `ruff format --check` | Sí |
| `test` | test | `pytest` con cobertura y migraciones Alembic desde `0001` | Sí |
| `quality` | quality | `mypy src` | Sí |
| `sonar` | quality | SonarCloud y su Quality Gate | Sí, si está configurado |
| `security` | security | Trivy `fs` (`vuln`, `secret`, `misconfig`) | Sí, si hay `CRITICAL` |
| `build` | build | `docker build` sin publicar | Sí |
| `image_security` | image_security | Trivy `image` sobre la imagen construida | Sí, si hay `CRITICAL` |
| `sbom` | sbom | SBOM CycloneDX como artefacto | No |

Los hallazgos `HIGH` se reportan y no bloquean. Los reportes JSON y el SBOM quedan como artefactos durante 7 días.

Para reproducir localmente las verificaciones de calidad:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest --cov --cov-report=xml
```

Dependabot revisa semanalmente `pip`, `docker` y `github-actions`.

## Configurar SonarCloud

El job `sonar` se omite hasta que existan estos valores en GitHub (Settings, Secrets and variables, Actions):

| Tipo | Nombre | Valor |
|------|--------|-------|
| Secret | `SONAR_TOKEN` | Token generado en SonarCloud |
| Variable | `SONAR_ORGANIZATION` | Clave de la organización en SonarCloud |
| Variable | `SONAR_PROJECT_KEY` | Clave del proyecto en SonarCloud |

Para exigirlo en `main`, agregue los checks `sonar` y `validate` como requeridos en la protección de rama. La cobertura se genera en `test` (`coverage.xml`) y `sonar` la consume.
