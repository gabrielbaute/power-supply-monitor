import logging
from typing import Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, Template

from app.settings.app_settings import Settings
from app.errors import TemplateMailNotFound, BuildMessageError

class MailBuilder:
    """
    Módulo para construir mensajes MIME utilizando plantillas Jinja2.
    """
    def __init__(self, settings: Settings):
        """
        Configura el entorno de plantillas.

        Args:
            template_dir (Path): Ruta al directorio de plantillas.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.env = Environment(loader=FileSystemLoader(str(settings.MAIL_TEMPLATES_DIR)))

    def _get_template(self, template_name: str) -> Template:
        """
        Busca y carga la plantilla de email.

        Args:
            template_name (str): Nombre de la plantilla de email.

        Returns:
            Template: Plantilla de email solicitada.

        Raises:
            TemplateMailNotFound: En caso de que no se encuentre la plantilla o no se pueda cargar.
        """
        try:
            template = self.env.get_template(template_name)
            return template
        except Exception as e:
            self.logger.error(f"Plantilla de email {template_name} no encontrada.")
            raise TemplateMailNotFound(
                message=f"Error al cargar la plantilla {template_name}.",
                details={"Detalle de error:": {e}}
            ) from e

    def create_message(
            self,
            sender: str,
            recipient: str,
            subject: str,
            template_name: str,
            context: Dict[str, Any]
        ) -> MIMEMultipart:
        """
        Crea un objeto MIMEMultipart renderizando una plantilla.

        Args:
            sender (str): Email del remitente.
            recipient (str): Email del destinatario.
            subject (str): Asunto del correo.
            template_name (str): Nombre del archivo de plantilla.
            context (Dict[str, Any]): Datos para renderizar en la plantilla.

        Returns:
            MIMEMultipart: Objeto de mensaje listo para ser enviado.
        """
        self.logger.debug(f"Creando mensaje para {recipient} con asunto {subject}")
        try:
            message = MIMEMultipart("alternative")
            message["From"] = sender
            message["To"] = recipient
            message["Subject"] = subject
            template = self._get_template(template_name=template_name)

            html_content = template.render(context)

            message.attach(MIMEText(html_content, "html"))
            return message
        except Exception as e:
            self.logger.error(f"Error al construir el mensaje: {e}")
            raise BuildMessageError(
                message=f"Error al construir el mensaje de correo para {recipient}",
                details={"Detalle de error:": {e}}
            ) from e
