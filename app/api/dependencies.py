"""
Módulo de control de inyección de dependencias en la API
"""
from fastapi import Depends
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.settings import Settings, settings
from app.managers import DatabaseManager, db_manager
from app.services import ElectricEventService

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
