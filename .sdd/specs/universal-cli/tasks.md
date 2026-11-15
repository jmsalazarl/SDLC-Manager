# Implementation Plan: Universal CLI

## Overview

Implementar una interfaz CLI universal sobre el procesador existente, conservar el inicio MCP sin argumentos, agregar códigos de salida estables, probar entradas y procesos separados, y documentar ejecución nativa y Docker.

## Tasks

- [x] 1. Implementar la frontera CLI.
  - [x] 1.1 Crear `cli.py` con `argparse`, lectura limitada de stdin y salida JSON.
  - [x] 1.2 Definir códigos de salida para información, PASS, WARN, BLOCK, rechazo y errores técnicos.
  - [x] 1.3 Mantener el inicio MCP cuando no se proporcionan argumentos.
  - _Requerimientos: Requirement 1, Requirement 2, Requirement 4_
  - _Capa: Application / Interface_
  - _Depende de: SPEC-004_

- [x] 2. Integrar bootstrap y persistencia.
  - [x] 2.1 Reutilizar `run_migrations` y `build_container` sin reinicializar la base.
  - [x] 2.2 Verificar persistencia, duplicados y conflictos entre procesos separados.
  - [x] 2.3 Validar permisos y ejecución dentro de Docker.
  - _Requerimientos: Requirement 3, Requirement 5_
  - _Capa: Infrastructure / Interface_
  - _Depende de: 1_

- [x] 3. Crear pruebas de CLI y compatibilidad.
  - [x] 3.1 Probar PASS, WARN, BLOCK e información.
  - [x] 3.2 Probar JSON inválido, UUID inválido, tamaño y errores técnicos.
  - [x] 3.3 Probar stdout JSON limpio y logs en stderr.
  - [x] 3.4 Probar MCP anterior y CLI en Docker.
  - _Requerimientos: Requirement 2, Requirement 3, Requirement 6_
  - _Capa: QA_
  - _Depende de: 1, 2_

- [x] 4. Documentar y validar.
  - [x] 4.1 Crear `docs/universal-cli-validation.md` con comandos y resultados reales.
  - [x] 4.2 Actualizar README, documentación Docker y trazabilidad.
  - [x] 4.3 Ejecutar pytest, Ruff, mypy, Alembic, Docker y `sddnxp validate`.
  - _Requerimientos: Todos_
  - _Capa: Docs / QA_
  - _Depende de: 3_

## Notes

- No implementar Hooks ni adaptadores específicos de clientes.
- No agregar servidores, brokers ni dependencias externas.
- No modificar contratos MCP existentes.
- No tratar `decision: null` como PASS.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2"] },
    { "id": 2, "tasks": ["3"] },
    { "id": 3, "tasks": ["4"] }
  ]
}
```
