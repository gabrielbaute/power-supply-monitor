"""Módulo para la representación de los roles de usuario existentes."""
from enum import StrEnum
from app.enums.base_enum import BaseEnum

class UserRole(BaseEnum, StrEnum):
    """
    Tipos de usuarios

    Attributes:
        ADMIN (str): "ADMIN", usuario administrador.
        USER (str): "USER", usuario convencional sin privilegios.
    """
    ADMIN = "ADMIN"
    USER = "USER"

    @classmethod
    def from_value(cls, value: str) -> 'UserRole':
        """
        Obtiene una instancia de UserRole a partir de una cadena de texto.

        Args:
            value (str): Identificador o nombre del rol de usuario.

        Returns:
            UserRole: La instancia correspondiente del Enum.

        Raises:
            ValueError: Si el valor suministrado no coincide con un rol de usuario válido.
        """
        if isinstance(value, str):
            clean_str = value.strip().lower()

            name_mapping = {name.lower(): cls[name] for name in cls.enum_dict()}

            if clean_str in name_mapping:
                return name_mapping[clean_str]

        raise ValueError(
            f"'{value}' no es un valor de rol válido para UserRole."
        )
