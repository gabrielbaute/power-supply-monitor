"""Módulo para la representación de los niveles de prioridad de notificación para ntfy."""
from enum import IntEnum
from typing import Union
from app.enums.base_enum import BaseEnum

class NTFYPriority(BaseEnum, IntEnum):
    """
    Representa los niveles de prioridad de notificación para ntfy.

    Attributes:
        MAX (int): Prioridad máxima / urgente (ID: 5).
        HIGH (int): Prioridad alta (ID: 4).
        DEFAULT (int): Prioridad por defecto (ID: 3).
        LOW (int): Prioridad baja (ID: 2).
        MIN (int): Prioridad mínima (ID: 1).
    """
    MAX = 5
    HIGH = 4
    DEFAULT = 3
    LOW = 2
    MIN = 1

    @classmethod
    def from_value(cls, value: Union[int, str]) -> "NTFYPriority":
        """
        Obtiene una instancia de NTFYPriority a partir de un entero o texto.

        Args:
            value (Union[int, str]): Identificador numérico o nombre de la prioridad.

        Returns:
            NTFYPriority: La instancia correspondiente del Enum.

        Raises:
            ValueError: Si el valor suministrado no coincide con ninguna prioridad.
        """
        if isinstance(value, int):
            return cls(value)

        if isinstance(value, str):
            clean_str = value.strip().lower()

            name_mapping = {name.lower(): cls[name] for name in cls.enum_dict()}

            if clean_str in name_mapping:
                return name_mapping[clean_str]

            if clean_str.isdigit():
                return cls(int(clean_str))

        raise ValueError(
            f"'{value}' no es un valor de prioridad válido para ntfy. "
            f"Valores enteros permitidos: {cls.to_list()} o cadenas ('max', 'urgent', 'high', 'default', 'low', 'min')."
        )
