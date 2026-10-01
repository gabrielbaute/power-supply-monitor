"""
Módulo para la inicialización y semillado de datos del usuario administrador.
Este módulo define la clase `UserBootstrapManager`, encargada de verificar
y crear el usuario administrador por defecto si no existe en la base de datos.
"""

import logging
from typing import Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.settings.app_settings import Settings
from app.enums import UserRole, UserStatus
from app.database.models import UserSQLModel
from app.services.security_service import SecurityService

class UserBootstrapManager:
    """Gestor encargado de sembrar datos iniciales de usuarios en la base de datos."""
    def __init__(
        self, security_service: SecurityService, app_settings: Settings
    ) -> None:
        """
        Inicializa el gestor de semillado de usuarios.

        Args:
            security_service (SecurityService): Servicio para el hashing de contraseñas.
            app_settings (Settings): Instancia de configuración de la aplicación.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.security_service: SecurityService = security_service
        self.settings: Settings = app_settings

    async def create_initial_admin(self, session: AsyncSession) -> None:
        """
        Crea el usuario administrador por defecto de forma asíncrona si no existe.

        Args:
            session (AsyncSession): Sesión asíncrona activa de SQLAlchemy/SQLModel.
        """
        statement = select(UserSQLModel).where(
            UserSQLModel.username == self.settings.ADMIN_USERNAME
        )

        # Uso de .execute() compatible con AsyncSession de SQLAlchemy
        result = await session.execute(statement)
        existing_admin: Optional[UserSQLModel] = result.scalars().first()

        if existing_admin is not None:
            self.logger.info("El usuario administrador ya existe. Se omite la creación.")
            return

        hashed_pwd: str = self.security_service.get_password_hash(
            self.settings.ADMIN_PASSWORD
        )

        admin_user = UserSQLModel(
            username=self.settings.ADMIN_USERNAME,
            email=self.settings.ADMIN_EMAIL,
            password_hash=hashed_pwd,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )

        session.add(admin_user)
        await session.commit()
        self.logger.info(
            f"Usuario administrador '{self.settings.ADMIN_USERNAME}' creado exitosamente."
        )
