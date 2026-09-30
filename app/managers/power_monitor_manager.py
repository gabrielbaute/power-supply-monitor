import asyncio
import logging
from pydantic import HttpUrl
from httpx import AsyncClient
from typing import Any, Dict, Optional
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession

from app.settings import Settings
from app.enums import NTFYPriority, EventType
from app.schemas import NTFYPayload, ElectricEventCreate
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

        # Estado del debounce
        self._pending_status: Optional[bool] = None
        self._pending_count: int = 0
        self._pending_since: Optional[datetime] = None

        # Anti-spam de fluctuaciones
        self._last_fluctuation_notification: Optional[datetime] = None

    def _build_event_register(
        self,
        event_type: EventType,
        start_timestamp: Optional[datetime] = None,
        end_timestamp: Optional[datetime] = None,
    ) -> ElectricEventCreate:
        """
        Genera el reporte de evento eléctrico para la base de datos.

        Args:
            event_type (EventType): Tipo de evento (CORTE, FLUCTUACION, ...).
            start_timestamp (Optional[datetime]): Inicio del evento. Por defecto, ahora en UTC.
            end_timestamp (Optional[datetime]): Fin del evento (para fluctuaciones cerradas).

        Return:
            ElectricEventCreate: esquema de creación de registro de un evento eléctrico.
        """
        return ElectricEventCreate(
            start_timestamp=start_timestamp or datetime.now(UTC),
            end_timestamp=end_timestamp,
            latitude=self.settings.LATITUDE,
            longitude=self.settings.LONGITUDE,
            event_type=event_type
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
        """Construye un objeto NTFYPayload con los argumentos proporcionados."""
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

    # ------------------------------------------------------------------
    # Handlers de eventos
    # ------------------------------------------------------------------

    async def _handle_power_lost(self) -> None:
        """Maneja la transición confirmada a estado de corte: registra el evento y notifica."""
        self.logger.info("Energía desconectada, enviando notificación.")
        ntfy_payload = self._build_ntfy_message(
            title="ALERTA: CORTE DE ENERGIA",
            event="SUMINISTRO DESCONECTADO",
            description="El servidor ha perdido la alimentación de red y está operando con BATERÍA.",
            priority=NTFYPriority.MAX,
            tags="warning,zap",
        )
        event_register = self._build_event_register(event_type=EventType.CORTE)
        await self.electric_event_service.register_event(event_data=event_register)
        await self.ntfy_service.emit(payload=ntfy_payload)
        await self.ntfy_service.close()

    async def _handle_power_restored(self) -> None:
        """Maneja la transición confirmada a energía restablecida: cierra el evento y notifica."""
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

    async def _handle_power_fluctuation(self, started_at: datetime) -> None:
        """
        Maneja una inestabilidad que se resolvió antes de confirmarse como corte:
        registra el evento como FLUCTUACION y notifica (con cooldown anti-spam).
        """
        ended_at = datetime.now(UTC)
        duration = ended_at - started_at
        self.logger.info(
            f"Fluctuación detectada: {duration} de inestabilidad. Se registra en la DB."
        )

        event_register = self._build_event_register(
            event_type=EventType.FLUCTUACION,
            start_timestamp=started_at,
            end_timestamp=ended_at,
        )
        await self.electric_event_service.register_event(event_data=event_register)

        # Cooldown: si el enchufe está muy mal, no queremos una notificación
        # cada 15 segundos. La DB siempre registra todo; la notificación, no.
        now = datetime.now(UTC)
        if (
            self._last_fluctuation_notification is not None
            and (now - self._last_fluctuation_notification).total_seconds()
                < self.settings.FLUCTUATION_NOTIFY_COOLDOWN_SECONDS
        ):
            self.logger.debug("Notificación de fluctuación suprimida por cooldown.")
            return

        self._last_fluctuation_notification = now
        ntfy_payload = self._build_ntfy_message(
            title="AVISO: INESTABILIDAD EN LA RED",
            event="FLUCTUACION DE SUMINISTRO",
            description=(
                f"Se detectaron {duration} de inestabilidad en la red eléctrica "
                "que se resolvieron sin corte. Posible falso contacto en el cable o enchufe."
            ),
            priority=NTFYPriority.LOW,
            tags="warning,electric_plug",
        )
        await self.ntfy_service.emit(payload=ntfy_payload)
        await self.ntfy_service.close()

    # ------------------------------------------------------------------
    # Arranque
    # ------------------------------------------------------------------

    async def _reconcile_startup_state(self) -> None:
        """
        Al arrancar con energía presente, cierra cualquier evento abierto que haya
        quedado huérfano (el servidor se apagó durante el corte y volvió con la
        luz ya restablecida).
        """
        if not self.is_ac_connected:
            return

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

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Ejecuta el bucle principal de monitoreo continuo."""
        self.logger.info(
            f"Iniciando monitoreo de energía en: {self.power_monitor_service.sysfs_ac_path}"
        )
        self.logger.info(f"Publicando alertas en: {self.settings.NTFY_URL}")

        await self._reconcile_startup_state()

        while True:
            try:
                current_ac_status: bool = self.power_monitor_service.read_ac_status()

                if current_ac_status != self.is_ac_connected:
                    # Estado inestable: iniciamos o continuamos el conteo de confirmación.
                    if self._pending_status != current_ac_status:
                        self._pending_status = current_ac_status
                        self._pending_count = 0
                        self._pending_since = datetime.now(UTC)

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
                        self._pending_since = None

                        if not self.is_ac_connected:
                            await self._handle_power_lost()
                        else:
                            await self._handle_power_restored()

                elif self._pending_status is not None:
                    # La inestabilidad se resolvió antes de confirmarse → fluctuación.
                    fluctuation_start = self._pending_since or datetime.now(UTC)
                    self._pending_status = None
                    self._pending_count = 0
                    self._pending_since = None
                    await self._handle_power_fluctuation(started_at=fluctuation_start)

            except Exception:
                self.logger.exception("[Error en loop]")

            await asyncio.sleep(self.settings.CHECK_INTERVAL)
