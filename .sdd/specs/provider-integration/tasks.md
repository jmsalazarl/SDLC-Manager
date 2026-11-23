# Implementation Plan: Integración con proveedores

## Overview

Se implementará una integración vertical reutilizando el CLI, MCP, `SdlcEventProcessor`, `EvidenceEngine` e `IntegrationInstaller` existentes. La implementación debe comenzar por el proveedor con contrato de hooks más verificable y extenderse después a los demás sin incorporar SDKs externos al núcleo.

## Tasks

- [x] 1. Confirmar contratos y versiones soportadas
  - Registrar las versiones instaladas o marcar el proveedor como `NOT_TESTED` cuando no esté disponible.
  - Verificar contra documentación oficial el schema de entrada, salida, timeout y enforcement de cada superficie.
  - _Requerimiento: Requirement 2, Requirement 10_
  - _Capa: Integración / Docs_
  - _Depende de: ninguno_

- [ ] 2. Definir el contrato de eventos de CI
  - Definir campos normalizados para etapa, job, resultado, referencia y alcance.
  - Conservar `event_id`, aplicar límites y no guardar logs completos.
  - _Requerimiento: Requirement 1, Requirement 4, Requirement 8_
  - _Capa: Aplicación / CI_
  - _Depende de: 1_

- [x] 3. Implementar el adaptador vertical del proveedor inicial
  - Seleccionar hooks de proyecto de Codex con salida contextual documentada.
  - Traducir eventos al CLI y renderizar recomendaciones, `PASS`, `WARN`, `BLOCK`, errores y estados no verificables.
  - _Requerimiento: Requirement 1, Requirement 3, Requirement 6_
  - _Capa: Integración_
  - _Depende de: 1, 2_

- [ ] 4. Registrar evidencias automáticas como `PENDING`
  - Asociar evento, proyecto, HU, regla o gate y referencia de origen.
  - Rechazar cualquier transición automática a `VERIFIED`.
  - _Requerimiento: Requirement 5_
  - _Capa: Aplicación / Persistencia_
  - _Depende de: 2, 3_

- [ ] 5. Extender configuraciones de Kiro, Codex, OpenCode y Claude Code
  - Mantener MCP, instrucciones y recursos con namespace propio.
  - Implementar solamente eventos oficiales verificables y marcar las capacidades restantes.
  - _Requerimiento: Requirement 2, Requirement 3, Requirement 4, Requirement 9_
  - _Capa: Integración_
  - _Depende de: 3, 4_

- [ ] 6. Reforzar instalación, actualización, rollback y retiro selectivo
  - Probar plan, backup, merge, conflicto, escritura atómica e idempotencia en directorios temporales.
  - Preservar configuraciones ajenas y la base SQLite.
  - _Requerimiento: Requirement 7, Requirement 9_
  - _Capa: Infraestructura / Seguridad_
  - _Depende de: 5_

- [ ] 7. Implementar pruebas de propagación y compatibilidad
  - Comprobar que una recomendación llega al canal visible del proveedor.
  - Separar resultados `IMPLEMENTADO`, `PROBADO CON MOCK`, `VALIDADO EN CLIENTE REAL`, `PARTIAL`, `NOT_VERIFIED` y `UNSUPPORTED`.
  - _Requerimiento: Requirement 6, Requirement 10_
  - _Capa: QA_
  - _Depende de: 3, 5, 6_

- [ ] 8. Validar seguridad, persistencia y documentación
  - Ejecutar pruebas de payloads inválidos, rutas, secretos, concurrencia, reinicio y ausencia del proveedor.
  - Actualizar la matriz de compatibilidad y las instrucciones de instalación sin describir capacidades no comprobadas.
  - _Requerimiento: Requirement 8, Requirement 9, Requirement 10_
  - _Capa: QA / Docs / Seguridad_
  - _Depende de: 4, 6, 7_

## Notes

- Esta spec no autoriza cambios en motores de dominio ni en SDDNXP.
- No se ejecutan aprobaciones, transiciones ni cambios de archivos SDDNXP automáticamente.
- Las integraciones siguen siendo opcionales y no cargan experiencias, proyectos o evidencias ficticias.
- Los clientes no instalados se reportan como `NOT_TESTED`; los mocks no se presentan como validación real.
- Todo cambio de esquema requiere una migración Alembic aditiva y pruebas de actualización.

## Task Dependency Graph

```json
{
  "waves": [
    {"id": 0, "tasks": ["1"]},
    {"id": 1, "tasks": ["2"]},
    {"id": 2, "tasks": ["3", "4"]},
    {"id": 3, "tasks": ["5", "6"]},
    {"id": 4, "tasks": ["7"]},
    {"id": 5, "tasks": ["8"]}
  ]
}
```
