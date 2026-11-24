"""
Módulo de rutas para pruebas y emisión de notificaciones del sistema.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_current_admin, get_ntfy_service
from app.errors import NTFYNotificationError
from app.schemas import NTFYPayload, UserResponse
from app.services import NtfysService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post(
    "/test",
    status_code=status.HTTP_200_OK,
    summary="Enviar notificación de prueba a NTFY",
)
async def send_test_notification(
    payload: NTFYPayload,
    topic: Optional[str] = Query(
        default=None,
        description="Tópico opcional de NTFY. Si se omite, usa NTFY_TOPIC configurado.",
    ),
    current_admin: UserResponse = Depends(get_current_admin),
    ntfy_service: NtfysService = Depends(get_ntfy_service),
) -> Dict[str, Any]:
    """
    Emite una notificación de prueba hacia el servidor NTFY configurado.

    Args:
        payload (NTFYPayload): Contenido estructurado de la notificación a enviar.
        topic (Optional[str]): Canal destino opcional; por defecto usa el tópico principal.
        current_admin (UserResponse): Usuario administrador autenticado que solicita la prueba.
        ntfy_service (NtfysService): Servicio de notificaciones NTFY inyectado.

    Returns:
        Dict[str, Any]: Confirmación del envío con el código de estado HTTP retornado por NTFY.

    Raises:
        NTFYNotificationError: Si el servidor NTFY no responde o falla la resolución/conexión.
    """
    try:
        status_code: Optional[int] = await ntfy_service.emit(
            payload=payload,
            topic=topic,
        )
    finally:
        await ntfy_service.close()

    if status_code is None:
        raise NTFYNotificationError(
            message="Fallo al conectar o emitir la notificación de prueba en NTFY. Revisa los logs del contenedor.",
            details={
                "ntfy_url": ntfy_service.settings.NTFY_URL,
                "topic": topic or ntfy_service.settings.NTFY_TOPIC,
            },
        )

    return {
        "status": "sent",
        "ntfy_status_code": status_code,
        "topic": topic or ntfy_service.settings.NTFY_TOPIC,
        "requested_by": current_admin.username,
    }
