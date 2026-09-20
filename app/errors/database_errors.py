from app.errors.base_error import GeneralError

class DatabaseOperationError(GeneralError):
    """Error lanzado cuando hay un problema con una operación de la base de datos."""
    def __init__(self, message: str = "Database operation error", details=None):
        super().__init__(message, details)

class DatabaseSessionError(GeneralError):
    """Error lanzado cuando hay un problema con la sesión de la base de datos."""
    def __init__(self, message: str = "Database session error", details=None):
        super().__init__(message, details)

class RegisterNotFoundError(GeneralError):
    """Error lanzado cuando no se encuentra un registro en la base de datos."""
    def __init__(self, message: str = "Register not found", details=None):
        super().__init__(message, details)
