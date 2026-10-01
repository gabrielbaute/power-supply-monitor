"""Módulo para la representación de los roles de usuario existentes."""
from enum import StrEnum

class UserRole(StrEnum):
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

            name_mapping: dict[str, UserRole] = {
                "admin": cls.ADMIN,
                "user": cls.USER,
            }

            if clean_str in name_mapping:
                return name_mapping[clean_str]

        raise ValueError(
            f"'{value}' no es un valor de rol válido para UserRole. "
        )

    @classmethod
    def has_value(cls, value: str) -> bool:
        """
        Identifica si una cadena se corresponde con un valor de rol de usuario.

        Args:
            value (str): Valor de texto a validar.

        Returns:
            bool: True si el valor es un rol de usuario válido, False en caso contrario.
        """
        try:
            cls.from_value(value)
            return True
        except ValueError:
            return False

    @classmethod
    def to_list(cls) -> list[str]:
        """
        Obtiene la lista completa de valores de roles de usuario.

        Returns:
            list[str]: Lista con los identificadores de rol de usuario.
        """
        return [item.value for item in cls]
