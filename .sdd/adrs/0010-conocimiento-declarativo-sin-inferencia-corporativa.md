# ADR 0010: Conocimiento Declarativo Sin Inferencia Corporativa

## Estado

Aceptada

## Contexto

El núcleo contenía una inferencia basada en una extensión de archivo específica.
Esto mezclaba conocimiento organizacional con el servicio de aplicación y hacía
que el repositorio distribuible revelara un formato interno.

## Decisión

El servicio solo inferirá `file_change` cuando existan archivos modificados y
no se haya proporcionado un evento. Las extensiones, componentes y evidencias
son responsabilidad exclusiva de los paquetes YAML activos. Los ejemplos del
repositorio usan nombres ficticios y genéricos.

## Consecuencias

- El núcleo puede distribuirse sin conocimiento de una organización.
- Los paquetes de conocimiento siguen siendo extensibles sin modificar Python.
- Los adaptadores deben enviar el evento cuando el contexto sea relevante.
- Las pruebas conservan cobertura de triggers declarativos con datos ficticios.
