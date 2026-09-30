from app.errors.base_error import GeneralError

class SMTPConnectionError(GeneralError):
    """Error lanzado cuando no es posible conectarse con el servidor SMTP remoto."""
    def __init__(self, message: str = "Error al conectar al servidor SMTP", details=None):
        super().__init__(message, details)

class SendMailError(GeneralError):
    """Error lanzado cuando no es posible enviar un mensaje de correo electrónico."""
    def __init__(self, message: str = "Error al enviar el correo electrónico.", details=None):
        super().__init__(message, details)

class TemplateMailNotFound(GeneralError):
    """Error lanzado cuando no se logra cargar la plabtilla de email solicitada."""
    def __init__(self, message: str = "Plantilla de Email no encontrada.", details=None):
        super().__init__(message, details)

class BuildMessageError(GeneralError):
     """Error lanzado cuando falla el builder de email."""
     def __init__(self, message: str = "Error al construir el mensaje en Jinja", details=None):
        super().__init__(message, details)
