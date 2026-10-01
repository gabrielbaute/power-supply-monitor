"""
Módulo de control de inyección de dependencias en la API
"""
from fastapi import Depends
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.settings import Settings, settings
from app.managers import DatabaseManager, db_manager
from app.services import (
    ElectricEventService,
    LogService,
    MailService,
    UserService
)

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
