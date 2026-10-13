from uuid import UUID
from datetime import datetime, UTC
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enums import UserRole, UserStatus


class UserRegisterRequest(BaseModel):
    """
    Modelo de solicitud de registro de un nuevo usuario.

    Attributes:
        username (str): Nombre de usuario único en el sistema.
        email (EmailStr): Correo electrónico del usuario.
        password (str): Contraseña en texto plano (será hasheada en el backend).
    """
    username: str
    email: EmailStr
    password: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "username": "jdoe",
                    "email": "jdoe@example.com",
                    "password": "S3cur3P@ssw0rd!"
                }
            ]
        }
    )


class UserCreate(BaseModel):
    """
    Modelo de creación de un usuario a nivel de persistencia.

    Attributes:
        username (str): Nombre de usuario único en el sistema.
        email (EmailStr): Correo electrónico del usuario.
        password_hash (str): Hash de la contraseña del usuario.
        status (UserStatus): Estado actual del usuario (activo, inactivo, etc.).
        role (UserRole): Rol asignado al usuario dentro del sistema.
    """
    username: str
    email: EmailStr
    password_hash: str
    status: UserStatus
    role: UserRole

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "username": "jdoe",
                    "email": "jdoe@example.com",
                    "password_hash": "$2b$12$abcdefghijklmnopqrstuv...",
                    "status": "ACTIVE",
                    "role": "USER"
                }
            ]
        }
    )


class UserResponse(BaseModel):
    """
    Modelo de respuesta con la información pública de un usuario.

    Attributes:
        id (UUID): Identificador único del usuario.
        username (str): Nombre de usuario único en el sistema.
        email (EmailStr): Correo electrónico del usuario.
        created_at (datetime): Fecha y hora de creación del registro.
        updated_at (Optional[datetime]): Fecha y hora de la última actualización.
        role (UserRole): Rol asignado al usuario dentro del sistema.
        status (UserStatus): Estado actual del usuario.
    """
    id: UUID
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: Optional[datetime] = None
    role: UserRole
    status: UserStatus

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                    "username": "jdoe",
                    "email": "jdoe@example.com",
                    "created_at": "2026-10-01T07:43:14.890702",
                    "updated_at": "2026-10-02T09:00:00.000000",
                    "role": "USER",
                    "status": "ACTIVE"
                }
            ]
        }
    )


class UserListResponse(BaseModel):
    """
    Respuesta de lista de varios usuarios. Para consultas masivas en la base de datos.

    Attributes:
        users (List[UserResponse]): Lista de objetos UserResponse.
        count (int): Total de usuarios traídos desde la base de datos.
    """
    users: List[UserResponse] = []
    count: int = 0

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "users": [
                        {
                            "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                            "username": "jdoe",
                            "email": "jdoe@example.com",
                            "created_at": "2026-10-01T07:43:14.890702",
                            "updated_at": "2026-10-02T09:00:00.000000",
                            "role": "USER",
                            "status": "ACTIVE"
                        },
                        {
                            "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                            "username": "asmith",
                            "email": "asmith@example.com",
                            "created_at": "2026-10-02T09:43:14.890702",
                            "updated_at": None,
                            "role": "ADMIN",
                            "status": "INACTIVE"
                        }
                    ],
                    "count": 2
                }
            ]
        }
    )


class UserUpdate(BaseModel):
    """
    Modelo de edición de un usuario existente.

    Attributes:
        username (Optional[str]): Nuevo nombre de usuario único en el sistema.
        email (Optional[EmailStr]): Nuevo correo electrónico del usuario.
        role (Optional[UserRole]): Nuevo rol asignado al usuario.
        status (Optional[UserStatus]): Nuevo estado del usuario.
        updated_at (datetime): Marca de tiempo de la última actualización
            (por defecto, el momento actual en UTC).
    """
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "username": "jdoe_updated",
                    "email": "jdoe_new@example.com",
                    "role": "ADMIN",
                    "status": "ACTIVE",
                    "updated_at": "2026-10-02T09:00:00.000000"
                }
            ]
        }
    )


class UserPasswordHash(BaseModel):
    """
    Esquema para el hash de la contraseña del usuario.

    Attributes:
        user_id (UUID): ID del usuario.
        password_hash (str): Hash de la contraseña.
    """
    user_id: UUID
    password_hash: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                    "password_hash": "$2b$12$abcdefghijklmnopqrstuv..."
                }
            ]
        }
    )
