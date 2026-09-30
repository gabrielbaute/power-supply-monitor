import logging
from typing import Dict, Any

from app.mail import SMTPClient, MailBuilder
from app.settings.app_settings import Settings

class MailService:
    """
    Servicio orquestador de alto nivel para el envío de correos.

    Attributes:
        client (SMTPClient): Instancia del cliente SMTP
        builder (MailBuilder): Constructor de emails a partir del motor de plantillas de Jinja2
        settings (Settings): Instancia de configuración de la app.
        logger (logging): Logger del módulo.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Inyecta las dependencias necesarias e inicializa el servicio de Email.

        Args:
            settings (Settings): Configuración global.
        """
        self.client = SMTPClient(settings=settings)
        self.builder = MailBuilder(settings=settings)
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)

    def send_templated_email(
            self,
            recipient: str,
            subject: str,
            template: str,
            context: Dict[str, Any]
        ) -> None:
        """Renderiza una plantilla y la envía.

        Args:
            recipient (str): Email destino.
            subject (str): Asunto del correo.
            template (str): Nombre del archivo .html en /templates.
            context (Dict[str, Any]): Variables para la plantilla.
        """
        # 1. Construir el mensaje
        message = self.builder.create_message(
            sender=self.settings.MAIL_USERNAME,
            recipient=recipient,
            subject=subject,
            template_name=template,
            context=context
        )
        self.logger.info(f"Sending email to {recipient}. Subject: {subject}.")
        # 2. Enviar usando el context manager del cliente
        with self.client as active_client:
            active_client.send_mail(message)
