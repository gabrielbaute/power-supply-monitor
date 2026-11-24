from uuid import UUID
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query

from app.services import ElectricEventService
from app.api.dependencies import get_electric_event_service
from app.schemas import ElectricEventResponse, ElectricEventListResponse

router = APIRouter(prefix="/events", tags=["Electric Events"])

@router.get("/detail", response_model=ElectricEventResponse)
async def get_event_detail(
    event_id: UUID = Query(description="ID del evento eléctrico"),
    electric_event_service: ElectricEventService = Depends(get_electric_event_service)
) -> Optional[ElectricEventResponse]:
    """
    Obtiene el detalle de un evento eléctrico concreto a partir de su ID
    """
    return await electric_event_service.get_event_by_id(event_id=event_id)

@router.get("/history", response_model=ElectricEventListResponse)
async def get_events_history(
    start_date: datetime = Query(
        description="Fecha de inicio con zona horaria (ej. 2026-11-01T00:00:00-04:00 o 2026-11-01T00:00:00Z)."
    ),
    end_date: datetime = Query(
        description="Fecha de fin con zona horaria (ej. 2026-11-24T23:59:59-04:00 o 2026-11-24T23:59:59Z)."
    ),
    skip: int = Query(0, ge=0, description="Registros a saltar en la paginación."),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros a traer por petición."),
    electric_event_service: ElectricEventService = Depends(get_electric_event_service)
) -> ElectricEventListResponse:
    """
    Obtiene el histórico de eventos eléctricos registrados en el server hasta una fecha dada.
    """
    electric_events = await electric_event_service.get_events_by_date_range(
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return electric_events
