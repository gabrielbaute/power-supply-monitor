"""Módulo que define la clase mixin base para los enumeradores del sistema."""
from typing import Any

class BaseEnum:
    """
    Clase base mixin para centralizar la lógica común de los Enums
    sin generar conflictos de metaclases con EnumMeta.
    """

    @classmethod
    def has_value(cls, value: Any) -> bool:
        """
        Identifica si un valor se corresponde con un elemento válido del Enum.

        Args:
            value (Any): Valor a validar.

        Returns:
            bool: True si el valor es válido, False en caso contrario.
        """
        try:
            cls.from_value(value)  # type: ignore[attr-defined]
            return True
        except ValueError:
            return False

    @classmethod
    def to_list(cls) -> list[Any]:
        """
        Obtiene la lista completa de valores del Enum.

        Returns:
            list[Any]: Lista con los valores de los elementos del enum.
        """
        return [item.value for item in cls]

    @classmethod
    def enum_dict(cls) -> dict[str, Any]:
        """
        Obtiene un diccionario que mapea los nombres de los elementos con sus valores.

        Returns:
            dict[str, Any]: Diccionario con la estructura {nombre: valor}.
        """
        return {item.name: item.value for item in cls}
