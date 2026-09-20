import asyncio
import logging
from uuid import uuid4
from pydantic import HttpUrl
from httpx import AsyncClient
from typing import Any, Dict, Optional
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession

from app.settings import Settings
from app.enums import NTFYPriority, EventType
from app.schemas import NTFYPayload, ElectricEventCreate, ElectricEventResponse
from app.services import ElectricEventService, NtfysService, PowerMonitorService

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
        database_session: AsyncSession,
        settings_instance: Settings,
    ) -> None:
        """
        Inicializa el mánager y establece el estado inicial del suministro.

        Args:
            settings_instance (Settings): Instancia de configuraciones de la app.
        """
        self.settings = settings_instance
        self._client = AsyncClient()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.power_monitor_service = PowerMonitorService(
            settings=settings_instance,
            ac_supply_name=settings_instance.AC_SUPPLY_NAME
        )
        self.ntfy_service = NtfysService(
            settings=settings_instance,
            client=self._client
        )
        self.electric_event_service = ElectricEventService(database_session=database_session)
        self.is_ac_connected: bool = self.power_monitor_service.read_ac_status()

    def _build_event_register(self, ) -> ElectricEventCreate:
        """
        Genera el reporte de evento eléctrico para la base de datos.

        Return:
            ElectricEventCreate: esquema de creación de registro de un evento eléctrico
        """
        return ElectricEventCreate(
            start_timestamp=datetime.now(UTC),
            latitude=self.settings.LATITUDE,
            longitude=self.settings.LONGITUDE,
            event_type=EventType.CORTE
        )

    def _build_ntfy_message(
        self,
        event: str,
        description: Optional[str] = None,
        title: Optional[str] = None,
        priority: NTFYPriority = NTFYPriority.DEFAULT,
        tags: Optional[str] = None,
        click: Optional[str] = None,
        icon: Optional[HttpUrl] = None,
        url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> NTFYPayload:
        """Construye un objeto NTFYPayload con los argumentos proporcionados.

        Args:
            event (str): Nombre del evento.
            description (str): Descripción o cuerpo del mensaje.
            title (Optional[str]): Título opcional de la notificación.
            priority (NTFYPriority): Prioridad de la notificación.
            tags (Optional[str]): Etiquetas separadas por comas o emojis.
            click (Optional[str]): Enlace al hacer clic.
            icon (Optional[HttpUrl]): URL del icono/logo de la aplicación.
            url (Optional[str]): URL opcional adjunta.
            data (Optional[Dict[str, Any]]): Metadatos adicionales.

        Returns:
            NTFYPayload: Instancia formateada del esquema de notificación.
        """
        return NTFYPayload(
            event=event,
            description=description,
            title=title,
            priority=priority,
            tags=tags,
            click=click,
            icon=icon,
            url=url,
            data=data,
        )

    async def run(self) -> None:
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
                            title="ALERTA: CORTE DE ENERGIA",
                            event="SUMINISTRO DESCONECTADO",
                            description="El servidor ha perdido la alimentación de red y está operando con BATERÍA.",
                            priority=NTFYPriority.MAX,
                            tags="warning,zap",
                        )
                        event_register = self._build_event_register()
                        await self.electric_event_service.register_event(event_data=event_register)
                        await self.ntfy_service.emit(payload=ntfy_payload)
                        await self.ntfy_service.close()
                    else:
                        self.logger.info("Energía restituida, enviando notificación.")
                        closed_event = await self.electric_event_service.close_last_open_event()
                        if closed_event:
                            duration = closed_event.end_timestamp - closed_event.start_timestamp # type: ignore
                            self.logger.info(
                                f"Evento {closed_event.id} cerrado. Duración: {duration}."
                            )

                        ntfy_payload = self._build_ntfy_message(
                            title="RESTABLECIDO: ENERGIA AC",
                            event="SUMINISTRO RESTITUIDO",
                            description="El suministro eléctrico se ha restaurado. El servidor vuelve a cargar la batería.",
                            priority=NTFYPriority.DEFAULT,
                            tags="heavy_check_mark,electric_plug",
                        )
                        await self.ntfy_service.emit(payload=ntfy_payload)
                        await self.ntfy_service.close()

            except Exception as loop_error:
                self.logger.error(f"[Error en loop]: {loop_error}")

            await asyncio.sleep(self.settings.CHECK_INTERVAL)
