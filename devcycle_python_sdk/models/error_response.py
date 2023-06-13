# ruff: noqa: N815
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(order=False)
class ErrorResponse:
    message: str
    statusCode: Optional[int] = 0
    data: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None
        }
