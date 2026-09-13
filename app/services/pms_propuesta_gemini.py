"""
Este documento contiene la propuesta de script creada por Gemini

Módulo para la detección de fallos de energía y notificación vía ntfy.

Este script monitorea el estado de la fuente de alimentación AC en servidores
basados en laptops con Ubuntu y envía alertas en tiempo real mediante ntfy.
"""

from pathlib import Path
import time
import urllib.parse
import urllib.request


class PowerMonitorService:
    """Servicio de monitoreo del estado de la fuente de alimentación AC del sistema.

    Attributes:
        ntfy_url (str): URL completa del tema (topic) en el servidor de ntfy.
        check_interval (int): Intervalo en segundos entre cada comprobación.
        sysfs_ac_path (Path): Ruta al archivo del sistema de archivos sysfs para la fuente AC.
        is_ac_connected (bool): Estado interno actual de la conexión de energía.
    """

    def __init__(
        self,
        ntfy_host: str,
        topic: str,
        ac_supply_name: str = "AC",
        check_interval: int = 5,
    ) -> None:
        """Inicializa el servicio de monitoreo de energía.

        Args:
            ntfy_host (str): Servidor o IP donde corre ntfy (ej. 'https://ntfy.sh' o 'http://192.168.1.50:8080').
            topic (str): Nombre del tema (topic) donde se publicarán los mensajes.
            ac_supply_name (str, optional): Nombre del dispositivo AC en /sys/class/power_supply/.
                Defaults to "AC". (En algunos sistemas puede ser ACAD, ADP1, etc.).
            check_interval (int, optional): Intervalo de escaneo en segundos. Defaults to 5.
        """
        self.ntfy_url: str = urllib.parse.urljoin(ntfy_host, topic)
        self.check_interval: int = check_interval
        self.sysfs_ac_path: Path = Path(f"/sys/class/power_supply/{ac_supply_name}/online")

        # Leemos el estado inicial para evitar falsas alarmas al arrancar el servicio
        self.is_ac_connected: bool = self._read_ac_status()

    def _read_ac_status(self) -> bool:
        """Lee directamente el estado de la fuente AC desde el sistema de archivos /sys.

        Returns:
            bool: True si la laptop está conectada a la corriente, False si está en batería.

        Raises:
            FileNotFoundError: Si la ruta /sys/class/power_supply/ provista no existe.
            ValueError: Si el contenido del archivo sysfs no se puede interpretar como entero.
        """
        if not self.sysfs_ac_path.exists():
            raise FileNotFoundError(
                f"No se encontró la interfaz de energía en: {self.sysfs_ac_path}"
            )

        try:
            status_raw: str = self.sysfs_ac_path.read_text().strip()
            return int(status_raw) == 1
        except ValueError as err:
            raise ValueError(f"Error al parsear el estado de AC: {err}") from err

    def send_ntfy_notification(
        self, title: str, message: str, priority: int = 3, tags: str = ""
    ) -> None:
        """Envía una notificación HTTP POST al servidor ntfy especificado.

        Args:
            title (str): Título que mostrará la notificación.
            message (str): Cuerpo principal del mensaje.
            priority (int, optional): Nivel de prioridad de ntfy (1 al 5). Defaults to 3.
            tags (str, optional): Etiquetas o emojis separados por comas para ntfy. Defaults to "".
        """
        headers: dict[str, str] = {
            "Title": title,
            "Priority": str(priority),
        }
        if tags:
            headers["Tags"] = tags

        req = urllib.request.Request(
            url=self.ntfy_url,
            data=message.encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as response:
                _ = response.read()
        except Exception as error:
            # En un entorno de producción se recomienda registrar con logging
            print(f"[Error] Fallo al enviar notificación a ntfy: {error}")

    def run(self) -> None:
        """Ejecuta el bucle principal de monitoreo continuo."""
        print(f"Iniciando monitoreo de energía en: {self.sysfs_ac_path}")
        print(f"Publicando alertas en: {self.ntfy_url}")

        while True:
            try:
                current_ac_status: bool = self._read_ac_status()

                # Detectamos un cambio de estado en la alimentación
                if current_ac_status != self.is_ac_connected:
                    self.is_ac_connected = current_ac_status

                    if not self.is_ac_connected:
                        self.send_ntfy_notification(
                            title="🔴 CORTE DE ENERGÍA DETECTADO",
                            message="El servidor ha perdido la alimentación de red y está operando con BATERÍA.",
                            priority=5,
                            tags="warning,zap",
                        )
                    else:
                        self.send_ntfy_notification(
                            title="🟢 ENERGÍA RESTABLECIDA",
                            message="El suministro eléctrico se ha restaurado. El servidor vuelve a cargar la batería.",
                            priority=3,
                            tags="heavy_check_mark,electric_plug",
                        )

            except Exception as loop_error:
                print(f"[Error en loop]: {loop_error}")

            time.sleep(self.check_interval)
