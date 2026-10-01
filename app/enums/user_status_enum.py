"""Módulo para la representación de los estados de usuario posibles."""
from enum import StrEnum

class UserStatus(StrEnum):
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

            name_mapping: dict[str, UserStatus] = {
                "active": cls.ACTIVE,
                "inactive": cls.INACTIVE,
                "block": cls.BLOCK
            }

            if clean_str in name_mapping:
                return name_mapping[clean_str]

        raise ValueError(
            f"'{value}' no es un valor de estatus válido para UserStatus."
        )

    @classmethod
    def has_value(cls, value: str) -> bool:
        """
        Identifica si una cadena se corresponde con un valor de estatus o estado de usuario.

        Args:
            value (str): Valor de texto a validar.

        Returns:
            bool: True si el valor es un estatus de usuario válido, False en caso contrario.
        """
        try:
            cls.from_value(value)
            return True
        except ValueError:
            return False

    @classmethod
    def to_list(cls) -> list[str]:
        """
        Obtiene la lista completa de valores de estatus de usuario.

        Returns:
            list[str]: Lista con los identificadores de estatus de usuario.
        """
        return [item.value for item in cls]
