"""Módulo para la representación de los tipos de fallo eléctrico."""
from enum import StrEnum
from app.enums.base_enum import BaseEnum


class EventType(StrEnum, BaseEnum):
    """
    Tipo de evento eléctrico.

    Attributes:
        CORTE (str): Corte eléctrico.
        CAIDA_TENSION (str): Caída de la tensión eléctrica en la red.
        FLUCTUACION (str): Fluctuación o pico en la red eléctrica.
    """
    CORTE = "CORTE"
    CAIDA_TENSION = "CAIDA_TENSION"
    FLUCTUACION = "FLUCTUACION"

    @classmethod
    def from_value(cls, value: str) -> 'EventType':
        """
        Obtiene una instancia de EventType a partir de una cadena de texto.

        Args:
            value (str): Identificador o nombre del evento.

        Returns:
            EventType: La instancia correspondiente del Enum.

        Raises:
            ValueError: Si el valor suministrado no coincide con un tipo de evento válido.
        """
        if isinstance(value, str):
            clean_str = value.strip().lower()

            name_mapping: dict[str, EventType] = {
                "corte": cls.CORTE,
                "caida_tension": cls.CAIDA_TENSION,
                "fluctuacion": cls.FLUCTUACION
            }

            if clean_str in name_mapping:
                return name_mapping[clean_str]

        raise ValueError(
            f"'{value}' no es un valor de evento válido para EventType."
        )
