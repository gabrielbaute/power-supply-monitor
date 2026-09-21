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
        self._pending_status: Optional[bool] = None
        self._pending_count: int = 0

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

        # --- Reconciliación post-reinicio ---
        # Si hay energía pero quedó un evento abierto en la DB, el servidor
        # se apagó durante el corte y volvió con la electricidad ya restablecida.
        if self.is_ac_connected:
            closed_event = await self.electric_event_service.close_last_open_event()
            if closed_event:
                duration = closed_event.end_timestamp - closed_event.start_timestamp  # type: ignore
                self.logger.info(
                    f"Evento {closed_event.id} cerrado tras reinicio. Duración estimada: {duration}."
                )
                ntfy_payload = self._build_ntfy_message(
                    title="RESTABLECIDO: ENERGIA AC",
                    event="SUMINISTRO RESTITUIDO",
                    description=(
                        f"El servidor se reinició tras un corte de energía. "
                        f"Duración estimada: {duration}. El suministro está activo."
                    ),
                    priority=NTFYPriority.DEFAULT,
                    tags="heavy_check_mark,electric_plug",
                )
                await self.ntfy_service.emit(payload=ntfy_payload)
                await self.ntfy_service.close()

        # --- Bucle principal con debounce ---
        while True:
            try:
                current_ac_status: bool = (
                    self.power_monitor_service.read_ac_status()
                )

                if current_ac_status != self.is_ac_connected:
                    # Estado inestable: iniciamos o continuamos el conteo de confirmación.
                    if self._pending_status != current_ac_status:
                        self._pending_status = current_ac_status
                        self._pending_count = 0

                    self._pending_count += 1
                    self.logger.debug(
                        f"Estado inestable: AC={'conectado' if current_ac_status else 'desconectado'} "
                        f"({self._pending_count}/{self.settings.CONFIRMATION_READS})"
                    )

                    if self._pending_count >= self.settings.CONFIRMATION_READS:
                        # Cambio de estado confirmado.
                        self.is_ac_connected = current_ac_status
                        self._pending_status = None
                        self._pending_count = 0

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
                            duration: Any = ""
                            if closed_event:
                                duration = closed_event.end_timestamp - closed_event.start_timestamp  # type: ignore
                                self.logger.info(
                                    f"Evento {closed_event.id} cerrado. Duración: {duration}."
                                )

                            ntfy_payload = self._build_ntfy_message(
                                title="RESTABLECIDO: ENERGIA AC",
                                event="SUMINISTRO RESTITUIDO",
                                description=(
                                    f"El suministro eléctrico se ha restaurado tras {duration}. "
                                    "El servidor vuelve a cargar la batería."
                                ) if closed_event else "El suministro eléctrico se ha restaurado.",
                                priority=NTFYPriority.DEFAULT,
                                tags="heavy_check_mark,electric_plug",
                            )
                            await self.ntfy_service.emit(payload=ntfy_payload)
                            await self.ntfy_service.close()

                elif self._pending_status is not None:
                    # El estado volvió a la normalidad antes de confirmarse: falso contacto.
                    self.logger.debug(
                        f"Falso contacto descartado tras {self._pending_count} lectura(s)."
                    )
                    self._pending_status = None
                    self._pending_count = 0

            except Exception as loop_error:
                self.logger.error(f"[Error en loop]: {loop_error}")

            await asyncio.sleep(self.settings.CHECK_INTERVAL)
