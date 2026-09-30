"""
Módulo de servicio para la lectura y gestión de archivos de logs del sistema.
"""
from collections import deque
import logging
from pathlib import Path
from typing import List

from app.settings import Settings


class LogService:
    """
    Servicio para inspeccionar los archivos de registro (logs) generados por la aplicación.

    Attributes:
        settings (Settings): Configuración global de la aplicación.
        logger (logging.Logger): Logger para registrar eventos del propio servicio.
        log_file_path (Path): Ruta física al archivo principal de logs.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Inicializa el servicio de lectura de logs.

        Args:
            settings (Settings): Instancia con la configuración general.
        """
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self.log_file_path: Path = self.settings.LOGS_DIR / "monitor.log"

    async def get_tail_logs(self, lines: int = 25) -> List[str]:
        """
        Obtiene las últimas N líneas del archivo de log del sistema.

        Args:
            lines (int, optional): Cantidad de líneas a recuperar. Defaults to 25.

        Returns:
            List[str]: Lista de líneas obtenidas del archivo de log.
        """
        if not self.log_file_path.exists():
            self.logger.warning(
                f"El archivo de log no existe en la ruta: {self.log_file_path}"
            )
            return []

        try:
            with open(self.log_file_path, mode="r", encoding="utf-8") as file:
                # deque con maxlen lee de forma eficiente solo las últimas N líneas
                tail_lines = deque(file, maxlen=lines)
                return [line.rstrip("\r\n") for line in tail_lines]
        except Exception as e:
            self.logger.exception("Error al leer el archivo de log}")
            raise FileNotFoundError("Error al leer el archivo de log") from e
