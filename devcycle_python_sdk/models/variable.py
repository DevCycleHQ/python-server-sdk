from dataclasses import dataclass
from typing import Optional, Any


class TypeEnum:
    BOOLEAN = "Boolean"
    STRING = "String"
    NUMBER = "Number"
    JSON = "JSON"


def determine_variable_type(value: Any) -> str:
    if isinstance(value, bool):
        return TypeEnum.BOOLEAN
    elif isinstance(value, str):
        return TypeEnum.STRING
    elif isinstance(value, (int, float)):
        return TypeEnum.NUMBER
    elif isinstance(value, dict):
        return TypeEnum.JSON
    else:
        raise TypeError(f"Unsupported type: {type(value)}")


@dataclass(eq=False, order=False)
class Variable:
    _id: str
    key: str
    type: str
    value: Optional[Any] = None
    isDefaulted: bool = False
    defaultValue: Optional[Any] = None
    evalReason: Optional[str] = None

    def to_json(self):
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None
        }

    @staticmethod
    def create_default_variable(key: str, default_value: Any) -> "Variable":
        var_type = determine_variable_type(default_value)
        return Variable(_id="", key=key, type=var_type, value=default_value, isDefaulted=True)
