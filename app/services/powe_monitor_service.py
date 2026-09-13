import logging
from pathlib import Path

from app.settings import Settings

class PowerMonitorService:
    """Servicio de monitoreo del estado de la fuente de alimentación AC del sistema.

    Attributes:
        logger (logging.Logger): Instancia para el registro de sucesos.
        settings (Settings): Configuración general de la aplicación.
        sysfs_ac_path (Path): Ruta al archivo sysfs para consultar el estado AC.
    """

    def __init__(
        self,
        settings: Settings,
        ac_supply_name: str = "AC0",
    ) -> None:
        """Inicializa el servicio de monitoreo de la fuente de alimentación.

        Args:
            settings (Settings): Instancia de la configuración de la app.
            ac_supply_name (str, optional): Nombre del dispositivo AC en sysfs. Defaults to "AC0".
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.settings = settings
        self.sysfs_ac_path: Path = (
            self.settings.SUPPLY_PATH / ac_supply_name / "online"
        )

    def read_ac_status(self) -> bool:
        """Lee el estado de la fuente AC desde el sistema de archivos /sys.

        Returns:
            bool: True si está conectado a la red eléctrica, False si está en batería.

        Raises:
            FileNotFoundError: Si la ruta en sysfs no existe.
            ValueError: Si el contenido del archivo no se puede interpretar como entero.
        """
        if not self.sysfs_ac_path.exists():
            self.logger.error(
                f"No se encontró la interfaz de energía en: {self.sysfs_ac_path}"
            )
            raise FileNotFoundError(
                f"No se encontró la interfaz de energía en: {self.sysfs_ac_path}"
            )

        try:
            status_raw: str = self.sysfs_ac_path.read_text().strip()
            return int(status_raw) == 1
        except ValueError as err:
            self.logger.error(f"Error al parsear el estado de AC: {err}")
            raise ValueError(f"Error al parsear el estado de AC: {err}") from err
