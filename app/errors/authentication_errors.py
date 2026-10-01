from app.errors.base_error import GeneralError

class AuthenticationError(GeneralError):
    """Error lanzado cuando hay un problema con la autenticación de una sesión."""
    def __init__(self, message: str = "Authentication operation error", details=None):
        super().__init__(message, details)
