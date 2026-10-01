"""
Módulo de rutas de autenticación de la API.
"""
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, status, Depends

from app.enums import UserStatus
from app.api.dependencies import get_mail_service, get_user_service
from app.services import SecurityService, UserService, MailService
from app.schemas.auth_schemas import Token, PasswordResetConfirm, UserLogin
from app.schemas.user_schemas import UserCreate, UserResponse, UserRegisterRequest

from app.errors import ResourceNotFoundError, PermissionDeniedError, ValidationError, GeneralError

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    """
    Endpoint estándar de OAuth2 para obtener un token de acceso.
    """
    login_credentials = UserLogin(
        email=form_data.username,
        password=form_data.password
    )

    # El servicio ya maneja la lógica de hash y verificación
    user: Optional[UserResponse] = await user_service.authenticate_user(login_credentials)

    # Generamos el token de acceso
    security = SecurityService()
    access_token = security.create_access_token(
        data={"sub": str(user.id), "scope": "access"} #type: ignore
    )

    return {
        "access_token": access_token.access_token,
        "token_type": "bearer"
    }

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegisterRequest,
    user_service: UserService = Depends(get_user_service)
) -> Optional[UserResponse]:
    """
    Registro público de nuevos usuarios.
    Se encarga de crear el registro en DB y la estructura de carpetas física.
    """
    return await user_service.register_user(user_data=user_data)

@router.post("/password-recovery", status_code=status.HTTP_200_OK)
async def request_recovery(
    email: str,
    user_service: UserService = Depends(get_user_service),
    mail_service: MailService = Depends(get_mail_service)
):
    """
    Solicita un link de recuperación. No revela si el email existe por seguridad.
    """
    try:
        recovery_data = await user_service.generate_password_recovery_data(email=email)
        await mail_service.send_templated_email(
            recipient=email,
            subject="Recuperacion de contraseña",
            template="emails/recover_password.html",
            context=recovery_data
        )
    except ResourceNotFoundError:
        # No hacemos nada, devolvemos 200 para evitar enumeración de usuarios
        pass
    except Exception as e:
        raise GeneralError(
            message="Error al enviar el mensaje de recuperacion.",
            details={"detail": str(e)}
        ) from e

    return {"message": "Si el email está registrado, recibirás un enlace de recuperación."}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    data: PasswordResetConfirm,
    user_service: UserService = Depends(get_user_service)
) -> dict[str, str]:
    """
    Cambia la contraseña usando un token de scope 'password_reset'.
    """
    security = SecurityService()
    # 1. Validamos el token específico para reset
    token_data = security.decode_token(data.token, expected_scope="password_reset")

    # 2. Hasheamos la nueva password
    hashed_password = security.get_password_hash(data.new_password)

    # 3. Actualizamos
    await user_service.update_user_password(
        user_id=token_data.user_id, #type: ignore
        hashed_password=hashed_password
    )
    return {"message": "Contraseña actualizada correctamente."}
