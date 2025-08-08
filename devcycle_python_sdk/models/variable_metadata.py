from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class VariableMetadata:
    feature_id: str

    @staticmethod
    def from_json(json_obj: Optional[Dict[str, Any]]) -> Optional["VariableMetadata"]:
        if json_obj is None:
            return None
        return VariableMetadata(
            feature_id=json_obj["feature_id"],
        )

    def to_json(self):
        result = {}
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            result[field_name] = value
        return result
