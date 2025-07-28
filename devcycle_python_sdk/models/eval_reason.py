from dataclasses import dataclass
from typing import Optional


class EvalReasons:
    """Evaluation reasons constants"""

    DEFAULT = "DEFAULT"


class DefaultReasonDetails:
    """Default reason details constants"""

    MISSING_CONFIG = "Missing Config"
    USER_NOT_TARGETED = "User Not Targeted"
    TYPE_MISMATCH = "Variable Type Mismatch"
    MISSING_VARIABLE = "Missing Variable"
    ERROR = "Error"


@dataclass(order=False)
class EvalReason:
    reason: str
    details: Optional[str] = None
    target_id: Optional[str] = None

    def to_json(self):
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None
        }

    @classmethod
    def from_json(cls, data: dict) -> "EvalReason":
        return cls(
            reason=data["reason"],
            details=data.get("details"),
            target_id=data.get("target_id"),
        )
