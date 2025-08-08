from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class EnvironmentMetadata:
    id: str
    key: str

    @staticmethod
    def from_json(
        json_obj: Optional[Dict[str, Any]],
    ) -> Optional["EnvironmentMetadata"]:
        if json_obj is None:
            return None
        return EnvironmentMetadata(
            id=json_obj["id"],
            key=json_obj["key"],
        )

    def to_json(self):
        result = {}
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            result[field_name] = value
        return result
