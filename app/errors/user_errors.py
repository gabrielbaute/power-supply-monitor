from app.errors.base_error import GeneralError

class ResourceNotFoundError(GeneralError):
    """Error lanzado cuando un recurso del usuario no se encuentra o no está disponible."""
    def __init__(self, message: str = "Recurso o usuario no encontrado", details=None):
        super().__init__(message, details)

class ValidationError(GeneralError):
    """Error lanzado cuando no es posible validar los datos del usuario o las reglas de negocio."""
    def __init__(self, message: str = "No se pudieron validar los requerimientos o datos.", details=None):
        super().__init__(message, details)

class PermissionDeniedError(GeneralError):
    """Error lanzado cuando un usuario no tiene permisos para realizar una acción."""
    def __init__(self, message: str = "El usuario no tiene privilegios suficientes para esta acción.", details=None):
        super().__init__(message, details)
