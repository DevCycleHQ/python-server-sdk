# ruff: noqa: N815
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


@dataclass(order=False)
class Variable:
    _id: Optional[str]
    key: str
    type: str
    value: Any = None
    isDefaulted: Optional[bool] = False
    defaultValue: Any = None
    evalReason: Optional[str] = None

    def to_json(self):
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None
        }

    @classmethod
    def from_json(cls, data: dict) -> "Variable":
        return cls(
            _id=data["_id"],
            key=data["key"],
            type=data["type"],
            value=data["value"],
            isDefaulted=data.get("isDefaulted", None),
            defaultValue=data.get("defaultValue"),
            evalReason=data.get("evalReason"),
        )

    @staticmethod
    def create_default_variable(key: str, default_value: Any) -> "Variable":
        var_type = determine_variable_type(default_value)
        return Variable(
            _id=None,
            key=key,
            type=var_type,
            value=default_value,
            defaultValue=default_value,
            isDefaulted=True,
        )
