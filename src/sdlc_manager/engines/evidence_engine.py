from __future__ import annotations

from pathlib import PurePosixPath


class EvidenceValidationError(ValueError):
    """Indica una referencia de evidencia no permitida."""


def validate_evidence_reference(reference: str) -> str:
    value = reference.strip()
    if not value or len(value) > 500:
        raise EvidenceValidationError("La referencia de evidencia no es valida")
    path = PurePosixPath(value)
    if value.startswith(("/", "\\")) or ".." in path.parts:
        raise EvidenceValidationError("No se permiten rutas locales arbitrarias")
    return value
