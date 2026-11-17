from __future__ import annotations

from typing import Any, Protocol


class SddnxpContextReader(Protocol):
    """Contrato de lectura opcional para enriquecer un evento procesado."""

    def read(self) -> dict[str, Any] | None:
        """Devuelve metadatos locales sin cambiar el estado externo."""
