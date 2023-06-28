# ruff: noqa: N815
from dataclasses import dataclass
from typing import Optional


@dataclass(order=False)
class Feature:
    _id: str
    key: str
    type: str
    _variation: str
    variationName: Optional[str] = None
    variationKey: Optional[str] = None
    evalReason: Optional[str] = None

    def to_json(self):
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None
        }

    @classmethod
    def from_json(cls, data: dict) -> "Feature":
        return cls(
            _id=data["_id"],
            key=data["key"],
            type=data["type"],
            _variation=data["_variation"],
            variationName=data["variationName"],
            variationKey=data["variationKey"],
            evalReason=data.get("evalReason"),
        )
