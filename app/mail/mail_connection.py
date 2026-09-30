import ssl
import logging
from typing import Optional
from smtplib import SMTP, SMTP_SSL, SMTPException

from app.settings.app_settings import Settings
from app.errors import SMTPConnectionError, SendMailError

class SMTPClient:
    """Maneja la conexión y autenticación con el servidor SMTP."""

    def __init__(self, settings: Settings) -> None:
        """Inicializa los parámetros de conexión.

        Args:
            settings (AppSettings): Objeto de configuración con los parámetros del servidor.
        """
        self.settings = settings
        self.server: Optional[SMTP] = None
        self._context = ssl.create_default_context()
        self.logger = logging.getLogger(self.__class__.__name__)

    def __enter__(self) -> "SMTPClient":
        """
        Permite el uso de 'with SMTPClient(...) as client'.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Asegura el cierre de la conexión al salir del bloque 'with'."""
        self.logger.debug("Finalizando conexión SMTP")
        self.disconnect()

    def connect(self) -> None:
        """
        Establece la conexión física y lógica con el servidor SMTP.

        Aquí es donde 'self.server' deja de ser None para convertirse en el objeto de conexión.
        """
        try:
            if self.settings.MAIL_USE_SSL:
                # Conexión implícita SSL (Puerto 465)
                self.server = SMTP_SSL(
                    self.settings.MAIL_HOST,
                    self.settings.MAIL_PORT,
                    context=self._context
                )
            else:
                # Conexión estándar o STARTTLS (Puerto 587 o 25)
                self.server = SMTP(
                    self.settings.MAIL_HOST,
                    self.settings.MAIL_PORT
                )
                if self.settings.MAIL_USE_TLS:
                    self.server.starttls(context=self._context)

            # Autenticación
            if self.settings.MAIL_USERNAME and self.settings.MAIL_PASSWORD:
                self.server.login(
                    self.settings.MAIL_USERNAME,
                    self.settings.MAIL_PASSWORD
                )
        except SMTPException as e:
            self.logger.exception("Error al conectar al servidor SMTP.")
            raise SMTPConnectionError(
                message=f"Error al conectarse al servidor SMTP {self.settings.MAIL_HOST}",
                details={"detail": str(e)}
            ) from e

    def send_mail(self, message) -> None:
        """
        Envía un mensaje ya construido.

        Args:
            message: Objeto email.message.Message (o MIMEMultipart).

        Returns:
            None
        Raises:
            SMTPConnectionError: Si no hay una conexión activa del servidor.
            SendMailError: Si el envío del email falla.
        """
        try:
            if not self.server:
                raise SMTPConnectionError(
                    message="El servidor no está conectado.",
                    details={"Detalle de error:": {"Llama a connect() primero."}}
                )
            self.logger.debug(f"Enviando correo a {message['To']}")
            self.server.send_message(message)
        except SMTPException as e:
            self.logger.exception("Error al enviar el correo.")
            raise SendMailError(
                message="Error al enviar el correo",
                details={"detail": str(e)}
            ) from e

    def disconnect(self) -> None:
        """
        Cierra la conexión de forma segura.
        """
        if self.server:
            self.logger.debug("Cerrando conexión SMTP")
            self.server.quit()
            self.server = None
