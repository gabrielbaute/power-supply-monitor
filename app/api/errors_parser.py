"""
Módulo handler para traducir errores y excepciones del backend a respuestas HTTP.
"""
import logging
from typing import Any, Dict, Type

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.errors import (
    DatabaseOperationError,
    DatabaseSessionError,
    GeneralError,
    RegisterNotFoundError,
)


class ErrorHandlerRegistry:
    """
    Clase encargada de registrar y gestionar los manejadores de excepciones de la API.
    """
    def __init__(self) -> None:
        """
        Inicializa el registro de errores, el logger y el mapeo de excepciones.
        """
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._error_mapping: Dict[Type[GeneralError], int] = {
            RegisterNotFoundError: status.HTTP_404_NOT_FOUND,
            DatabaseSessionError: status.HTTP_500_INTERNAL_SERVER_ERROR,
            DatabaseOperationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        }

    def get_status_code(self, exception_type: Type[GeneralError]) -> int:
        """
        Obtiene el código de estado HTTP correspondiente al tipo de excepción.

        Args:
            exception_type (Type[GeneralError]): Clase de la excepción lanzada.

        Returns:
            int: Código de estado HTTP correspondiente o 400 Bad Request por
            defecto.
        """
        return self._error_mapping.get(exception_type, status.HTTP_400_BAD_REQUEST)

    async def handle_general_error(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Mapea los errores dominiales del backend a respuestas HTTP estructuradas.

        Args:
            request (Request): Objeto de la petición HTTP entrante.
            exc (Exception): Excepción capturada (instancia de GeneralError).

        Returns:
            JSONResponse: Respuesta estructurada con el código de error y
              detalles.
        """
        if not isinstance(exc, GeneralError):
            return await self.handle_unhandled_exception(request, exc)

        http_status = self.get_status_code(type(exc))
        details_content: Dict[str, Any] = exc.details or {}

        return JSONResponse(
            status_code=http_status,
            content={
                "status": "error",
                "code": exc.__class__.__name__,
                "message": exc.message,
                "details": jsonable_encoder(details_content),
            },
        )

    async def handle_unhandled_exception(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Captura cualquier error no controlado para evitar fuga de información.

        Args:
            request (Request): Objeto de la petición HTTP entrante.
            exc (Exception): Excepción genérica no capturada.

        Returns:
            JSONResponse: Respuesta HTTP 500 estándar.
        """
        self.logger.error("Unhandled error: %s", exc, exc_info=exc)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "code": "InternalServerError",
                "message": "An unexpected error has occurred on the server.",
            },
        )

    def register(self, app: FastAPI) -> None:
        """
        Registra los métodos de la clase como manejadores de excepciones en FastAPI.

        Args:
            app (FastAPI): Instancia de la aplicación FastAPI.
        """
        app.add_exception_handler(GeneralError, self.handle_general_error)
        app.add_exception_handler(Exception, self.handle_unhandled_exception)


def register_error_handlers(app: FastAPI) -> None:
    """
    Función de entrada para instanciar el registro y configurar los handlers en la API.

    Args:
        app (FastAPI): Instancia de la aplicación FastAPI.
    """
    registry = ErrorHandlerRegistry()
    registry.register(app)
