# ruff: noqa: N815
from dataclasses import dataclass, field
from typing import Dict, Optional
from time import time


@dataclass(order=False)
class Event:
    type: Optional[str] = None
    target: Optional[str] = None
    date: int = field(default_factory=lambda: int(time()))
    value: Optional[int] = None
    metaData: Dict[str, str] = field(default_factory=dict)

    def to_json(self):
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None
        }
