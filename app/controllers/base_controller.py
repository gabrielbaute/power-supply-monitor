"""
Controller base abstracto para operaciones CRUD asíncronas con SQLAlchemy y SQLModel.
Este módulo define la clase `AsyncBaseController`, que proporciona una implementación básica para interactuar con la base de datos, incluyendo métodos para crear, leer, actualizar y eliminar registros. La clase está diseñada para ser genérica y puede ser extendida para modelos específicos.
"""
from uuid import UUID
from sqlmodel import select, SQLModel, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generic, Type, TypeVar, List, Optional, Any, Tuple, Union

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
ResponseSchemaType = TypeVar("ResponseSchemaType")

from app.errors.database_errors import DatabaseOperationError

class AsyncBaseController(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """
    Controlador base para operaciones CRUD asíncronas con SQLAlchemy y SQLModel.
    Esta clase proporciona métodos genéricos para interactuar con la base de datos, incluyendo la creación, lectura, actualización y eliminación de registros. Está diseñada para ser extendida por controladores específicos de modelos.

    Attributes:
        model (Type[ModelType]): El modelo SQLModel asociado con este controlador.
        session (AsyncSession): La sesión de base de datos asíncrona utilizada para las operaciones CRUD.

    Methods:
        get(id: UUID) -> Optional[ModelType]: Devuelve un registro por su ID.
        get_last_register_with_conditions(where_clause: List[Any], sort_by_attribute: str = "date") -> Optional[ModelType]: Devuelve el último registro que cumple con las condiciones dadas.
        get_multi(skip: int = 0, limit: int = 100) -> List[ModelType]: Devuelve una lista de registros con paginación.
        get_multi_with_conditions(where_clause: List[Any], skip: int = 0, limit: int = 100, sort_by_attribute: str = "date") -> List[ModelType]: Devuelve una lista de registros que cumplen con las condiciones dadas.
        create(obj_in: CreateSchemaType) -> ModelType: Crea un nuevo registro en la base de datos.
        update(db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]) -> ModelType: Actualiza un registro existente.
        remove(id: UUID) -> Optional[ModelType]: Elimina un registro de la base de datos.
    """
    def __init__(self, model: Type[ModelType], database_session: AsyncSession):
        """
        Inicializa el controlador con un modelo SQLModel y una sesión de base de datos asíncrona.

        Args:
            model (Type[ModelType]): El modelo SQLModel asociado con este controlador.
            database_session (AsyncSession): La sesión de base de datos asíncrona.
        """
        self.model = model
        self.database_session = database_session

    def _validate_uuid(self, uuid_str: Union[str, UUID]) -> UUID:
        """
        Helper para validar que una ID sea en efecto de tipo UUID.

        Args:
            uuid_str (Union[str, UUID]): ID en string o UUID.

        Returns:
            UUID: ID en formato UUID.
        """
        if isinstance(uuid_str, str):
            return UUID(uuid_str)
        else:
            return uuid_str

    async def _commit_or_rollback(self) -> None:
        """
        Intenta realizar un commit de la sesión actual. Si ocurre un error, realiza un rollback para revertir los cambios.

        Raises:
            Exception: Si ocurre un error durante el commit, se lanza una excepción con el error correspondiente y se realiza un rollback de la sesión.
        """
        try:
            await self.database_session.commit()
        except Exception:
            await self.database_session.rollback()
            raise

    async def get(self, id: UUID) -> Optional[ModelType]:
        """
        Devuelve un registro de la base de datos por su ID.

        Args:
            id (UUID): UUID del registro a buscar.

        Returns:
            Optional[ModelType]: El objeto encontrado o None si no existe.
        """
        statement = select(self.model).where(self.model.id == id) # type: ignore
        result = await self.database_session.execute(statement)
        return result.scalar_one_or_none()

    async def get_last_register_with_conditions(
        self,
        where_clause: List[Any],
        sort_by_attribute: str = "date"
    ) -> Optional[ModelType]:
        """
        Devuelve el último registro que cumple con las condiciones dadas, ordenado por un atributo específico en orden descendente.

        Args:
            where_clause (List[Any]): Lista de expresiones condicionales de SQLAlchemy para filtrar los registros.
            sort_by_attribute (str): Nombre del atributo por el cual ordenar los registros en orden descendente. Por defecto es "date".

        Returns:
            Optional[ModelType]: El objeto encontrado o None si no existe ningún registro que cumpla con las condiciones.
        """
        order_column = getattr(self.model, sort_by_attribute)
        statement = select(self.model).where(*where_clause).order_by(order_column.desc()).limit(1)
        result = await self.database_session.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi_with_conditions(
        self,
        where_clause: List[Any],
        skip: int = 0,
        limit: int = 100,
        sort_by_attribute: str = "registered_at"
    ) -> Tuple[List[ModelType], int]:
        """
        Devuelve una lista de registros que cumplen con las condiciones dadas y el conteo total de registros que coinciden.

        Args:
            where_clause (List[Any]): Lista de expresiones condicionales de SQLAlchemy/SQLModel para filtrar los registros.
            skip (int): Número de registros a omitir para la paginación.
            limit (int): Número máximo de registros a devolver.
            sort_by_attribute (str): Nombre del atributo por el cual ordenar los registros en orden descendente.

        Returns:
            Tuple[List[ModelType], int]: Tupla que contiene la lista de objetos paginados y el conteo total sin paginar.

        Raises:
            DatabaseOperationError: Si ocurre un error al consultar la base de datos.
        """
        try:
            # 1. Consulta para el conteo total sin la paginación (offset/limit)
            count_statement = select(func.count()).select_from(self.model)
            if where_clause:
                count_statement = count_statement.where(*where_clause)

            count_result = await self.database_session.execute(count_statement)
            total_count: int = count_result.scalar_one()

            # 2. Consulta para obtener los registros paginados y ordenados
            order_column = getattr(self.model, sort_by_attribute)
            statement = select(self.model)
            if where_clause:
                statement = statement.where(*where_clause)

            statement = statement.order_by(order_column.desc()).offset(skip).limit(limit)

            result = await self.database_session.execute(statement)
            items: List[ModelType] = list(result.scalars().all())

            return items, total_count
        except Exception as e:
            raise DatabaseOperationError(
                message="Error al realizar la consulta con condiciones en la base de datos.",
                details={"error": str(e)}
            )

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by_attribute: str = "registered_at"
    ) -> Tuple[List[ModelType], int]:
        """
        Devuelve una lista de registros de la base de datos con paginación y el conteo total.

        Args:
            skip (int): Registros a omitir para la paginación.
            limit (int): Número máximo de registros a devolver.
            sort_by_attribute (str): Nombre del atributo por el cual ordenar los registros en orden descendente.

        Returns:
            Tuple[List[ModelType], int]: Tupla con la lista de objetos obtenidos y el total de registros en la tabla.

        Raises:
            DatabaseOperationError: Si ocurre un error al consultar la base de datos.
        """
        return await self.get_multi_with_conditions(
            where_clause=[],
            skip=skip,
            limit=limit,
            sort_by_attribute=sort_by_attribute
        )

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        Crea un nuevo registro en la base de datos a partir de los datos proporcionados.

        Args:
            obj_in (CreateSchemaType): Objeto de entrada válido que contiene los datos para crear el nuevo registro.

        Returns:
            ModelType: El objeto recién creado en la base de datos.
        """
        obj_data = obj_in.model_dump() # type: ignore
        db_obj = self.model(**obj_data)

        self.database_session.add(db_obj)
        await self._commit_or_rollback()
        await self.database_session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """
        Actualiza un registro existente.

        Args:
            db_obj (ModelType): El objeto actual en la base de datos.
            obj_in (UpdateSchemaType | dict[str, Any]): Contenedor de los nuevos datos.

        Returns:
            ModelType: El objeto actualizado en la base de datos.
        """
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True) # type: ignore

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        self.database_session.add(db_obj)
        await self._commit_or_rollback()
        await self.database_session.refresh(db_obj)
        return db_obj

    async def remove(self, id: UUID) -> Optional[ModelType]:
        """
        Elimina un registro de la base de datos.

        Args:
            id (UUID): ID del registro a eliminar.

        Returns:
            Optional[ModelType]: El objeto eliminado si se encuentra, de lo contrario None.
        """
        obj = await self.get(id)
        if obj:
            await self.database_session.delete(obj)
            await self._commit_or_rollback()
        return obj
