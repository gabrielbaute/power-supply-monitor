"""
Módulo de servicio de usuario. Este módulo gestiona la lógica de negocio en torno a las operaciones
de un usuario sobre sus propios datos en la aplicación.
"""
import logging
from uuid import UUID
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.settings import Settings
from app.enums import UserRole, UserStatus
from app.controllers import UserController
from app.services.mail_service import MailService
from app.services.security_service import SecurityService
from app.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserLogin
)
from app.errors import ResourceNotFoundError, ValidationError, PermissionDeniedError

class UserService:
    """
    Servicio para manejar lógica de negocios relacionada con la gestión de usuarios.

    Attributes:
        database_session (AsyncSession): Sesión de acceso a la base de datos.
        settings (Settings): Instancia de configuración global de la app.
        mail_service (MailService): Servicio de envío de notificaciones por correo.
        controller (UserController): Controlador de usuario para persistencia de datos.
        security_service (SecurityService): Servicio de seguridad, autenticación y cifrado de la aplicación.
        logger (logging): Logger del módulo de servicio de usuario.
    """
    def __init__(self, database_session: AsyncSession, mail_service: MailService, settings: Settings):
        """
        Inicializa el servicio de usuario con una sesión de base de datos.

        Args:
            database_session (AsyncSession): Sesión de base de datos.
            mail_service (MailService): Servicio de envío de notificaciones por correo.
            settings (Settings): Instancia global de configuración de la aplicación.
        """
        self.database_session = database_session
        self.settings = settings
        self.mail_service = mail_service
        self.controller = UserController(database_session=self.database_session)
        self.security_service = SecurityService()
        self.logger = logging.getLogger(self.__class__.__name__)

    # ========= MÉTODOS PRIVADOS =========
    async def _mail_service_notification(self, user: UserResponse, template: str, subject: Optional[str] = None):
        """
        Método para envío de actualización de datos de la cuenta.
        """
        try:
            await self.mail_service.send_templated_email(
                recipient=user.email,
                subject=subject if subject else "Actualización de cuenta",
                template=template,
                context={"user_name": user.username}
            )
        except Exception as e:
            self.logger.error(f"Failed to send status email to {user.email}: {e}")

    async def _is_user_admin(self, user_id: UUID) -> bool:
        """
        Verifica si un usuario es un administrador.

        Args:
            user_id (str): ID del usuario.

        Returns:
            bool: True si el usuario es un administrador, False en caso contrario.
        """
        user = await self.controller.get_user_by_id(user_id=user_id)
        return user is not None and user.role == UserRole.ADMIN

    async def _check_permissions(self, user_id: UUID, requester_id: UUID) -> bool:
        """
        Verifica si un solicitante tiene permisos para modificar un recurso.
        La lógica permite el acceso si el solicitante es el dueño del recurso
        o si el solicitante posee privilegios de administrador.

        Args:
            user_id (UUID): ID del usuario dueño del recurso/registro.
            requester_id (UUID): ID del usuario que intenta realizar la acción.

        Returns:
            bool: True si el acceso es concedido, False en caso contrario.
        """
        # 1. Validación rápida: ¿Es el dueño?
        if user_id == requester_id:
            return True

        # 2. Si no es el dueño, verificamos si el SOLICITANTE es admin
        requester = await self.controller.get_user_by_id(requester_id)

        if not requester:
            self.logger.warning(
                f"Solicitante con ID {requester_id} no encontrado para verificación."
            )
            return False

        return requester.role == UserRole.ADMIN

    async def _change_user_status(
            self,
            user_id: UUID,
            new_status: UserStatus,
            subject: Optional[str] = None
        ) -> UserResponse:
        """
        Cambia el estatus de un usuario

        Args:
            user_id (str): The ID of the user.
            new_status (UserStatus): The new status to set.
            subject (Optional[str]): Asunto de la notificación de correo.

        Returns:
            UserResponse: The updated user data.

        Raises:
            ResourceNotFoundError: If the user is not found.
        """
        user_update = UserUpdate(status=new_status)
        updated_user = await self.controller.update_user(user_id=user_id, update_data=user_update)

        if not updated_user:
            raise ResourceNotFoundError(
                message="No se pudo cambiar el estatus del usuario.",
                details={"detail": f"Usuario con ID {user_id.__str__()} no encontrado."}
            )

        # Si se provee MailService, disparamos la notificación
        if self.mail_service:
            template_map = {
                UserStatus.ACTIVE: "emails/usuario_activado.html",
                UserStatus.BLOCK: "emails/usuario_bloqueado.html",
            }

            template = template_map.get(new_status)
            if template:
                await self._mail_service_notification(updated_user, template, subject)

        return updated_user

    # ========= MÉTODOS DE AUTENTICACIÓN =========
    async def register_user(
        self,
        user_data: UserCreate,
        password: str
    ) -> Optional[UserResponse]:
        """
        Orquesta el registro completo de un nuevo usuario:
        1. Hashea la contraseña.
        2. Crea el registro en la tabla de usuarios.

        Args:
            user_data (UserCreate): Datos de registro del usuario.
            password (str): Contraseña del usuario

        Returns:
            Optional[UserResponse]: Datos del usuario creado o None si falla.
        """
        try:
            # 1. Seguridad: Hashear contraseña
            hashed_password = self.security_service.get_password_hash(password)
            user_data.password_hash = hashed_password
            # 2. Persistencia: Crear usuario en DB
            new_user_db = await self.controller.create_user(user_data)
            if not new_user_db:
                raise ValidationError(
                    message="No se pudo crear el usuario en la DB.",
                    details={"detail": f"No se pudo crear el usuario {user_data.email} en la DB."}
                )

            self.logger.info(f"Usuario {new_user_db.email} registrado exitosamente con ID {new_user_db.id}")
            return new_user_db

        except Exception:
            self.logger.exception("Error en el proceso de registro}")
            raise

    async def authenticate_user(self, login_credentials: UserLogin) -> Optional[UserResponse]:
        """
        Orquesta la autenticación de un usuario a partir de credenciales de inicio de sesión.

        Args:
            login_data (UserLogin): Credenciales de inicio de sesión.

        Returns:
            Optional[UserResponse]: Datos del usuario autenticado o None si falla.
        """
        user = await self.controller.get_user_by_email(login_credentials.email)

        if not user:
            raise ResourceNotFoundError(
                message="Fallo en proceso de login",
                details={"Detalle de error:": f"Usuario con email {login_credentials.email} no encontrado."}
            )

        # Bloqueamos a los baneados
        if user.status == UserStatus.BLOCK:
            raise PermissionDeniedError(
                message="Fallo en proceso de autenticación",
                details={"Detalle de error:": "Cuenta bloqueada. Contacte a soporte."}
            )

        # Bloqueamos a los que aún no activan su cuenta.
        if user.status == UserStatus.INACTIVE:
            raise PermissionDeniedError(
                message="Fallo en proceso de autenticación",
                details={"Detalle de error:": "Debe validar su cuenta antes de iniciar sesión."}
            )

        user_credentials = await self.controller.get_user_password_hash(user.id)

        # Bloqueamos si los ID's no coinciden
        if not user_credentials.user_id == user.id: #type: ignore
            raise PermissionDeniedError(
                message="Fallo en proceso de autenticación",
                details={"detail": "El ID del solicitante no coincide con el de la cuenta."}
            )
        if not user_credentials:
            return None

        if not self.security_service.verify_password(login_credentials.password, user_credentials.password_hash):
            return None

        return user

    async def generate_password_recovery_data(self, email: str) -> Dict[str, str]:
        """
        Inicia el proceso de recuperación de contraseña por medio de un token. Se envía un correo con el token.

        Args:
            email (str): Email del usuario.
        Returns:
            Dict[str, str]: Data del correo de recuperación.
        """
        user = await self.controller.get_user_by_email(email)

        # Si no existe o no está activo, lanzamos el error que atrapará el router
        if not user or user.status == UserStatus.BLOCK:
            raise ResourceNotFoundError("Usuario no encontrado o bloqueado.")

        # Creamos el token con el scope específico
        token = self.security_service.create_password_reset_token(str(user.id))

        # URL que apunta al frontend
        recovery_url = f"{self.settings.URL_BASE}/reset-password?token={str(token)}"

        self.logger.info(f"Token de recuperación generado para user_id: {user.id}")

        # Devolvemos los datos para que el Router orqueste el envío
        return {
            "email": user.email,
            "user_name": f"{user.username}",
            "recovery_url": recovery_url
        }

    async def update_user_password(self, user_id: UUID, hashed_password: str) -> bool:
        """
        Actualiza la contraseña de un usuario.

        Args:
            user_id (str): ID del usuario.
            hashed_password (str): Contraseña hasheada.

        Returns:
            Optional[bool]: True si la actualización fue exitosa, False en caso contrario.
        """
        user = await self.controller.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("Usuario no encontrado")

        if user.status == UserStatus.BLOCK:
            raise PermissionDeniedError("El usuario está bloqueado, requiere acción del administrador")

        if user.status == UserStatus.INACTIVE:
            user.status = UserStatus.ACTIVE
            user_update = UserUpdate(status=user.status)
            await self.controller.update_user(user_id, user_update)

        return await self.controller.update_user_password(user_id, hashed_password)

    # ========= CRUD =========
    async def get_user_by_id(self, user_id: UUID) -> Optional[UserResponse]:
        """
        Obtiene un usuario por su ID.

        Args:
            user_id (str): ID del usuario.

        Returns:
            Optional[UserResponse]: Datos del usuario o None si no se encuentra.
        """
        user = await self.controller.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"No se encontró el usuario con el ID {user_id}.")
        return user

    async def get_all_users(self, requester_id: UUID, skip: int, limit: int = 100) -> UserListResponse:
        """
        Obtiene una lista de todos los usuarios.

        Args:
            requester_id (UUID): ID del usuario que solicita la acción.
            skip (int): Desplazamiento.
            limit (int): Tamaño de página.

        Returns:
            UserListResponse: Lista de usuarios.
        """
        if not self._is_user_admin(requester_id):
            raise PermissionDeniedError("Permisos insuficientes.")

        return await self.controller.get_all_users(skip, limit)

    async def get_users_by_status(
            self,
            requester_id: UUID,
            status: UserStatus,
            skip: int,
            limit: int = 100
    ) -> UserListResponse:
        """
        Obtiene una lista de usuarios filtrados por su estatus dentro de la app.

        Args:
            status (UserStatus): Estatus de los usuarios.
            skip (int): Valor de desplazamiento de paginación.
            limit (int): Cantidad de registros a traer por petición.

        Returns:
            UserListResponse: Lista de usuarios filtrados por estatus.

        Raises:
            PermissionDeniedError: Si el ejecutor no tiene privilegios de ADMIN.
        """
        if not self._is_user_admin(requester_id):
            raise PermissionDeniedError("Permisos insuficientes.")
        users = await self.controller.get_users_by_status(
            status=status,
            skip=skip,
            limit=limit
        )
        return users

    async def get_users_by_role(
            self,
            requester_id: UUID,
            role: UserRole,
            skip: int,
            limit: int = 100
    ) -> UserListResponse:
        """
        Obtiene una lista de usuarios filtrados por su estatus dentro de la app.

        Args:
            status (UserStatus): Estatus de los usuarios.
            skip (int): Valor de desplazamiento de paginación.
            limit (int): Cantidad de registros a traer por petición.

        Returns:
            UserListResponse: Lista de usuarios filtrados por estatus.

        Raises:
            PermissionDeniedError: Si el ejecutor no tiene privilegios de ADMIN.
        """
        if not self._is_user_admin(requester_id):
            raise PermissionDeniedError("Permisos insuficientes.")

        users = await self.controller.get_users_by_role(
            user_role=role,
            skip=skip,
            limit=limit
        )
        return users

    async def update_user_info(self, user_id: UUID, requester_id: UUID, update_data: UserUpdate) -> UserResponse:
        """
        Actualiza la información de un usuario.

        Args:
            user_id (str): ID del usuario.
            update_data (UserUpdate): Datos de actualización.
            requester_id (UUID): ID del usuario que solicita la acción.

        Returns:
            UserResponse: Datos del usuario actualizado.

        Raises:
            PermissionDeniedError: Si el ejecutor no tiene privilegios de ADMIN.
            ResourceNotFoundError: En caso de que no se encuentre el registro del usuario a editar.
        """
        if not self._check_permissions(user_id, requester_id):
            raise PermissionDeniedError(message="Permisos insuficientes para esta acción")

        updated_user = await self.controller.update_user(user_id, update_data)
        if not updated_user:
            raise ResourceNotFoundError("Usuario no encontrado o actualización fallida.")

        return updated_user

    async def activate_user(self, user_id: UUID, requester_id: UUID) -> UserResponse:
        """
        Cambia el estatus de un usuario a activo

        Args:
            user_id (UUID): ID del usuario que se va a activar.
            requester_id (UUID): ID del usuario que solicita la acción.

        Returns:
            UserResponse: Esquema de respuesta de usuario

        Raises:
            PermissionDeniedError: Si el ejecutor no tiene privilegios de ADMIN.
        """
        if not self._is_user_admin(requester_id):
            raise PermissionDeniedError(f"El usuario con ID {requester_id} no cuenta con privilegios suficientes.")

        subject = "Activación de cuenta"
        return await self._change_user_status(user_id=user_id, new_status=UserStatus.ACTIVE, subject=subject)

    async def deactivate_user(self, user_id: UUID, requester_id: UUID) -> UserResponse:
        """
        Cambia el estatus de un usuario a desactivado

        Args:
            user_id (UUID): ID del usuario que se va a activar.
            requester_id (UUID): ID del usuario que solicita la acción.

        Returns:
            UserResponse: Esquema de respuesta de usuario

        Raises:
            PermissionDeniedError: Si el ejecutor no tiene privilegios de ADMIN.
        """
        if not self._check_permissions(user_id, requester_id):
            raise PermissionDeniedError(message="Permisos insuficientes para esta acción")

        subject = "Su cuenta ha sido desactivada"
        return await self._change_user_status(user_id=user_id, new_status=UserStatus.INACTIVE, subject=subject)

    async def block_user(self, user_id: UUID, requester_id: Optional[UUID]) -> UserResponse:
        """
        Cambia el estatus de un usuario a Bloqueado

        Args:
            user_id (UUID): ID del usuario que se va a activar.
            requester_id (UUID): ID del usuario que solicita la acción.

        Returns:
            UserResponse: Esquema de respuesta de usuario

        Raises:
            PermissionDeniedError: Si el ejecutor no tiene privilegios de ADMIN.
        """
        if requester_id:
            if not self._is_user_admin(requester_id):
                raise PermissionDeniedError("Privilegios insuficientes para esta acción")

        subject = "Su cuenta ha sido bloqueada."
        return await self._change_user_status(user_id=user_id, new_status=UserStatus.BLOCK, subject=subject)

    async def delete_user(self, user_id: UUID, requester_id: UUID) -> UserResponse:
        """
        Elimina a un usuario por su ID.

        Args:
            user_id (UUID): ID del usuario a eliminar.
            requester_id (UUID): ID del usuario que solicita la acción.

        Returns:
            UserResponse: Los datos del usuario eliminado.

        Raises:
            ResourceNotFoundError: Si el usuario a eliminar no se encuentra en la base de datos.
            PermissionDeniedError: Si el ejecutor no tiene privilegios de ADMIN.
        """
        user = await self.controller.get_user_by_id(user_id=user_id)
        if not user:
            self.logger.warning(f"Usuario {user_id} no encontrado")
            raise ResourceNotFoundError("Usuario no encontrado")

        if not self._is_user_admin(requester_id):
            raise PermissionDeniedError("Privilegios insuficientes")

        return await self.controller.delete_user(user_id)
