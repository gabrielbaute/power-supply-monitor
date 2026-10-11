import asyncio
import base64
import logging
from typing import Dict, Optional
from httpx import AsyncClient, HTTPError

from app.schemas import NTFYPayload
from app.settings import Settings

class NtfysService:
    """Servicio para emitir notificaciones asíncronas a través de NTFY."""

    def __init__(
        self,
        settings: Settings,
        client: Optional[AsyncClient] = None
    ) -> None:
        """
        Inicializa el servicio NTFY con la configuración y un cliente HTTP asíncrono.

        Args:
            settings (Settings): Instancia con la configuración general de la aplicación.
            client (Optional[httpx.AsyncClient]): Cliente asíncrono de HTTPX reutilizable.
        """
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self._client = client
        self._owns_client = client is None
        self._client_lock = asyncio.Lock()

    async def _get_client_locked(self) -> AsyncClient:
        """Obtiene o crea un cliente HTTPX asíncrono con ``_client_lock`` adquirido.

        Returns:
            AsyncClient: Cliente de red asíncrono.
        """
        if self._client is None or getattr(self._client, "is_closed", False):
            self._client = AsyncClient(timeout=10.0)
            self._owns_client = True
        return self._client

    def _generate_auth_header(self) -> Optional[dict[str, str]]:
        """
        Construye el token de autenticación a partir del usuario y contraseña, o del token.

        Return:
            dict[str, str]: header de autenticación.
        """
        if self.settings.NTFY_USER and self.settings.NTFY_PASSWORD:
            string_code: str = f"{self.settings.NTFY_USER}:{self.settings.NTFY_PASSWORD}"
            string_bytes = string_code.encode("utf-8")
            base64_bytes = base64.b64encode(string_bytes)
            base64_string = base64_bytes.decode("utf-8")
            return {"Authorization": f"Basic {base64_string}"}

        if self.settings.NTFY_TOKEN:
            return {"Authorization": f"Bearer {self.settings.NTFY_TOKEN}",}

        else:
            return None

    def _format_message(self, payload: NTFYPayload) -> str:
        """
        Formatea el cuerpo del mensaje priorizando el contenido principal y firmando al final.

        Args:
            payload (NTFYPayload): Estructura de datos de la notificación.

        Returns:
            str: Mensaje formateado en Markdown.
        """
        body_parts = [payload.description]
        footer = f"— *{self.settings.APP_NAME}* `v{self.settings.APP_VERSION}`"
        body_parts.append(footer)

        return "\n\n".join(body_parts) #type: ignore

    def _format_headers(self, payload: NTFYPayload) -> Dict[str, str]:
        """
        Genera los encabezados HTTP según las especificaciones de NTFY.

        Args:
            payload (NTFYPayload): Contenido de la notificación.

        Returns:
            Dict[str, str]: Diccionario con las cabeceras formateadas.
        """
        headers: Dict[str, str] = {
            "Priority": str(payload.priority.value),
            "Tags": payload.tags if payload.tags else "robot",
            "Markdown": "yes",
        }

        # Agregamos header de autenticación
        if self._generate_auth_header() is not None:
            auth_header: dict[str, str] =  self._generate_auth_header() #type: ignore
            headers.update(auth_header)

        # El título en la cabecera es independiente del cuerpo
        if payload.title:
            headers["Title"] = payload.title
        else:
            headers["Title"] = f"{self.settings.APP_NAME} - {payload.event}"

        if payload.click:
            headers["Click"] = payload.click
        elif payload.url:
            headers["Click"] = payload.url

        if payload.icon:
            headers["Icon"] = str(payload.icon)

        return headers

    async def emit(
        self,
        payload: NTFYPayload,
        topic: Optional[str] = None
    ) -> Optional[int]:
        """Emite una notificación a NTFY de forma asíncrona.

        Args:
            payload (NTFYPayload): Contenido estructurado de la notificación.
            topic (Optional[str]): Nombre del tópico de ntfy al que se enviará la notificación.

        Returns:
            Optional[int]: Código de estado HTTP retornado por el servidor NTFY.
        """
        message = self._format_message(payload)
        headers = self._format_headers(payload)

        url = (
            f"{self.settings.NTFY_URL.strip("/")}/{topic}" if topic
            else f"{self.settings.NTFY_URL.strip("/")}/{self.settings.NTFY_TOPIC}"
        )

        try:
            async with self._client_lock:
                client = await self._get_client_locked()
                response = await client.post(
                    url,
                    content=message.encode("utf-8"),
                    headers=headers,
                )
                response.raise_for_status()
            self.logger.debug(
                f"Notificación NTFY enviada exitosamente. Status code: {response.status_code}"
            )
            return response.status_code
        except HTTPError as e:
            self.logger.exception(f"Error al enviar notificación NTFY: {e}")
            return None

    async def close(self) -> None:
        """
        Cierra el cliente HTTPX asíncrono si está activo.
        """
        async with self._client_lock:
            if self._owns_client and self._client and not self._client.is_closed:
                await self._client.aclose()
