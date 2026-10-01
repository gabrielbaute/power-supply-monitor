"""Módulo para el controlador de usuario."""
import logging
from uuid import UUID
from typing import List, Optional, Any
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserStatus, UserRole
from app.database.models import UserSQLModel
from app.errors import DatabaseOperationError
from app.controllers.base_controller import AsyncBaseController
from app.schemas.user_schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserPasswordHash
)

class UserController(
    AsyncBaseController[
        UserSQLModel,
        UserCreate,
        UserUpdate,
        UserResponse,
    ]
):
    """Controlador para gestión de la data de usuarios."""
    def __init__(self, database_session: AsyncSession):
        """
        Inicializa el controlador de usuario con una sesión asíncrona.

        Args:
            session (AsyncSession): Asynchronous database session context.
        """
        super().__init__(model=UserSQLModel, database_session=database_session)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.create_model = UserCreate
        self.update_model = UserUpdate
        self.response_model = UserResponse

    @staticmethod
    def _build_list_response(
        users: List[UserSQLModel], total: int
    ) -> UserListResponse:
        """
        Construye una lista de usuarios paginada y validada como respuesta.

        Args:
            users (List[UserSQLModel]): Lista de objetos UserSQLModel directo desde la base de datos..
            total (int): Global count matching the filtered parameters.

        Returns:
            UserListResponse: Lista de objetos de UserResponse y contador total de objetos dentro de la lista.
        """
        return UserListResponse(
            users=[UserResponse.model_validate(user.model_dump()) for user in users],
            count=total,
        )

    async def create_user(self, new_user_data: UserCreate) -> Optional[UserResponse]:
        """
        Crea un registro para un nuevo usuario en la base de datos

        Args:
            new_user_data (UserCreate): Esquema que contiene la entrada del usuario.

        Returns:
            Optional[UserResponse]: The validated response schema or None.
        """
        new_user = await self.create(obj_in=new_user_data)
        if not new_user:
            return None

        return UserResponse.model_validate(new_user)

    async def get_user_by_id(self, user_id: UUID) -> Optional[UserResponse]:
        """
        Obtiene un registro de usuario de la base de datos a partir de su ID.

        Args:
            user_id (UUID): ID del usuario.

        Returns:
            Optional[UserResponse]: Modelo de datosd el usuario.
        """
        user = await self._get_or_raise(db_obj_id=user_id)
        if not user:
            self.logger.warning(f"Usuario {user_id} no encontrado.")
            return None
        return UserResponse.model_validate(user.model_dump())

    async def get_user_by_email(self, user_email: str) -> Optional[UserResponse]:
        """
        Obtiene el registro de un usuario a partir de su email.

        Args:
            user_email (str): Email del usuario

        Returns:
            UserResponse: Esquema de respuesta del usuario si se encuentra, None en caso contrario.
        """
        stmt = select(UserSQLModel).where(UserSQLModel.email == user_email)
        data = await self.database_session.execute(stmt)

        if data:
            user_db = data.scalar_one_or_none()
            return UserResponse.model_validate(user_db.model_dump()) # type: ignore

        return None

    async def get_user_password_hash(self, user_id: UUID) -> Optional[UserPasswordHash]:
        """
        Obtiene el hash del password de usuario a partir de la ID del usuario (para logging).

        Args:
            user_id (UUID): ID del usuario.

        Returns:
            Optional[UserPasswordHash]: Objeto que contiene el password hash del usuario y su ID. None
            en caso de fallar al recuperar el usuario.
        """
        user_id = self._validate_uuid(user_id)
        try:
            stmt = select(UserSQLModel.password_hash).where(UserSQLModel.id == user_id)
            data = await self.database_session.execute(stmt)
            password_hash = data.scalar_one_or_none()
            return UserPasswordHash(user_id=user_id, password_hash=password_hash) if password_hash else None
        except Exception as e:
            self.logger.error(f"Error retrieving password hash for user {user_id}: {e}")
            raise DatabaseOperationError(
                message=f"Error retrieving password hash from user {user_id}",
                details={"detail": str(e)}
            ) from e

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> UserListResponse:
        """
        Obtiene todos los usarios en la base de datos.

        Args:
            skip (int): Valor de desplazamiento de paginación.
            limit (int): Cantidad de registros a traer por petición.

        Returns:
            UserListResponse: Lista de usuarios con todos los usuarios.
        """
        users, total = await self.get_multi(skip=skip, limit=limit, sort_by_attribute="created_at")
        return self._build_list_response(users=users, total=total)

    async def get_users_by_status(self, status: UserStatus, skip: int = 0, limit: int = 100) -> UserListResponse:
        """
        Obtiene una lista de usuarios filtrados por su estatus dentro de la app.

        Args:
            status (UserStatus): Estatus de los usuarios.
            skip (int): Valor de desplazamiento de paginación.
            limit (int): Cantidad de registros a traer por petición.

        Returns:
            UserListResponse: Lista de usuarios filtrados por estatus.
        """
        conditions = [UserSQLModel.status == status]
        users_data, total_count = await self.get_multi_with_conditions(
            where_clause=conditions,
            skip=skip,
            limit=limit,
            sort_by_attribute="created_at"
        )
        return self._build_list_response(users=users_data, total=total_count)

    async def get_users_by_role(self, user_role: UserRole, skip: int = 0, limit: int = 100) -> UserListResponse:
        """
        Obtiene una lista de usuarios filtrados por su rol dentro de la app.

        Args:
            user_role (UserRole): Rol de los usuarios.
            skip (int): Valor de desplazamiento de paginación.
            limit (int): Cantidad de registros a traer por petición.

        Returns:
            UserListResponse: Lista de usuarios filtrados por rol.
        """
        conditions = [UserSQLModel.role == user_role]
        users_data, total_count = await self.get_multi_with_conditions(
            where_clause=conditions,
            skip=skip,
            limit=limit,
            sort_by_attribute="created_at"
        )
        return self._build_list_response(users=users_data, total=total_count)

    async def update_user(self, user_id: UUID, update_data: UserUpdate) -> UserResponse:
        """
        Actualiza un registro de usuario en la base de datos.

        Args:
            user_id (UUID): ID del usuario a actualizar.
            update_data (UserUpdate): Contenido de los datos a actualizar.

        Returns:
            UserResponse: Objeto de respuesta de usuario con la data ya actualizada.

        Raises:
        """
        db_obj = await self._get_or_raise(db_obj_id=user_id)
        try:
            updated_obj = await self.update(
                db_obj=db_obj,
                obj_in=update_data
            )
            self.logger.debug(f"Registro de usurio {user_id} actualizado correctamente.")
            return UserResponse.model_validate(updated_obj.model_dump())
        except Exception as e:
            self.logger.error(f"Error al actualizar {user_id}: {e}")
            raise DatabaseOperationError(
                message=f"Error al actualizar el registro de usuario {user_id}.",
                details={"detail": str(e)}
            ) from e

    async def update_user_password(self, user_id: UUID, hashed_password: str) -> bool:
        """
        Actualiza la contraseña de un usuario existente.

        Args:
            user_id (UUID): ID del usuario.
            hashed_password (str): Hash de la contraseña.

        Returns:
            Optional[bool]: True si la actualización fue exitosa, False en caso contrario.
        """
        db_obj = await self._get_or_raise(db_obj_id=user_id)
        db_obj.password_hash = hashed_password
        if not await self._update_or_rollback(db_obj):
            self.logger.error(f"Error al actualizar la contraseña de {user_id}")
            return False

        return True

    async def delete_user(self, user_id: UUID) -> Optional[UserResponse]:
        """
        Elimina el registro de un usuario de la base de datos.

        Args:
            user_id (UUID): ID del usuario a eliminar.

        Returns:
            UserResponse: Objeto de respuesta de usuario con los datos del usuario eliminado.
        """
        db_obj = await self._get_or_raise(db_obj_id=user_id)
        await self.remove(id=user_id)
        self.logger.info(f"Registro de usuario {user_id} eliminado exitosamente.")
        return UserResponse.model_validate(db_obj.model_dump())
