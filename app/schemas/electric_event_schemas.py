from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

from app.enums import EventType

class ElectricEventCreate(BaseModel):
    """
    Modelo de registro de un nuevo evento eléctrico.

    Attributes:
        id (UUID): ID de registro de la falla/evento eléctrico.
        start_timestamp (Optional[datetime]): Marca de tiempo de inicio del evento.
        end_timestamp (Optional[datetime]): Marca de tiempo de finalización del evento.
        latitude (float): Latitud de la ubicación desde donde se emite el registro de evento.
        longitude (float): Longitud de la ubicación desde donde se emite el registro de evento.
        event_type (EventType): Tipo de evento, corte o fluctuación.
    """
    id: UUID
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    latitude: float
    longitude: float
    event_type: EventType = EventType.CORTE

    model_config = ConfigDict(from_attributes=True)

class ElectricEventUpdate(BaseModel):
    """
    Modelo de edición de un evento eléctrico.

    Attributes:
        start_timestamp ( Optional[datetime]): Marca de tiempo de inicio del evento.
        end_timestamp (Optional[datetime]): Marca de tiempo de finalización del evento.
        latitude (Optional[float]): Latitud de la ubicación desde donde se emite el registro de evento.
        longitude (Optional[float]): Longitud de la ubicación desde donde se emite el registro de evento.
        event_type (Optional[EventType]): Tipo de evento, corte o fluctuación.
    """
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    event_type: Optional[EventType] = None

    model_config = ConfigDict(from_attributes=True)

class ElectricEventResponse(BaseModel):
    """
    Modelo de respuesta del registro de un evento eléctrico.

    Attributes:
        id (UUID): ID de registro de la falla/evento eléctrico.
        start_timestamp (datetime): Marca de tiempo de inicio del evento.
        end_timestamp (Optional[datetime]): Marca de tiempo de finalización del evento.
        latitude (float): Latitud de la ubicación desde donde se emite el registro de evento.
        longitude (float): Longitud de la ubicación desde donde se emite el registro de evento.
        event_type (EventType): Tipo de evento, corte o fluctuación.
    """
    id: UUID
    start_timestamp: datetime
    end_timestamp: Optional[datetime] = None
    latitude: float
    longitude: float
    event_type: EventType

    model_config = ConfigDict(from_attributes=True)

class ElectricEventListResponse(BaseModel):
    """
    Respuesta de lista de varios eventos eléctricos. Para consultas masivas en la base de datos.

    Attributes:
        events (List[ElectricEventResponse]): Lista de objetos ElectricEventResponse
        count (int): Total de eventos traídos desde la base de datos.
    """
    events: List[ElectricEventResponse] = []
    count: int = 0
