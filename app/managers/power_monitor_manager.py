import logging
import time

from app.settings import Settings
from app.enums import NTFYPriority
from app.schemas import WebhookPayload
from app.services import NtfysService, PowerMonitorService

class PowerMonitorManager:
    def __init__(
        self,
        settings_instance: Settings,
    ):
        self.settings = settings_instance
        self.logger = logging.getLogger(self.__class__.__name__)
        self.power_monitor_service = PowerMonitorService(settings=settings_instance)
        self.ntfy_service = NtfysService(settings=settings_instance)

    def _build_ntfy_message(
        self,
        title: str,
        event: str,
        message: str,
        priority: NTFYPriority,
        tags: str
    ) -> WebhookPayload:
        """Organiza los datos del evento en forma de un mensaje de NTFY Payload"""
        payload = WebhookPayload(
            title=title,
            event=event,
            description=message,
            priority=priority,
            tags=tags
        )
        return payload

    def run(self) -> None:
        """Ejecuta el bucle principal de monitoreo continuo."""
        self.logger.info(f"Iniciando monitoreo de energía en: {self.settings.SUPPLY_PATH}")
        self.logger.info(f"Publicando alertas en: {self.settings.NTFY_URL}")

        while True:
            try:
                current_ac_status: bool = self.power_monitor_service._read_ac_status()

                # Detectamos un cambio de estado en la alimentación
                if current_ac_status != self.is_ac_connected:
                    self.is_ac_connected = current_ac_status

                    if not self.is_ac_connected:
                        ntfy_payload = self._build_ntfy_message(
                            title="🔴 CORTE DE ENERGÍA DETECTADO",
                            event="SUMINISTRO DESCONECTADO",
                            message="El servidor ha perdido la alimentación de red y está operando con BATERÍA.",
                            priority=NTFYPriority.MAX,
                            tags="warning,zap",
                        )
                        self.ntfy_service.emit(payload=ntfy_payload)
                    else:
                        ntfy_payload = self._build_ntfy_message(
                            title="🟢 ENERGÍA RESTABLECIDA",
                            event="SUMINISTRO RESTITUIDO",
                            message="El suministro eléctrico se ha restaurado. El servidor vuelve a cargar la batería.",
                            priority=NTFYPriority.DEFAULT,
                            tags="heavy_check_mark,electric_plug",
                        )
                        self.ntfy_service.emit(payload=ntfy_payload)

            except Exception as loop_error:
                self.logger.error(f"[Error en loop]: {loop_error}")

            time.sleep(self.settings.CHECK_INTERVAL)
