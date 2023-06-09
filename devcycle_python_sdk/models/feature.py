from dataclasses import dataclass
from typing import Optional


@dataclass(eq=False, order=False)
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
