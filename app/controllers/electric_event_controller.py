"""Modulo para gestionar la persistencia de datos de los eventos eléctricos."""
import logging
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import EventType
from app.controllers.base_controller import AsyncBaseController
from app.errors import RegisterNotFoundError, DatabaseOperationError
from app.database.models.electric_eventl_sql_model import ElectricEventSQLModel
from app.schemas.electric_event_schemas import (
    ElectricEventCreate,
    ElectricEventUpdate,
    ElectricEventResponse,
    ElectricEventListResponse
)

class ElectricEventController(
    AsyncBaseController[
        ElectricEventSQLModel,
        ElectricEventCreate,
        ElectricEventUpdate,
        ElectricEventResponse
    ]
):
    """Controlador de gestión de registros de eventos eléctricos."""
    def __init__(self, database_session: AsyncSession):
        """
        Inicializa el controlador de eventos eléctricos con una sesión asíncrona.

        Args:
            database_session (AsyncSession): Asynchronous database session context.
        """
        super().__init__(model=ElectricEventSQLModel, database_session=database_session)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.create_model = ElectricEventCreate
        self.update_model = ElectricEventUpdate
        self.response_model = ElectricEventResponse

    @staticmethod
    def _build_list_response(
        electric_events: List[ElectricEventSQLModel], total: int
    ) -> ElectricEventListResponse:
        """
        Construye una lista de usuarios paginada y validada como respuesta.

        Args:
            electric_events (List[ElectricEventSQLModel]): Lista de objetos ElectricEventSQLModel directo desde la base de datos.
            total (int): Conteo total de registros traídos en la consulta.

        Returns:
            ElectricEventListResponse: Lista de objetos de ElectricEventResponse y contador total de objetos dentro de la lista.
        """
        return ElectricEventListResponse(
            events=[ElectricEventResponse.model_validate(event.model_dump()) for event in electric_events],
            count=total,
        )

    async def _get_or_raise(self, event_id: UUID) -> ElectricEventSQLModel:
        """
        Obtiene un registro de usuario especÃ­fico o genere una excepciÃ³n.

        Args:
            event_id (UUID): Identificador de clave primaria de la base de datos.

        Returns:
            ElectricEventSQLModel: El modelo de datos de persistencia de evento.

        Raises:
            RegisterNotFoundError: Si el ID no se corresponde con ningún registro.
        """
        event_id = self._validate_uuid(event_id)
        obj = await self.get(id=event_id)
        if obj is None:
            self.logger.warning(f"El registro de evento {event_id} no se encontró en la base de datos.")
            raise RegisterNotFoundError(
                message="Registro de evento no encontrado en la base de datos.",
                details={"detail": f"ID del objeto de evento: {event_id}",}
            )
        return obj

    async def register_event(self, event_data: ElectricEventCreate) -> ElectricEventResponse:
        """
        Registra un nuevo evento eléctrico en la base de dtos

        Args:
            event_data (ElectricEventCreate): Datos del evento eléctrico.

        Returns:
            ElectricEventResponse: Esquema de respuesta del evento registrado en la base de datos.
        """
        new_event = await self.create(obj_in=event_data)
        return ElectricEventResponse.model_validate(new_event.model_dump())

    async def get_event_by_id(self, event_id: UUID) -> Optional[ElectricEventResponse]:
        """
        Obtiene el registro de un evento eléctrico por su ID.

        Args:
            event_id (UUID): ID del evento eléctrico.

        Returns:
            Optional[ElectricEventResponse]: Esquema de respuesta del evento eléctrico si existe, None en caso contrario.
        """
        event = await self._get_or_raise(event_id=event_id)
        if not event:
            return None
        return ElectricEventResponse.model_validate(event.model_dump())

    async def get_events_by_event_type(
        self,
        event_type: EventType,
        skip: int = 0,
        limit: int = 100
    ) -> ElectricEventListResponse:
        """
        Obtiene una lsita de eventos eléctricos de acuerdo al tipo de evento.
        """
        where_clause = [ElectricEventSQLModel.event_type == event_type]

        events, count = await self.get_multi_with_conditions(
            where_clause=where_clause,
            skip=skip,
            limit=limit,
            sort_by_attribute="start_timestamp"
        )
        return self._build_list_response(electric_events=events, total=count)

    async def get_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> ElectricEventListResponse:
        """
        Obtiene una lista de eventos eléctricos dentro de un rango cronológico dado.
        """
        where_clause = [
            ElectricEventSQLModel.start_timestamp >= start_date,
            ElectricEventSQLModel.start_timestamp <= end_date
        ]
        events, count = await self.get_multi_with_conditions(
            where_clause=where_clause,
            skip=skip,
            limit=limit,
            sort_by_attribute="start_timestamp"
        )
        return self._build_list_response(electric_events=events, total=count)

    async def update_event(
        self,
        event_id: UUID,
        event_data: ElectricEventUpdate
    ) -> ElectricEventResponse:
        """
        Actualiza un registro de un evento eléctrico en la base de datos.

        Args:
            event_id (UUID): ID del evento a actualizar.
            event_data (ElectricEventUpdate): Contenido de los datos a actualizar.

        Returns:
            ElectricEventResponse: Objeto de respuesta de usuario con la data ya actualizada.

        Raises:
            DatabaseOperationError: Si falla el proceso de guardado.
        """
        db_obj = await self._get_or_raise(event_id=event_id)
        try:
            updated_obj = await self.update(
                db_obj=db_obj,
                obj_in=event_data
            )
            self.logger.debug(f"Registro de evento {event_id} actualizado correctamente.")
            return ElectricEventResponse.model_validate(updated_obj.model_dump())
        except Exception as e:
            self.logger.error(f"Error al actualizar {event_id}: {e}")
            raise DatabaseOperationError(
                message=f"Error al actualizar el registro de evento {event_id}.",
                details={"detail": e}
            )

    async def delete_event(self, event_id: UUID) -> Optional[ElectricEventResponse]:
        """
        Elimina el registro de un usuario de la base de datos.

        Args:
            user_id (UUID): ID del usuario a eliminar.

        Returns:
            ElectricEventResponse: Objeto de respuesta de evento con los datos del evento eliminado.
        """
        db_obj = await self._get_or_raise(event_id=event_id)
        await self.remove(id=event_id)
        self.logger.info(f"Registro de evento {event_id} eliminado exitosamente.")
        return ElectricEventResponse.model_validate(db_obj.model_dump())
