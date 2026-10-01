from uuid import UUID
from datetime import datetime, UTC
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr

from app.enums import UserRole, UserStatus

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password_hash: str
    role: UserRole
    status: UserStatus

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: Optional[datetime] = None
    role: UserRole
    status: UserStatus

    model_config = ConfigDict(from_attributes=True)

class UserListResponse(BaseModel):
    users: List[UserResponse] = []
    count: int = 0

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    updated_at: datetime = datetime.now(UTC)

    model_config = ConfigDict(from_attributes=True)

class UserPasswordHash(BaseModel):
    """
    Esquema para el hash de la contraseña del usuario.

    Args:
        user_id (UUID): ID del usuario.
        password_hash (str): Hash de la contraseña.
    """
    user_id: UUID
    password_hash: str

    model_config = ConfigDict(from_attributes=True)
