import logging
from pathlib import Path
from re import S

from app.settings import Settings

class PowerMonitorService:
    """
    vicio de monitoreo del estado de la fuente de alimentación AC del sistema.

    Attributes:
        check_interval (int): Intervalo en segundos entre cada comprobación.
        sysfs_ac_path (Path): Ruta al archivo del sistema de archivos sysfs para la fuente AC.
        is_ac_connected (bool): Estado interno actual de la conexión de energía.
    """

    def __init__(
        self,
        settings: Settings,
        ac_supply_name: str = "AC",
    ) -> None:
        """
        Inicializa el servicio de monitoreo de energía.

        Args:
            ac_supply_name (str, optional): Nombre del dispositivo AC en /sys/class/power_supply/.
            Defaults to "AC". (En algunos sistemas puede ser ACAD, ADP1, etc.).
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.settings = settings
        self.sysfs_ac_path: Path = self.settings.SUPPLY_PATH / f"{ac_supply_name}" / "online"
        self.is_ac_connected: bool = self._read_ac_status()

    def _read_ac_status(self) -> bool:
        """
        Lee directamente el estado de la fuente AC desde el sistema de archivos /sys.

        Returns:
            bool: True si la laptop está conectada a la corriente, False si está en batería.

        Raises:
            FileNotFoundError: Si la ruta /sys/class/power_supply/ provista no existe.
            ValueError: Si el contenido del archivo sysfs no se puede interpretar como entero.
        """
        if not self.sysfs_ac_path.exists():
            self.logger.error(f"No se encontró la interfaz de energía en: {self.sysfs_ac_path}")
            raise FileNotFoundError(
                f"No se encontró la interfaz de energía en: {self.sysfs_ac_path}"
            )

        try:
            status_raw: str = self.sysfs_ac_path.read_text().strip()
            return int(status_raw) == 1
        except ValueError as err:
            self.logger.error(f"Error al parsear el estado de AC: {err}")
            raise ValueError(f"Error al parsear el estado de AC: {err}") from err
