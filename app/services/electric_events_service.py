"""Módulo de servicio de registro de eventos eléctricos."""

import logging
from uuid import UUID
from typing import Optional
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import EventType
from app.controllers import ElectricEventController
from app.schemas.electric_event_schemas import (
    ElectricEventCreate,
    ElectricEventListResponse,
    ElectricEventResponse,
    ElectricEventUpdate,
)

class ElectricEventService:
    def __init__(self, database_session: AsyncSession):
        self.controller = ElectricEventController(database_session=database_session)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def register_event(self, event_data: ElectricEventCreate) -> Optional[ElectricEventResponse]:
        event_register = await self.controller.register_event(event_data=event_data)
        self.logger.info(f"Evento electrico registrado en la db: {event_register.event_type.value}")
        return event_register

    async def get_event_by_id(self, event_id: UUID) -> Optional[ElectricEventResponse]:
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
        event_registers = await self.controller.get_events_by_date_range(
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        return event_registers

    async def update_event(self, event_id: UUID, event_data: ElectricEventUpdate) -> Optional[ElectricEventResponse]:
        updated_event = await self.controller.update_event(
            event_id=event_id,
            event_data=event_data
        )
        self.logger.info(f"Registro de evento actualizado: {updated_event.id.__str__()}")
        return updated_event

    async def delete_event(self, event_id: UUID) -> Optional[ElectricEventResponse]:
        event = await self.get_event_by_id(event_id=event_id)
        if not event:
            self.logger.warning(f"Evento {event_id} no encontrado.")
            return None

        return await self.controller.delete_event(event_id=event_id)
