"""
Módulo de rutas para la gestión de usuarios (Autogestión)).
"""
from typing import Optional
from fastapi import APIRouter, Depends, status

from app.services import UserService, SecurityService
from app.errors import ResourceNotFoundError, PermissionDeniedError, GeneralError
from app.schemas import UserResponse, UserUpdate, PasswordChange, UserPasswordHash
from app.api.dependencies import get_current_user, get_user_service

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: UserResponse = Depends(get_current_user)):
    """Retorna el perfil del usuario autenticado."""
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Actualiza datos básicos del perfil (email, username)."""
    updated_user = await user_service.controller.update_user(current_user.id, user_update)
    return updated_user

@router.post("/me/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    data: PasswordChange,
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> dict[str, str]:
    """Cambia la contraseña del usuario validando la anterior."""
     # 1. Verificar la contraseña actual
    user_db: Optional[UserPasswordHash] = await user_service.controller.get_user_password_hash(current_user.id)
    if not user_db:
        raise ResourceNotFoundError(
            message="Usuario no encontrado."
        )
    security = SecurityService()
    if not security.verify_password(data.current_password, user_db.password_hash):
        raise PermissionDeniedError(message="La contraseña actual es incorrecta")

    # 2. Actualizar a la nueva
    new_hash = security.get_password_hash(data.new_password)
    success = await user_service.update_user_password(
        user_id=current_user.id,
        hashed_password=new_hash
    )
    if not success:
        raise GeneralError(message="No se pudo actualizar la contraseña")

    return {"message": "Contraseña actualizada exitosamente"}
