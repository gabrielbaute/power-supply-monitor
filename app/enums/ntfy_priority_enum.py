from enum import Enum

class NTFYPriority(Enum):
    """
    Enum for NTFY priority levels.

    Attributes:
        MAX (str): Represents the maximum priority.
        HIGH (str): Represents the high priority.
        DEFAULT (str): Represents the default priority.
        LOW (str): Represents the low priority.
        MIN (str): Represents the minimum priority.
    """
    MAX = 'max'
    HIGH = 'high'
    DEFAULT = 'default'
    LOW = 'low'
    MIN = 'min'

    def __str__(self):
        return self.value

    @classmethod
    def has_value(cls, value: str) -> bool:
        return any(value == item.value for item in cls)

    @classmethod
    def list(cls) -> list:
        return list(map(lambda c: c.value, cls))
