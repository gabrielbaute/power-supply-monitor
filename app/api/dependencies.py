"""
Módulo de control de inyección de dependencias en la API
"""
from typing import AsyncGenerator, Optional
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, Header, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole, UserStatus
from app.errors import AuthenticationError, PermissionDeniedError
from app.errors.user_errors import ResourceNotFoundError
from app.managers import DatabaseManager, db_manager
from app.settings import Settings, settings
from app.services import (
    ElectricEventService,
    LogService,
    MailService,
    SecurityService,
    UserService
)
from app.schemas import UserResponse, TokenData

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# ============ Proveedores de Servicios ============

def get_settings_instance() -> Settings:
    """
    Devuelve la instancia singleton de la configuración de la app.
    """
    return settings

def get_db_manager() -> DatabaseManager:
    """
    Devuelve la instancia singleton del administrador de sesión de la base de datos.
    """
    return db_manager

async def get_db_session(
    db_manager: DatabaseManager = Depends(get_db_manager)
) -> AsyncGenerator[AsyncSession]:
    """
    Generar y gestionar el ciclo de vida de una sesión de base de datos transaccional aislada.
    """
    async for session in db_manager.get_session():
        yield session

def get_electric_event_service(
    database_session: AsyncSession = Depends(get_db_session)
) -> ElectricEventService:
    """
    Inyecta una instancia de ElectricEventService en la API
    """
    return ElectricEventService(database_session=database_session)

def get_log_service(
    settings_instance: Settings = Depends(get_settings_instance)
) -> LogService:
    """
    Inyecta una instancia del servicio LogService en la API.

    Args:
        settings_instance (Settings): Instancia global de configuración.

    Returns:
        LogService: Servicio de gestión e inspección de logs.
    """
    return LogService(settings=settings_instance)

def get_mail_service(
    settings_instance: Settings = Depends(get_settings_instance)
) -> MailService:
    """
    Inyecta una instancia del servicio MailService en la API.

    Args:
        settings_instance (Settings): Instancia global de configuración.

    Returns:
        MailService: Servicio de gestión de correo electrónico.
    """
    return MailService(settings=settings_instance)

def get_user_iservice(
    database_session: AsyncSession = Depends(get_db_session),
    mail_service: MailService = Depends(get_mail_service),
    settings_instance: Settings = Depends(get_settings_instance),
) -> UserService:
    """
    Inyecta una instancia del servicio UserService en la API.

    Args:
        database_session
        mail_service
        settings_instance (Settings): Instancia global de configuración.

    Returns:
        UserService: Servicio de gestión de usuarios.
    """
    return UserService(database_session=database_session, mail_service=mail_service, settings=settings_instance)

# ============ Dependencias de Seguridad y Usuario ============

async def get_current_user(
    token_header: Optional[str] = Depends(oauth2_scheme),
    token_query: Optional[str] = Query(None, alias="token"),
    user_service: UserService = Depends(get_user_iservice)
) -> Optional[UserResponse]:
    """
    Valida el token JWT (extraído de Header o Query Param) y retorna el usuario actual.

    Esta implementación permite que recursos multimedia (como <img>) puedan
    autenticarse pasando el token en la URL, manteniendo la compatibilidad
    con el estándar OAuth2 para el resto de la API.

    Args:
        token_header (Optional[str]): Token extraído del header Authorization.
        token_query (Optional[str]): Token extraído del parámetro de consulta 'token'.
        user_service (UserService): Servicio para la gestión de la entidad de usuario.

    Returns:
        UserResponse: Objeto del usuario autenticado y activo.

    Raises:
        AuthenticationError: Si el usuario no está activado.
        ResourceNotFoundError: Si el usuario no se encuentra.
    """
    # 1. Priorizar el header, pero caer al query param si es necesario
    token = token_header or token_query

    if not token:
        raise AuthenticationError(
            message="No se proporcionaron credenciales de autenticación",
        )

    try:
        # 2. Decodificar el token usando el SecurityService
        security_service = SecurityService()
        token_data: TokenData = security_service.decode_token(
            token,
            expected_scope="access"
        )

        # 3. Recuperar usuario desde la base de datos
        user = await user_service.controller.get_user_by_id(token_data.user_id) #type: ignore

        if user is None:
            raise ResourceNotFoundError(
                message="Credenciales no válidas o usuario inexistente",
            )

        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError(
                message="La cuenta de usuario está desactivada",
            )

        return user

    except Exception as e:
        raise AuthenticationError(
            message="Error de autenticación.",
            details={"detail": str(e)},
        ) from e

def get_current_admin(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Asegura que el usuario tenga privilegios de administrador.

    Args:
        current_user (UserResponse): Usuario actual.

    Returns:
        UserResponse: Usuario actual.

    Raises:
        HTTPException: Si el usuario no tiene privilegios de administrador.
    """
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedError(
            message="Operación restringida, permisos insuficientes."
        )
    return current_user
