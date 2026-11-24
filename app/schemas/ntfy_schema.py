from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, HttpUrl

from app.enums import NTFYPriority

class NTFYPayload(BaseModel):
    """
    Esquema para el payload de notificaciones a través de NTFY.

    Attributes:
        title (Optional[str]): Título principal de la notificación.
        event (Optional[str]): Identificador técnico del evento (opcional).
        priority (NTFYPriority): Nivel de prioridad de la notificación.
        description (Optional[str]): Cuerpo principal del mensaje.
        tags (Optional[str]): Etiquetas o emojis separados por comas.
        click (Optional[str]): URL que se abre al hacer clic sobre la notificación.
        icon (Optional[HttpUrl]): URL del icono/logo de la aplicación.
        url (Optional[str]): URL de adjunto o acción.
        data (Optional[Dict[str, Any]]): Metadatos adicionales.
    """
    title: Optional[str] = None
    event: Optional[str] = None
    priority: NTFYPriority = NTFYPriority.DEFAULT
    description: Optional[str] = None
    tags: Optional[str] = None
    click: Optional[str] = None
    icon: Optional[HttpUrl] = None
    url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Alerta de corte eléctrico",
                    "priority": 4,
                    "description": "Se ha registrado una falla eléctrica",
                    "tags": "warning,zap",
                    "icon": "https://midominio.com/logo.png",
                }
            ]
        }
    )
