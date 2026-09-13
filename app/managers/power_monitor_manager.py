import logging
import time

from app.enums import NTFYPriority
from app.schemas import WebhookPayload
from app.services import NtfysService, PowerMonitorService
from app.settings import Settings

class PowerMonitorManager:
    """Mánager principal para orquestar la lectura de energía y el envío de notificaciones.

    Attributes:
        settings (Settings): Instancia de configuraciones globales.
        logger (logging.Logger): Instancia para el registro de logs.
        power_monitor_service (PowerMonitorService): Servicio de lectura del sistema sysfs.
        ntfy_service (NtfysService): Servicio de emisión de alertas vía ntfy.
        is_ac_connected (bool): Estado histórico de la fuente de energía.
    """

    def __init__(
        self,
        settings_instance: Settings,
    ) -> None:
        """Inicializa el mánager y establece el estado inicial del suministro.

        Args:
            settings_instance (Settings): Instancia de configuraciones de la app.
            ac_supply_name (str, optional): Nombre de la interfaz AC. Defaults to "AC0".
        """
        self.settings = settings_instance
        self.logger = logging.getLogger(self.__class__.__name__)
        self.power_monitor_service = PowerMonitorService(
            settings=settings_instance,
            ac_supply_name=settings_instance.AC_SUPPLY_NAME
        )
        self.ntfy_service = NtfysService(settings=settings_instance)
        self.is_ac_connected: bool = self.power_monitor_service.read_ac_status()

    def _build_ntfy_message(
        self,
        title: str,
        event: str,
        message: str,
        priority: NTFYPriority,
        tags: str,
    ) -> WebhookPayload:
        """Organiza los datos del evento en un esquema WebhookPayload para NTFY.

        Args:
            title (str): Título principal de la notificación.
            event (str): Identificador del evento.
            message (str): Descripción o contenido del evento.
            priority (NTFYPriority): Prioridad de envío.
            tags (str): Lista de tags/emojis separados por comas.

        Returns:
            WebhookPayload: Instancia validada con el mensaje formateado.
        """
        return WebhookPayload(
            title=title,
            event=event,
            description=message,
            priority=priority,
            tags=tags,
        )

    def run(self) -> None:
        """Ejecuta el bucle principal de monitoreo continuo."""
        self.logger.info(
            f"Iniciando monitoreo de energía en: {self.power_monitor_service.sysfs_ac_path}"
        )
        self.logger.info(f"Publicando alertas en: {self.settings.NTFY_URL}")

        while True:
            try:
                current_ac_status: bool = (
                    self.power_monitor_service.read_ac_status()
                )

                if current_ac_status != self.is_ac_connected:
                    self.is_ac_connected = current_ac_status

                    if not self.is_ac_connected:
                        self.logger.info("Energía desconectada, enviando notificación.")
                        ntfy_payload = self._build_ntfy_message(
                            title="[!] ALERTA: CORTE DE ENERGIA",
                            event="SUMINISTRO DESCONECTADO",
                            message="El servidor ha perdido la alimentación de red y está operando con BATERÍA.",
                            priority=NTFYPriority.MAX,
                            tags="warning,zap",
                        )
                        self.ntfy_service.emit(payload=ntfy_payload)
                    else:
                        self.logger.info("Energía restituida, enviando notificación.")
                        ntfy_payload = self._build_ntfy_message(
                            title="[OK] RESTABLECIDO: ENERGIA AC",
                            event="SUMINISTRO RESTITUIDO",
                            message="El suministro eléctrico se ha restaurado. El servidor vuelve a cargar la batería.",
                            priority=NTFYPriority.DEFAULT,
                            tags="heavy_check_mark,electric_plug",
                        )
                        self.ntfy_service.emit(payload=ntfy_payload)

            except Exception as loop_error:
                self.logger.error(f"[Error en loop]: {loop_error}")

            time.sleep(self.settings.CHECK_INTERVAL)
