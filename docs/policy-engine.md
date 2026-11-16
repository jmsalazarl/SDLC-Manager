# Motor de políticas

## Esquema YAML

Cada archivo declara una regla independiente:

```yaml
id: DEMO-001
name: Compatibilidad de artefactos
description: Exige evidencias antes del cierre tecnico.
version: "1.0.0"
severity: CRITICAL
trigger:
  event: file_change
  file_extensions: [.artifact]
scope: {}
conditions: {}
required_evidence: [baseline_reference, comparison_result]
target_gate: task_completion
action: block
approval_status: approved
enabled: true
```

Los campos desconocidos son rechazados. Los estados válidos son `draft`, `approved` y `rejected`; solamente una regla `enabled` y `approved` puede bloquear.

## Operadores permitidos

- `equals`: compara valores y tipos estrictamente.
- `not_equals`: niega la comparación estricta.
- `contains`: busca en texto o lista.
- `in`: valida pertenencia a una lista declarada.
- `exists`: comprueba presencia o ausencia de un valor.
- `file_extension_matches`: compara extensiones de una lista de archivos.
- `all` y `any`: agrupan condiciones anidadas.

No se interpretan expresiones de texto libre. El motor no usa `eval`, `exec` ni importaciones dinámicas.

## Aplicabilidad

`trigger` filtra por evento, etapa, extensión y componente. `conditions` evalúa un contexto normalizado por el caso de uso. Si una condición tiene estructura desconocida, se genera un error identificable y no se produce una decisión silenciosa.

## Decisiones

| Acción | Resultado |
| --- | --- |
| `block` aprobada con condición incumplida o evidencia faltante | `BLOCK` |
| `warn` o `recommend` aplicable | `WARN` |
| Ninguna infracción aplicable | `PASS` |

La prioridad es `BLOCK` sobre `WARN` sobre `PASS`. Una regla `block` aprobada con todas sus evidencias verificadas permite `PASS`.

## Evidencias

Las evidencias nuevas se crean como `PENDING`. Solo `VERIFIED` cuenta para satisfacer `required_evidence`. `verify_evidence` registra el identificador del aprobador y la fecha; un rechazo no satisface el requisito.

## Versionado y errores

Las reglas se versionan en Git junto con el paquete de conocimiento. Un YAML inválido detiene la carga del paquete y expone la ruta y el error de validación, sin ejecutar reglas parciales. Las políticas de demostración son ficticias y se ubican en `knowledge/rules/`.

