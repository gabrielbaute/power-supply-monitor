from typing import Any, Dict, Optional
from app.errors.base_error import GeneralError

class NTFYNotificationError(GeneralError):
    """Error lanzado cuando falla el envío de una notificación al servidor NTFY."""
    def __init__(
        self,
        message: str = "No se pudo emitir la notificación hacia el servidor NTFY.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Inicializa la excepción de fallo en el servicio NTFY.

        Args:
            message (str): Mensaje descriptivo del error.
            details (Optional[Dict[str, Any]]): Metadatos adicionales del fallo.
        """
        super().__init__(message, details)
