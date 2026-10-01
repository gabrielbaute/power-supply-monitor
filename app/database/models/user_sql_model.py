from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, UTC
from sqlmodel import SQLModel, Field

from app.enums import UserRole, UserStatus

class UserSQLModel(SQLModel, table=True):
    """
    Modelo de persistencia de datos de usuario.

    Attributes:
        id (UUID): ID o primary key del registro de usuario.
        username (str): Nombre de usuario.
        email (str): Correo del usuario (debe ser único)
        password_hash (str): Hash de la contraseña de usuario.
        created_at (datetime): Marca de tiempo de creación de la cuenta.
        updated_at (datetime): Marca de tiempo de la última actualización de la cuenta.
        role (UserRole): Rol del usuario
        status (UserStatus): Status del usuario.
    """
    __tablename__ = "users" # type: ignore

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(nullable=False, index=True)
    email: str = Field(nullable=False, index=True, unique=True)
    password_hash: str = Field(nullable=False, max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
    role: UserRole = Field(default=UserRole.USER, index=True)
    status: UserStatus = Field(default=UserStatus.INACTIVE, index=True)
