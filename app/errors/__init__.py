from app.errors.authentication_errors import AuthenticationError
from app.errors.base_error import GeneralError
from app.errors.database_errors import (
    DatabaseOperationError,
    DatabaseSessionError,
    RegisterNotFoundError
)
from app.errors.mail_errors import (
    BuildMessageError,
    SMTPConnectionError,
    SendMailError,
    TemplateMailNotFound
)
from app.errors.user_errors import (
    PermissionDeniedError,
    ResourceNotFoundError,
    ValidationError
)
from app.errors.validation_errors import TimezoneRequiredError
