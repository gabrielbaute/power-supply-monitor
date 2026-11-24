"""Módulo de servicio de registro de eventos eléctricos."""

import logging
from uuid import UUID
from typing import Optional
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import EventType
from app.errors import DatabaseSessionError, TimezoneRequiredError
from app.controllers import ElectricEventController
from app.schemas.electric_event_schemas import (
    ElectricEventCreate,
    ElectricEventListResponse,
    ElectricEventResponse,
    ElectricEventUpdate,
)

class ElectricEventService:
    """
    Servicio de gestión de eventos eléctricos en el sistema.
    """
    def __init__(self, database_session: AsyncSession):
        self.database_session = database_session
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _ensure_timezone_aware(dt: datetime, field_name: str) -> None:
        """
        Valida que un objeto datetime contenga información explícita de zona horaria.

        Args:
            dt (datetime): Fecha y hora a validar.
            field_name (str): Nombre del parámetro evaluado.

        Raises:
            TimezoneRequiredError: Si el datetime es naive (tzinfo es None o utcoffset es None).
        """
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            raise TimezoneRequiredError(
                message=f"El parámetro '{field_name}' debe incluir zona horaria explícita (formato ISO 8601 con offset, ej. '2026-11-01T00:00:00-04:00' o '2026-11-01T00:00:00Z').",
                details={
                    "field": field_name,
                    "received": dt.isoformat(),
                    "expected_format": "YYYY-MM-DDTHH:MM:SS±HH:MM",
                },
            )

    @property
    def controller(self) -> ElectricEventController:
        """
        Proporciona una instancia de ElectricEventController.

        Returns:
            ElectricEventController

        Raises:
            DatabaseSessionError: si no se provee una instancia de la base de datos.
        """
        if not self.database_session:
            raise DatabaseSessionError(
                message="Se requiere una sesión de la base de datos para operar",
                details={"error": "Sesión de base de datos no proveída."}
            )
        return ElectricEventController(database_session=self.database_session)

    async def register_event(self, event_data: ElectricEventCreate) -> Optional[ElectricEventResponse]:
        """
        Registra un nuevo evento eléctrico.

        Args:
            event_data (ElectricEventCreate): Esquema de nuevo evento eléctrico

        Returns:
            Optional[ElectricEventResponse]: Evento eléctrico creado
        """
        event_register = await self.controller.register_event(event_data=event_data)
        self.logger.info(f"Evento electrico registrado en la db: {event_register.event_type.value}")
        return event_register

    async def get_event_by_id(self, event_id: UUID) -> Optional[ElectricEventResponse]:
        """
        Obtiene el esquema de respuesta de un evento eléctrico por su ID.
        """
        event_register = await self.controller.get_event_by_id(event_id=event_id)
        return event_register

    async def close_last_open_event(
        self,
        end_timestamp: Optional[datetime] = None
    ) -> Optional[ElectricEventResponse]:
        """
        Cierra el último evento eléctrico abierto asignándole su marca de finalización.

        Args:
            end_timestamp (Optional[datetime]): Marca de tiempo de finalización.
                Si es None, se usa la hora actual en UTC.

        Returns:
            Optional[ElectricEventResponse]: El evento actualizado, o None si no había eventos abiertos.
        """
        last_open_event = await self.controller.get_last_open_event()
        if last_open_event is None:
            self.logger.warning("No se encontró ningún evento abierto para cerrar.")
            return None

        return await self.update_event(
            event_id=last_open_event.id,
            event_data=ElectricEventUpdate(
                end_timestamp=end_timestamp or datetime.now(UTC)
            )
        )

    async def get_events_by_event_type(
        self,
        event_type: EventType,
        skip: int = 0,
        limit: int = 100
    ) -> ElectricEventListResponse:
        """
        Obtiene los eventos eléctricos por tipo.
        """
        event_registers = await self.controller.get_events_by_event_type(
            event_type=event_type,
            skip=skip,
            limit=limit
        )
        return event_registers

    async def get_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> ElectricEventListResponse:
        """
        Obtiene los eventos eléctricos para un rango de fecha determinado.

        Args:
            start_date (datetime): Fecha y hora de inicio con zona horaria.
            end_date (datetime): Fecha y hora de fin con zona horaria.
            skip (int): Registros a omitir en la paginación.
            limit (int): Máximo de registros a retornar.

        Returns:
            ElectricEventListResponse: Lista paginada de eventos y conteo total.

        Raises:
            TimezoneRequiredError: Si start_date o end_date no incluyen zona horaria.
        """
        self._ensure_timezone_aware(start_date, "start_date")
        self._ensure_timezone_aware(end_date, "end_date")

        event_registers = await self.controller.get_events_by_date_range(
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        return event_registers

    async def update_event(self, event_id: UUID, event_data: ElectricEventUpdate) -> Optional[ElectricEventResponse]:
        """
        Actualiza los datos de un evento eléctrico previamente registrado.

        Args:
            event_id (UUID): ID del registro a actualizar.
            event_data (ElectricEventUpdate): Datos a actualizar.

        Returns:
            Optional[ElectricEventResponse]: Datos actualizados.
        """
        updated_event = await self.controller.update_event(
            event_id=event_id,
            event_data=event_data
        )
        self.logger.info(f"Registro de evento actualizado: {updated_event.id.__str__()}")
        return updated_event

    async def delete_event(self, event_id: UUID) -> Optional[ElectricEventResponse]:
        """
        Elimina el registro de un evento eléctrico.

        Args:
            event_id (UUID): ID del registro a eliminar.

        Returns:
            Optional[ElectricEventResponse]: Datos del evento eliminado, None en caso contrario.
        """
        event = await self.get_event_by_id(event_id=event_id)
        if not event:
            self.logger.warning(f"Evento {event_id} no encontrado.")
            return None

        return await self.controller.delete_event(event_id=event_id)
