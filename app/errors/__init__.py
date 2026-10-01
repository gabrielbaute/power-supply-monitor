from app.errors.base_error import GeneralError
from app.errors.authentication_errors import AuthenticationError
from app.errors.database_errors import (
    DatabaseOperationError,
    DatabaseSessionError,
    RegisterNotFoundError
)
from app.errors.mail_errors import (
    SMTPConnectionError,
    SendMailError,
    TemplateMailNotFound,
    BuildMessageError
)
