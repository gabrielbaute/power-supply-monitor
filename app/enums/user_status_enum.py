"""Módulo para la representación de los estados de usuario posibles."""
from enum import StrEnum
from app.enums.base_enum import BaseEnum

class UserStatus(BaseEnum, StrEnum):
    """
    Estatus o estado del usuario

    Attributes:
        ACTIVE (str): "ACTIVE", usuario activo.
        INACTIVE (str): "INACTIVE", usuario desactivado o inactivo.
        BLOCK (str): "BLOCK", usuario bloqueado.
    """
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCK = "BLOCK"

    @classmethod
    def from_value(cls, value: str) -> 'UserStatus':
        """
        Obtiene una instancia de UserStatus a partir de una cadena de texto.

        Args:
            value (str): Identificador o nombre del estatus de usuario.

        Returns:
            UserStatus: La instancia correspondiente del Enum.

        Raises:
            ValueError: Si el valor suministrado no coincide con un estatus de usuario válido.
        """
        if isinstance(value, str):
            clean_str = value.strip().lower()

            name_mapping = {name.lower(): cls[name] for name in cls.enum_dict()}

            if clean_str in name_mapping:
                return name_mapping[clean_str]

        raise ValueError(
            f"'{value}' no es un valor de estatus válido para UserStatus."
        )
