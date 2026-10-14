"""Módulo que define la clase base abstracta para los enumeradores del sistema."""
from abc import ABC, ABCMeta, abstractmethod
from enum import EnumMeta
from typing import Any


class EnumABCMeta(EnumMeta, ABCMeta):
    """
    Metaclase combinada para resolver el conflicto entre EnumMeta y ABCMeta,
    permitiendo heredar simultáneamente de Enum y ABC.
    """
    pass


class BaseEnum(ABC, metaclass=EnumABCMeta):
    """
    Clase base abstracta para centralizar la lógica común de los Enums.
    """

    @classmethod
    @abstractmethod
    def from_value(cls, value: Any) -> "BaseEnum":
        """
        Obtiene una instancia del Enum a partir de un valor dado.

        Args:
            value (Any): Valor a convertir en instancia del enum.

        Returns:
            BaseEnum: Instancia correspondiente del enum.

        Raises:
            ValueError: Si el valor suministrado no es válido.
        """
        pass

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
            cls.from_value(value)
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
