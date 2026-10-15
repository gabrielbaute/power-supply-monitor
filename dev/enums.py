import json
from typing import Any
from app.enums import NTFYPriority, EventType, UserRole, UserStatus

def main() -> None:
    ntfy_dict_values: dict[str, Any] = NTFYPriority.enum_dict()
    events_dict_values: dict[str, Any] = EventType.enum_dict()
    roles_dict_values: dict[str, Any] = UserRole.enum_dict()
    status_dict_values: dict[str, Any] = UserStatus.enum_dict()

    print(json.dumps(ntfy_dict_values, indent=2))
    print(json.dumps(events_dict_values, indent=2))
    print(json.dumps(roles_dict_values, indent=2))
    print(json.dumps(status_dict_values, indent=2))

def test_values() -> None:
    testing_value = "corte"
    enum_value = EventType.from_value(value=testing_value)
    print(f"Valor: {enum_value}, tipo: {type(enum_value)}")

if __name__ == "__main__":
    main()
    test_values()
