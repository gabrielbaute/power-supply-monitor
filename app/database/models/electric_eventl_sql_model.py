from uuid import UUID, uuid4
from datetime import datetime, UTC
from sqlmodel import SQLModel, Field

from app.enums import EventType

class ElectricEventSQLModel(SQLModel, table=True):
    """
    Modelo de representación en la base de datos de un evento eléctrico.

    Attributes:
        id (UUID): ID de registro de la falla/evento eléctrico.
        start_timestamp (datetime): Marca de tiempo de inicio del evento.
        end_timestamp (datetime): Marca de tiempo de finalización del evento.
        latitude (float): Latitud de la ubicación desde donde se emite el registro de evento.
        longitude (float): Longitud de la ubicación desde donde se emite el registro de evento.
        event_type (EventType): Tipo de evento, corte o fluctuación.
    """
    __tablename__ = "fails" # type: ignore

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    start_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False,)
    end_timestamp: datetime = Field(nullable=True)
    latitude: float = Field(nullable=False)
    longitude: float = Field(nullable=False)
    event_type: EventType = Field(default=EventType.CORTE)
