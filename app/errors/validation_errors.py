from typing import Any, Dict, Optional
from app.errors.base_error import GeneralError

class TimezoneRequiredError(GeneralError):
    """Error lanzado cuando una fecha/hora carece de información de zona horaria (offset UTC)."""

    def __init__(
        self,
        message: str = "Las fechas deben incluir información de zona horaria (ej. 'Z' o '-04:00').",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Inicializa la excepción de zona horaria requerida.

        Args:
            message (str): Mensaje descriptivo del error.
            details (Optional[Dict[str, Any]]): Metadatos adicionales sobre el campo inválido.
        """
        super().__init__(message, details)
