"""
Módulo de rutas para la consulta e inspección de logs del servidor.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_log_service
from app.services import LogService

router = APIRouter(prefix="/logs", tags=["Logs"])

@router.get("", summary="Obtener las últimas líneas del log")
async def get_logs(
    lines: int = Query(
        default=25,
        ge=1,
        le=2000,
        alias="log-lines",
        description="Número de líneas a recuperar desde el final del log."
    ),
    log_service: LogService = Depends(get_log_service)
) -> Dict[str, Any]:
    """
    Consulta las últimas líneas registradas en el archivo de logs del sistema.

    Args:
        lines (int): Número de líneas a consultar (por defecto 25).
        log_service (LogService): Servicio de lectura de logs inyectado.

    Returns:
        Dict[str, Any]: Diccionario con las líneas del log y el total de líneas devueltas.
    """
    log_lines: List[str] = await log_service.get_tail_logs(lines=lines)
    return {
        "lines_requested": lines,
        "count": len(log_lines),
        "logs": log_lines
    }
